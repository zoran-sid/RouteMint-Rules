from __future__ import annotations

from builder.model import Rule, RuleType
from builder.optimize import (
    apply_removals,
    collapse_ips,
    dedupe,
    prune_shadowed_domains,
    resolve_conflicts,
)


def rules(*items: str) -> list[Rule]:
    return [Rule.parse(item) for item in items]


def values(items: list[Rule]) -> list[str]:
    return [str(r) for r in items]


def test_dedupe_keeps_first():
    out, dropped = dedupe(rules("DOMAIN-SUFFIX,a.com", "DOMAIN-SUFFIX,a.com", "DOMAIN-SUFFIX,b.com"))
    assert values(out) == ["DOMAIN-SUFFIX,a.com", "DOMAIN-SUFFIX,b.com"]
    assert dropped == 1


def test_prune_removes_children_and_exact_domains():
    out, dropped = prune_shadowed_domains(
        rules(
            "DOMAIN-SUFFIX,example.com",
            "DOMAIN-SUFFIX,cdn.example.com",
            "DOMAIN,www.example.com",
            "DOMAIN-SUFFIX,other.com",
        )
    )
    assert values(out) == ["DOMAIN-SUFFIX,example.com", "DOMAIN-SUFFIX,other.com"]
    assert dropped == 2


def test_prune_collapses_tld_children():
    out, dropped = prune_shadowed_domains(
        rules("DOMAIN-SUFFIX,cn", "DOMAIN-SUFFIX,baidu.cn", "DOMAIN-SUFFIX,qq.com")
    )
    assert values(out) == ["DOMAIN-SUFFIX,cn", "DOMAIN-SUFFIX,qq.com"]
    assert dropped == 1


def test_prune_keeps_keyword_and_ip_rules():
    out, _ = prune_shadowed_domains(
        rules(
            "DOMAIN-SUFFIX,example.com",
            "DOMAIN-KEYWORD,tracker",
            "IP-CIDR,10.0.0.0/8",
        )
    )
    assert "IP-CIDR,10.0.0.0/8" in values(out)
    assert "DOMAIN-KEYWORD,tracker" in values(out)


def test_collapse_merges_adjacent_ipv4_and_dedupes_v6():
    out, merged = collapse_ips(
        rules(
            "IP-CIDR,10.0.0.0/9",
            "IP-CIDR,10.128.0.0/9",
            "IP-CIDR,192.168.0.0/16",
            "IP-CIDR6,2001:db8::/32",
        )
    )
    assert merged == 1
    assert values(out) == ["IP-CIDR,10.0.0.0/8", "IP-CIDR,192.168.0.0/16", "IP-CIDR6,2001:db8::/32"]


def test_removals_have_reasons_and_apply_by_value():
    out, dropped = apply_removals(rules("DOMAIN-SUFFIX,a.com", "DOMAIN-SUFFIX,b.com"), {"a.com": "x"})
    assert values(out) == ["DOMAIN-SUFFIX,b.com"]
    assert dropped == 1


def test_conflict_higher_precedence_wins():
    resolved, stats = resolve_conflicts(
        {
            "proxy": rules("DOMAIN-SUFFIX,google.com", "DOMAIN-SUFFIX,shared.com"),
            "cn": rules("DOMAIN-SUFFIX,shared.com", "DOMAIN-SUFFIX,baidu.com"),
        },
        ["cn", "proxy"],
    )
    assert set(values(resolved["cn"])) == {"DOMAIN-SUFFIX,baidu.com", "DOMAIN-SUFFIX,shared.com"}
    assert values(resolved["proxy"]) == ["DOMAIN-SUFFIX,google.com"]
    assert stats.conflicts == 1
    assert stats.decisions[0].winner == "cn"


def test_conflict_partial_overlap_is_kept():
    resolved, stats = resolve_conflicts(
        {
            "a": rules("DOMAIN,api.example.com"),
            "b": rules("DOMAIN-SUFFIX,example.com"),
        },
        ["a", "b"],
    )
    assert stats.conflicts == 0
    assert len(resolved["b"]) == 1


def test_conflict_ip_subnet_loses_to_supernet():
    resolved, stats = resolve_conflicts(
        {
            "proxy": rules("IP-CIDR,1.0.1.0/24"),
            "cn-ip": rules("IP-CIDR,1.0.0.0/16"),
        },
        ["cn-ip", "proxy"],
    )
    assert resolved["proxy"] == []
    assert stats.decisions[0].reason == "inside 1.0.0.0/16"


def test_exact_domain_equal_to_higher_suffix_is_dropped():
    resolved, _ = resolve_conflicts(
        {
            "ai": rules("DOMAIN-SUFFIX,openai.com"),
            "proxy": rules("DOMAIN,openai.com", "DOMAIN-SUFFIX,example.net"),
        },
        ["ai", "proxy"],
    )
    assert values(resolved["proxy"]) == ["DOMAIN-SUFFIX,example.net"]
    assert values(resolved["ai"]) == ["DOMAIN-SUFFIX,openai.com"]
