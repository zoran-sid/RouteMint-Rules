from __future__ import annotations

import json
from pathlib import Path

from builder.build import CategoryBuild
from builder.model import Rule
from builder.report import CATEGORY_BEGIN, CATEGORY_END, update_readme_table, write_changelog
from builder.resolve import ResolvedCategory
from builder.spec import CategorySpec


def _category(cid: str, values: list[str], description: str = "d") -> CategoryBuild:
    spec = CategorySpec(
        id=cid, path=Path(f"{cid}.yaml"), description=description, meta={"description": description}
    )
    return CategoryBuild(
        spec=spec,
        rules=[Rule.parse(f"DOMAIN-SUFFIX,{v}") for v in values],
        resolved=ResolvedCategory(spec=spec),
    )


def test_readme_table_is_replaced_between_markers(tmp_path: Path):
    path = tmp_path / "README.md"
    path.write_text(
        f"# title\n\n{CATEGORY_BEGIN}\nold table\n{CATEGORY_END}\n\ntrailing text\n",
        encoding="utf-8",
    )
    assert update_readme_table(path, {"cn": _category("cn", ["baidu.com"], "中国大陆域名")})
    text = path.read_text(encoding="utf-8")
    assert "old table" not in text
    assert "| `cn` | 中国大陆域名 | 1 |" in text
    assert text.rstrip().endswith("trailing text")


def test_readme_without_markers_is_untouched(tmp_path: Path):
    path = tmp_path / "README.md"
    path.write_text("# no markers\n", encoding="utf-8")
    assert update_readme_table(path, {}) is False
    assert path.read_text(encoding="utf-8") == "# no markers\n"


def test_changelog_first_and_second_build(tmp_path: Path):
    path = tmp_path / "CHANGELOG.md"
    write_changelog(
        path,
        builds={"cn": _category("cn", ["a.com"])},
        previous=None,
        previous_dist=None,
        generated_at="2026-01-01T00:00:00+00:00",
        presets=[],
    )
    text = path.read_text(encoding="utf-8")
    assert text.count("# 变更日志") == 1
    assert "首次构建" in text

    previous = {"categories": {"cn": {"total": 1}}}
    old_dist = tmp_path / "old"
    (old_dist / "rules" / "cn").mkdir(parents=True)
    (old_dist / "rules" / "cn" / "cn.list").write_text(
        "# header\nDOMAIN-SUFFIX,a.com\nDOMAIN-SUFFIX,removed.com\n", encoding="utf-8"
    )
    write_changelog(
        path,
        builds={"cn": _category("cn", ["a.com", "b.com"])},
        previous=previous,
        previous_dist=old_dist,
        generated_at="2026-01-02T00:00:00+00:00",
        presets=[],
    )
    text = path.read_text(encoding="utf-8")
    assert text.count("# 变更日志") == 1
    assert "## 2026-01-02" in text
    assert "## 2026-01-01" in text
    assert "新增：DOMAIN-SUFFIX,b.com" in text
    assert "删除：DOMAIN-SUFFIX,removed.com" in text


def test_manifest_roundtrip_shape(tmp_path: Path):
    from builder.report import write_manifest

    path = tmp_path / "manifest.json"
    write_manifest(path, {"schema": 1, "categories": {"cn": {"total": 1}}})
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schema"] == 1
