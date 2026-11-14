from __future__ import annotations

from pathlib import Path

from builder.build import CategoryBuild, preset_total
from builder.model import Rule
from builder.render import build_context
from builder.resolve import ResolvedCategory
from builder.spec import CategorySpec, Group, Preset, RuleRef

URLS = {
    "owner": "o",
    "repo": "r",
    "branch": "release",
    "jsdelivr": "https://cdn.jsdelivr.net/gh/o/r",
    "raw": "https://raw.githubusercontent.com/o/r",
    "source_url": "https://github.com/o/r",
}


def _category(cid: str, rules: list[str], meta: dict | None = None) -> CategoryBuild:
    spec = CategorySpec(
        id=cid,
        path=Path(f"{cid}.yaml"),
        description=cid,
        meta=meta or {"description": cid},
    )
    return CategoryBuild(
        spec=spec,
        rules=[Rule.parse(r) for r in rules],
        resolved=ResolvedCategory(spec=spec),
    )


def _preset(rules: list[RuleRef], groups: list[Group]) -> Preset:
    return Preset(
        id="p",
        label="P",
        tagline="",
        audience="",
        summary="s",
        order=1,
        ads="ads-light",
        groups=tuple(groups),
        rules=tuple(rules),
    )


GROUPS = [
    Group(name="🚀 节点选择", type="select", members=("DIRECT",), use_providers=True),
    Group(name="🤖 AI 服务", type="select", members=("DIRECT",), use_providers=True),
    Group(name="🎯 全球直连", type="select", members=("DIRECT",)),
    Group(name="🛑 广告拦截", type="select", members=("REJECT",)),
    Group(name="🐟 漏网之鱼", type="select", members=("🎯 全球直连",)),
]


def test_context_orders_rules_and_splits_ip_providers():
    builds = {
        "private": _category("private", ["DOMAIN-SUFFIX,lan", "IP-CIDR,10.0.0.0/8"]),
        "ai": _category("ai", ["DOMAIN-SUFFIX,openai.com"]),
        "cn-ip": _category("cn-ip", ["IP-CIDR,1.0.1.0/24"], {"description": "cn ip"}),
    }
    preset = _preset(
        [
            RuleRef(category="private", policy="🎯 全球直连"),
            RuleRef(category="ai", policy="🤖 AI 服务"),
            RuleRef(category="cn-ip", policy="🎯 全球直连", no_resolve=True),
            RuleRef(final="🐟 漏网之鱼"),
        ],
        GROUPS,
    )
    context = build_context(preset, "ads-off", builds, URLS, "2026-01-01T00:00:00Z")
    lines = [entry.text for entry in context["rule_entries"]]
    assert lines == [
        "RULE-SET,private,🎯 全球直连",
        "RULE-SET,private-ip,🎯 全球直连",
        "RULE-SET,ai,🤖 AI 服务",
        "RULE-SET,cn-ip,🎯 全球直连,no-resolve",
        "MATCH,🐟 漏网之鱼",
    ]
    tags = [provider["tag"] for provider in context["providers"]]
    assert tags == ["private", "private-ip", "ai", "cn-ip"]
    assert context["providers"][3]["behavior"] == "ipcidr"
    assert context["providers"][3]["url"].endswith("/rules/cn-ip/cn-ip.mrs")


def test_dns_policy_splits_domestic_and_foreign():
    builds = {
        "private": _category("private", ["DOMAIN-SUFFIX,lan"]),
        "cn": _category("cn", ["DOMAIN-SUFFIX,baidu.com"]),
        "ai": _category("ai", ["DOMAIN-SUFFIX,openai.com"]),
    }
    preset = _preset(
        [
            RuleRef(category="private", policy="🎯 全球直连"),
            RuleRef(category="ai", policy="🤖 AI 服务"),
            RuleRef(category="cn", policy="🎯 全球直连"),
            RuleRef(final="🐟 漏网之鱼"),
        ],
        GROUPS,
    )
    context = build_context(preset, "ads-off", builds, URLS, "2026-01-01T00:00:00Z")
    policy = {item["key"]: item["servers"] for item in context["dns_policy"]}
    assert policy["rule-set:ai"] == ["https://1.1.1.1/dns-query#🚀 节点选择"]
    assert any("dns.alidns.com" in server for server in policy["rule-set:cn"])
    assert len(policy["rule-set:cn"]) == 2
    assert "rule-set:private" in policy


def test_tiers_drop_reject_categories():
    builds = {
        "reject-ads": _category("reject-ads", ["DOMAIN-SUFFIX,ads.example"]),
        "reject-tracker": _category("reject-tracker", ["DOMAIN-SUFFIX,trk.example"]),
        "reject-malware": _category("reject-malware", ["DOMAIN-SUFFIX,bad.example"]),
    }
    preset = _preset(
        [
            RuleRef(category="reject-malware", policy="🛑 广告拦截"),
            RuleRef(category="reject-tracker", policy="🛑 广告拦截"),
            RuleRef(category="reject-ads", policy="🛑 广告拦截"),
            RuleRef(final="🐟 漏网之鱼"),
        ],
        GROUPS,
    )
    assert [e.tag for e in build_context(preset, "ads-off", builds, URLS, "")["rule_entries"][:-1]] == []
    light = [e.tag for e in build_context(preset, "ads-light", builds, URLS, "")["rule_entries"]]
    assert light[:2] == ["reject-tracker", "reject-ads"]
    strict = [e.tag for e in build_context(preset, "ads-strict", builds, URLS, "")["rule_entries"]]
    assert strict[:3] == ["reject-malware", "reject-tracker", "reject-ads"]


def test_preset_total_counts_only_enabled_tiers():
    builds = {
        "reject-ads": _category("reject-ads", ["DOMAIN-SUFFIX,a.example"] * 1),
        "reject-malware": _category("reject-malware", ["DOMAIN-SUFFIX,b.example", "DOMAIN-SUFFIX,c.example"]),
    }
    preset = _preset(
        [
            RuleRef(category="reject-malware", policy="🛑 广告拦截"),
            RuleRef(category="reject-ads", policy="🛑 广告拦截"),
            RuleRef(final="🐟 漏网之鱼"),
        ],
        GROUPS,
    )
    assert preset_total(builds, preset, "ads-off") == 0
    assert preset_total(builds, preset, "ads-light") == 1
    assert preset_total(builds, preset, "ads-strict") == 3
