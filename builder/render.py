"""Render complete client configs from the single preset definition.

One preset defines policy groups + rule order once; every client template is a
dumb projection of that model, so groups cannot drift between clients.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from . import emit
from .spec import ADS_TIERS, Preset, categories_for

SUBSCRIPTION_PLACEHOLDER = "https://sub.example.com/api/v1/client/subscribe?token=YOUR_TOKEN"

CLIENTS = {
    "mihomo": "mihomo.yaml",
    "shadowrocket": "shadowrocket.conf",
}

# Categories whose domains are resolved by a domestic resolver.  Everything
# else in a preset is a foreign service and must not touch a CN resolver.
DOMESTIC_CATEGORIES = {
    "private",
    "cn",
    "cn-ip",
    "cn-ip6",
    "cn-region-locked",
    "reject-ads",
    "reject-tracker",
    "reject-malware",
}


@dataclass
class RuleEntry:
    kind: str  # ruleset | inline | final
    text: str = ""
    tag: str = ""
    policy: str = ""
    no_resolve: bool = False
    list_url: str = ""


def tier_categories(preset: Preset, tier: str) -> list[str]:
    return categories_for(preset, tier)


def build_context(preset: Preset, tier: str, builds: dict, urls: dict, generated_at: str) -> dict:
    categories = tier_categories(preset, tier)
    groups = [
        {
            "name": group.name,
            "type": group.type,
            "members": list(group.members),
            "use_providers": group.use_providers,
            "filter": group.filter,
            "exclude_filter": group.exclude_filter,
            "test_url": group.test_url,
            "interval": group.interval,
        }
        for group in preset.groups
    ]

    providers: list[dict] = []
    entries: list[RuleEntry] = []
    sr_entries: list[RuleEntry] = []
    dns_policy: list[dict] = []
    dns_proxy_group = proxy_group_name(preset)

    for ref in preset.rules:
        if ref.final:
            entries.append(RuleEntry(kind="final", text=f"MATCH,{ref.final}", policy=ref.final))
            sr_entries.append(RuleEntry(kind="final", text=f"FINAL,{ref.final}", policy=ref.final))
            continue
        if ref.category not in categories:
            continue
        item = builds[ref.category]
        policy = ref.policy or "DIRECT"
        list_url = f"{urls['jsdelivr']}@{urls['branch']}/rules/{ref.category}/{ref.category}.list"
        if item.domain_rules:
            tag = ref.category
            providers.append(_provider(ref.category, "domain", urls))
            entries.append(RuleEntry(kind="ruleset", tag=tag, text=f"RULE-SET,{tag},{policy}"))
        if item.ip_rules:
            # IP-only categories keep their own name (cn-ip.mrs); mixed ones get
            # a -ip suffix (private-ip.mrs) so both behaviours can coexist.
            suffix = "-ip" if item.domain_rules else ""
            tag = f"{ref.category}{suffix}"
            providers.append(
                _provider(ref.category, "ipcidr", urls, file_suffix=suffix, tag=tag)
            )
            suffix_text = ",no-resolve" if ref.no_resolve else ""
            entries.append(
                RuleEntry(
                    kind="ruleset",
                    tag=tag,
                    policy=policy,
                    no_resolve=ref.no_resolve,
                    text=f"RULE-SET,{tag},{policy}{suffix_text}",
                )
            )
        if item.domain_rules or item.ip_rules:
            sr_entries.append(
                RuleEntry(kind="ruleset", tag=ref.category, policy=policy, list_url=list_url)
            )
        for keyword in item.keyword_rules:
            inline = f"DOMAIN-KEYWORD,{keyword.value},{policy}"
            entries.append(RuleEntry(kind="inline", text=inline, policy=policy))
            sr_entries.append(RuleEntry(kind="inline", text=inline, policy=policy))
        if ref.category not in DOMESTIC_CATEGORIES and item.domain_rules:
            dns_policy.append(
                {
                    "key": f"rule-set:{ref.category}",
                    "servers": [f"https://1.1.1.1/dns-query#{dns_proxy_group}"],
                }
            )

    if "private" in categories and builds["private"].domain_rules:
        dns_policy.insert(
            0,
            {
                "key": "rule-set:private",
                "servers": ["https://dns.alidns.com/dns-query", "https://doh.pub/dns-query"],
            },
        )
    if "cn" in categories and builds["cn"].domain_rules:
        dns_policy.insert(
            0,
            {
                "key": "rule-set:cn",
                "servers": ["https://dns.alidns.com/dns-query", "https://doh.pub/dns-query"],
            },
        )

    return {
        "preset": preset,
        "tier": tier,
        "generated_at": generated_at,
        "groups": groups,
        "providers": providers,
        "rule_entries": entries,
        "sr_rule_entries": sr_entries,
        "dns_policy": dns_policy,
        "subscription_placeholder": SUBSCRIPTION_PLACEHOLDER,
        "urls": urls,
        "config_url": "",
        "rules_total": sum(builds[cid].counts["total"] for cid in categories),
    }


def proxy_group_name(preset: Preset) -> str:
    """Group used to reach foreign DNS servers; the first group that proxies."""
    for group in preset.groups:
        if group.name.startswith("🚀"):
            return group.name
    return preset.groups[0].name


def _provider(
    category: str,
    behavior: str,
    urls: dict,
    *,
    file_suffix: str | None = None,
    tag: str | None = None,
) -> dict:
    suffix = "" if behavior == "domain" else "-ip"
    if file_suffix is not None:
        suffix = file_suffix
    filename = f"{category}{suffix}.mrs"
    return {
        "tag": tag or f"{category}{suffix}",
        "behavior": behavior,
        "url": f"{urls['jsdelivr']}@{urls['branch']}/rules/{category}/{filename}",
        "path": f"./rules/{filename}",
    }


def render_client_configs(
    paths,
    presets: list[Preset],
    builds: dict,
    urls: dict,
    generated_at: str,
    mihomo_bin: Path | None = None,
) -> list[dict]:
    env = Environment(
        loader=FileSystemLoader(str(paths.templates)),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        autoescape=False,
    )
    checks: list[dict] = []
    for preset in presets:
        for tier in ADS_TIERS:
            context = build_context(preset, tier, builds, urls, generated_at)
            folder = paths.dist / "configs" / preset.id / tier
            for client, filename in CLIENTS.items():
                context["config_url"] = (
                    f"{urls['jsdelivr']}@{urls['branch']}/configs/{preset.id}/{tier}/{filename}"
                )
                extension = filename.split(".")[-1]
                template = env.get_template(f"{client}/config.{extension}.j2")
                text = template.render(**context, client=client, filename=filename)
                emit.write_text(folder / filename, text)
                if client == "mihomo" and mihomo_bin is not None:
                    ok, output = emit.Converter(mihomo_bin).test_config(folder / filename)
                    checks.append(
                        {
                            "file": f"configs/{preset.id}/{tier}/{filename}",
                            "ok": ok,
                            "output": output,
                        }
                    )
    return checks
