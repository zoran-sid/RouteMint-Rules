from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from builder.evaluate import explain

ROOT = Path(__file__).resolve().parents[1]
CASES = yaml.safe_load((ROOT / "tests" / "expectations.yaml").read_text(encoding="utf-8"))["cases"]


@pytest.mark.parametrize("case", CASES, ids=[c["domain"] for c in CASES])
def test_domain_routes_to_expected_category(built, preset_map, case):
    preset = preset_map[case["preset"]]
    result = explain(built.dist, preset, preset.ads, case["domain"])
    assert result is not None, f"{case['domain']} matched no rule in {preset.id}"
    category, policy = result
    assert category == case["category"], f"{case['domain']} hit {category}"
    assert policy == case["policy"], f"{case['domain']} routed to {policy}"


def test_ai_domain_is_not_in_proxy(built):
    proxy = built.categories["proxy"].rules
    proxy_values = {rule.value for rule in proxy}
    for value in ("openai.com", "anthropic.com", "claude.ai", "perplexity.ai"):
        assert value not in proxy_values, f"{value} leaked into proxy"


def test_cn_and_proxy_are_disjoint(built):
    cn = {rule.value for rule in built.categories["cn"].rules}
    proxy = {rule.value for rule in built.categories["proxy"].rules}
    assert not (cn & proxy), sorted(cn & proxy)[:5]
