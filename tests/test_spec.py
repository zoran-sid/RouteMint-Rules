from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from builder.config import ConfigError, Paths
from builder.spec import load_budgets, load_categories, load_category, load_presets, load_upstreams

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def repo(tmp_path: Path) -> Paths:
    """A minimal copy of the config tree that tests can mutate."""
    root = tmp_path / "repo"
    for name in ("sources", "presets"):
        shutil.copytree(ROOT / name, root / name)
    for name in ("upstreams.yaml", "budgets.yaml", "repo.yaml"):
        shutil.copy(ROOT / name, root / name)
    return Paths(root)


def test_repository_config_is_valid():
    paths = Paths(ROOT)
    categories = load_categories(paths)
    presets = load_presets(paths, categories)
    load_upstreams(paths)
    load_budgets(paths)
    assert "ai-openai" in categories
    assert presets[0].id == "cn-mainland"


def test_category_id_must_match_filename(repo: Paths):
    path = repo.sources / "private.yaml"
    path.write_text("id: other\nmeta: {description: x}\nadd: ['DOMAIN-SUFFIX,x.com']\n")
    with pytest.raises(ConfigError, match="must equal file name"):
        load_category(path)


def test_remove_requires_reason(repo: Paths):
    path = repo.sources / "cn.yaml"
    path.write_text(
        "id: cn\nmeta: {description: x}\nadd: ['DOMAIN-SUFFIX,x.com']\nremove:\n  - {value: y.com}\n"
    )
    with pytest.raises(ConfigError, match="needs a reason"):
        load_category(path)


def test_keyword_rule_requires_reason(repo: Paths):
    path = repo.sources / "cn.yaml"
    path.write_text(
        "id: cn\nmeta: {description: x}\nadd:\n  - rule: 'DOMAIN-KEYWORD,ads'\n"
    )
    with pytest.raises(ConfigError, match="needs a reason"):
        load_category(path)


def test_unknown_category_key_is_rejected(repo: Paths):
    path = repo.sources / "cn.yaml"
    path.write_text(
        "id: cn\nmeta: {description: x}\nadd: ['DOMAIN-SUFFIX,x.com']\nsurprise: true\n"
    )
    with pytest.raises(ConfigError, match="unknown keys"):
        load_category(path)


def test_preset_must_follow_canonical_order(repo: Paths):
    path = repo.presets / "cn-mainland.yaml"
    text = path.read_text(encoding="utf-8")
    # Move cn before private: a reorder that would silently change routing.
    text = text.replace(
        '  - {category: private, policy: "🎯 全球直连"}\n', ""
    ).replace(
        '  - {category: cn, policy: "🎯 全球直连"}',
        '  - {category: cn, policy: "🎯 全球直连"}\n  - {category: private, policy: "🎯 全球直连"}',
    )
    path.write_text(text, encoding="utf-8")
    categories = load_categories(repo)
    with pytest.raises(ConfigError, match="canonical order"):
        load_presets(repo, categories)


def test_preset_final_must_be_last(repo: Paths):
    path = repo.presets / "cn-mainland.yaml"
    text = path.read_text(encoding="utf-8")
    text = text.replace('  - {final: "🐟 漏网之鱼"}', "")
    text = text.replace(
        '  - {category: private, policy: "🎯 全球直连"}',
        '  - {final: "🐟 漏网之鱼"}\n  - {category: private, policy: "🎯 全球直连"}',
    )
    path.write_text(text, encoding="utf-8")
    categories = load_categories(repo)
    with pytest.raises(ConfigError):
        load_presets(repo, categories)


def test_upstream_requires_exactly_one_url_form(repo: Paths):
    path = repo.upstreams
    path.write_text(
        "upstreams:\n  x:\n    title: x\n    format: domains\n    license: MIT\n"
        "    url: https://a\n    url_template: https://b/{category}\n"
    )
    with pytest.raises(ConfigError, match="exactly one"):
        load_upstreams(repo)


def test_compose_category_cannot_have_rules(repo: Paths):
    path = repo.sources / "ai.yaml"
    path.write_text(
        "id: ai\nmeta: {description: x}\ncompose: [ai-openai]\nadd: ['DOMAIN-SUFFIX,x.com']\n"
    )
    with pytest.raises(ConfigError, match="cannot also include"):
        load_category(path)
