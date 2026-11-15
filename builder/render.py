"""Render complete client configs from the single preset definition.

One preset defines policy groups + rule order once; every client template is a
dumb projection of that model, so groups cannot drift between clients.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

import json

from . import emit
from .spec import ADS_TIERS, Preset, categories_for

SUBSCRIPTION_PLACEHOLDER = "https://sub.example.com/api/v1/client/subscribe?token=YOUR_TOKEN"
SUB_PLACEHOLDERS = {
    "mihomo": SUBSCRIPTION_PLACEHOLDER,
    "surge": SUBSCRIPTION_PLACEHOLDER + "&flag=surge",
    "loon": SUBSCRIPTION_PLACEHOLDER + "&flag=loon",
    "quantumultx": SUBSCRIPTION_PLACEHOLDER + "&flag=quantumultx",
    "singbox": SUBSCRIPTION_PLACEHOLDER,
}

# Groups whose only member is a built-in policy map to that built-in instead of
# becoming a policy group on clients where that is allowed (QX).
BUILTIN_POLICY = {"DIRECT": "direct", "REJECT": "reject"}

# Every published config uses a .conf suffix so the subscription URL looks the
# same regardless of the client; the content format is unchanged (mihomo = YAML,
# sing-box = JSON).
CLIENTS = {
    "mihomo": "mihomo.conf",
    "shadowrocket": "shadowrocket.conf",
    "surge": "surge.conf",
    "loon": "loon.conf",
    "quantumultx": "quantumultx.conf",
    "singbox": "singbox.conf",
}

# Stable, descriptive basenames are also the imported Shadowrocket profile names.
SHADOWROCKET_NAMES = {
    "cn-mainland": "RouteMint-CN-Whitelist",
    "cn-mainland-lite": "RouteMint-CN-Lite",
    "overseas": "RouteMint-Overseas-AI-Media",
    "overseas-return": "RouteMint-Return-CN",
}


def client_filename(client: str, preset: str, tier: str) -> str:
    if client == "shadowrocket":
        return f"{SHADOWROCKET_NAMES[preset]}-{tier}.conf"
    return CLIENTS[client]


# Client-specific file extensions; sing-box gets JSON, everyone else a conf/yaml.
TEMPLATE_EXT = {
    "mihomo": "yaml",
    "shadowrocket": "conf",
    "surge": "conf",
    "loon": "conf",
    "quantumultx": "conf",
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
            "tag": group.tag,
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
    mainland = preset.id.startswith("cn-mainland")
    default_dns = (
        ["https://dns.alidns.com/dns-query", "https://doh.pub/dns-query"]
        if mainland else ["system"]
    )
    bootstrap_dns = ["223.5.5.5", "119.29.29.29"] if mainland else ["1.1.1.1", "8.8.8.8"]

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
        if item.domain_rules and not ref.category.startswith("reject-"):
            # DNS follows the service policy, including a manually chosen DIRECT.
            # A return-media query must leave through the same mainland exit.
            if ref.category in {"private", "game-download", "baidu-pan", "steam-direct"}:
                servers = ["system"]
            elif ref.category in {"cn", "cn-region-locked"}:
                servers = [f"https://dns.alidns.com/dns-query#{policy}"]
            else:
                servers = [f"https://1.1.1.1/dns-query#{policy}"]
            dns_policy.append({"key": f"rule-set:{ref.category}", "servers": servers})

    builtin = {
        group["name"]: BUILTIN_POLICY[group["members"][0]]
        for group in groups
        if not group["use_providers"] and len(group["members"]) == 1 and group["members"][0] in BUILTIN_POLICY
    }
    # QX policy groups are flat: members are servers from the subscription, and
    # nesting another group is not documented, so every non-built-in group is
    # built from the airport resource instead of listing members.
    qx_policies = [
        {**group}
        for group in groups
        if group["name"] not in builtin
    ]
    qx_filters = [
        {
            "url": entry.list_url,
            "tag": entry.tag,
            "policy": builtin.get(entry.policy, entry.policy),
        }
        for entry in sr_entries
        if entry.kind == "ruleset"
    ]
    qx_inline = [
        {
            "text": entry.text.replace("DOMAIN-KEYWORD,", "host-keyword, ", 1),
            "policy": builtin.get(entry.policy, entry.policy),
        }
        for entry in sr_entries
        if entry.kind == "inline"
    ]
    surge_lines: list[str] = [
        f"Airport = select, policy-path={SUB_PLACEHOLDERS['surge']}, "
        "update-interval=86400, no-alert=true, hidden=true"
    ]
    loon_filters: list[str] = []
    loon_groups: list[str] = []

    for group in groups:
        name, gtype = group["name"], group["type"]
        members = list(group["members"])
        surge = f"{name} = {gtype}"
        loon = f"{name} = {gtype}"
        for member in members:
            loon += f", {member}"
        if group["use_providers"]:
            surge += ", include-other-group=Airport"
            if group["filter"]:
                surge += f', policy-regex-filter="{group["filter"]}"'
                filter_name = f"f-{group['tag'] or name}"
                loon_filters.append(
                    f"{filter_name} = NameRegex,Airport,FilterKey = {group['filter']}"
                )
                loon += f", {filter_name}"
            else:
                loon += ", Airport"
        for member in members:
            surge += f", {member}"
        if gtype != "select":
            surge += f", url={group['test_url']}, interval={group['interval']}"
            loon += f", url={group['test_url']}, interval={group['interval']}"
        surge_lines.append(surge)
        loon_groups.append(loon)

    surge_rules: list[str] = []
    loon_remote_rules: list[str] = []
    loon_rules: list[str] = []
    qx_filter_remote: list[str] = []
    qx_filter_local: list[str] = []
    for entry in sr_entries:
        if entry.kind == "ruleset":
            surge_rules.append(f"RULE-SET,{entry.list_url},{entry.policy}")
            loon_remote_rules.append(f"{entry.list_url},policy={entry.policy},enabled=true")
            qx_filter_remote.append(
                f"{entry.list_url.removesuffix('.list')}-qx.list, tag={entry.tag}, "
                f"force-policy={builtin.get(entry.policy, entry.policy)}, enabled=true"
            )
        elif entry.kind == "inline":
            surge_rules.append(entry.text)
            loon_rules.append(entry.text)
            qx_filter_local.append(
                f"{entry.text.rsplit(',', 1)[0].replace('DOMAIN-KEYWORD,', 'host-keyword, ', 1)}, {builtin.get(entry.policy, entry.policy)}"
            )
        else:
            surge_rules.append(f"FINAL,{entry.policy}")
            loon_rules.append(f"FINAL,{entry.policy}")

    qx_policy_lines: list[str] = []
    for policy in qx_policies:
        if policy["type"] == "select":
            # QX groups are flattened to subscription servers. Preserve an
            # explicit DIRECT/REJECT default instead of silently proxying it.
            first = policy["members"][0] if policy["members"] else ""
            default = builtin.get(first, BUILTIN_POLICY.get(first, ""))
            prefix = f"{default}, " if default else ""
            qx_policy_lines.append(f"static = {policy['name']}, {prefix}resource-tag-regex=^Airport$")
        else:
            qx_policy_lines.append(
                f"url-latency-benchmark = {policy['name']}, resource-tag-regex=^Airport$, "
                f"check-interval={policy['interval']}, tolerance=0"
            )

    final_policy = preset.rules[-1].final
    final_group = next((g for g in groups if g["name"] == final_policy), None)
    final_first = final_group["members"][0] if final_group and final_group["members"] else ""
    qx_final = builtin.get(final_first, final_policy)
    surge_groups = [
        {
            "name": group["name"],
            "type": group["type"],
            "members": [m for m in group["members"] if m not in BUILTIN_POLICY] + [
                m for m in group["members"] if m in BUILTIN_POLICY
            ],
            "use_providers": group["use_providers"],
            "policy_filter": group["filter"] if group["use_providers"] else None,
            "test_url": group["test_url"],
            "interval": group["interval"],
        }
        for group in groups
    ]

    return {
        "preset": preset,
        "tier": tier,
        "generated_at": generated_at,
        "groups": groups,
        "providers": providers,
        "rule_entries": entries,
        "sr_rule_entries": sr_entries,
        "dns_policy": dns_policy,
        "default_dns": default_dns,
        "bootstrap_dns": bootstrap_dns,
        "mainland": mainland,
        "subscription_placeholder": SUBSCRIPTION_PLACEHOLDER,
        "sub_placeholders": SUB_PLACEHOLDERS,
        "urls": urls,
        "config_url": "",
        "rules_total": sum(builds[cid].counts["total"] for cid in categories),
        "sb": _singbox_model(preset, groups, categories, builds, urls),
        "surge_groups": surge_groups,
        "surge": {"groups": surge_lines, "rules": surge_rules},
        "loon": {
            "filters": loon_filters,
            "groups": loon_groups,
            "remote_rules": loon_remote_rules,
            "rules": loon_rules,
        },
        "qx": {
            "policies": qx_policies,
            "filters": qx_filters,
            "inline": qx_inline,
            "final": qx_final,
            "policy_lines": qx_policy_lines,
            "filter_remote": qx_filter_remote,
            "filter_local": qx_filter_local,
            "sub": SUB_PLACEHOLDERS["quantumultx"],
        },
    }


SINGBOX_RESERVED = {"direct", "block", "airport"}


def _group_tag(group: dict, index: int) -> str:
    tag = group["tag"] or f"g{index + 1}"
    # `direct` / `block` / `airport` are outbound tags we always emit ourselves.
    return f"g-{tag}" if tag in SINGBOX_RESERVED else tag


def _singbox_model(preset: Preset, groups: list[dict], categories: list[str], builds: dict, urls: dict) -> dict:
    """sing-box config model.

    sing-box has no node-name regex filter, so the AI group cannot exclude
    regions automatically on this client; that is documented in the README.
    The outbound list contains a placeholder SOCKS outbound because a sing-box
    config must be syntactically complete while never containing real nodes.
    """
    policy_tag: dict[str, str] = {}
    for index, group in enumerate(groups):
        policy_tag[group["name"]] = _group_tag(group, index)
    policy_tag["DIRECT"] = "direct"
    policy_tag["REJECT"] = "block"

    outbounds: list[dict] = []
    for index, group in enumerate(groups):
        members: list[str] = []
        for member in group["members"]:
            tag = policy_tag.get(member, "direct")
            if tag not in members:
                members.append(tag)
        if group["use_providers"]:
            members.append("airport")
        if not members:
            members = ["airport"]
        entry: dict = {"type": "selector" if group["type"] == "select" else "urltest",
                       "tag": _group_tag(group, index), "outbounds": members}
        if group["type"] == "select":
            entry["default"] = members[0]
        else:
            entry["url"] = group["test_url"]
            entry["interval"] = f"{group['interval']}s"
        outbounds.append(entry)

    outbounds += [
        {"type": "socks", "tag": "airport", "server": "127.0.0.1", "server_port": 1080},
        {"type": "direct", "tag": "direct"},
        {"type": "block", "tag": "block"},
    ]

    rule_sets: list[dict] = []
    route_rules: list[dict] = [
        {"action": "sniff"},
        {"protocol": "dns", "action": "hijack-dns"},
    ]
    dns_rules: list[dict] = []
    dns_servers: list[dict] = []

    for ref in preset.rules:
        if ref.final or ref.category not in categories:
            continue
        item = builds[ref.category]
        tag = f"rs-{ref.category}"
        if item.rules:
            rule_sets.append(
                {
                    "type": "remote",
                    "tag": tag,
                    "format": "binary",
                    "url": f"{urls['jsdelivr']}@{urls['branch']}/rules/{ref.category}/{ref.category}.srs",
                    "download_detour": "proxy" if preset.id.startswith("cn-mainland") else "direct",
                }
            )
            route_rules.append({"rule_set": tag, "outbound": policy_tag[ref.policy or "DIRECT"]})
        if item.domain_rules and not ref.category.startswith("reject-"):
            if ref.category in {"private", "game-download", "baidu-pan", "steam-direct"}:
                dns_tag = "local"
            else:
                outbound = policy_tag[ref.policy or "DIRECT"]
                domestic = ref.category in {"cn", "cn-region-locked"}
                dns_tag = f"dns-{'cn' if domestic else 'remote'}-{outbound}"
                if not any(server["tag"] == dns_tag for server in dns_servers):
                    dns_servers.append({
                        "type": "https", "tag": dns_tag,
                        "server": "223.5.5.5" if domestic else "1.1.1.1",
                        "path": "/dns-query", "detour": outbound,
                        **({"tls": {"server_name": "dns.alidns.com"}} if domestic else {}),
                    })
            dns_rules.append({"rule_set": tag, "server": dns_tag})

    return {
        "dns_servers": dns_servers,
        "default_dns": "domestic" if preset.id.startswith("cn-mainland") else "local",
        "outbounds": outbounds,
        "rule_sets": rule_sets,
        "rules": route_rules,
        "dns_rules": dns_rules,
        "final": policy_tag[preset.rules[-1].final],
    }


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


def singbox_config(context: dict) -> dict:
    sb = context["sb"]
    return {
        "log": {"level": "info", "timestamp": True},
        "dns": {
            "servers": [
                {"type": "local", "tag": "local"},
                {"type": "https", "tag": "domestic", "server": "223.5.5.5",
                 "path": "/dns-query", "tls": {"server_name": "dns.alidns.com"},
                 "detour": "direct"},
                *sb["dns_servers"],
            ],
            "rules": sb["dns_rules"],
            "final": sb["default_dns"],
            "strategy": "prefer_ipv4",
        },
        "inbounds": [
            {
                "type": "tun",
                "tag": "tun-in",
                "address": ["172.19.0.1/30"],
                "auto_route": True,
                "strict_route": True,
            }
        ],
        "outbounds": sb["outbounds"],
        "route": {
            "rules": sb["rules"],
            "rule_set": sb["rule_sets"],
            "final": sb["final"],
            "default_domain_resolver": {"server": sb["default_dns"]},
        },
    }


def render_client_configs(
    paths,
    presets: list[Preset],
    builds: dict,
    urls: dict,
    generated_at: str,
    mihomo_bin: Path | None = None,
    singbox_bin: Path | None = None,
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
                published_filename = client_filename(client, preset.id, tier)
                base_url = (f"{urls['raw']}/{urls['branch']}" if client == "shadowrocket"
                            else f"{urls['jsdelivr']}@{urls['branch']}")
                context["config_url"] = (
                    f"{base_url}/configs/{preset.id}/{tier}/{published_filename}"
                )
                if client == "singbox":
                    text = json.dumps(singbox_config(context), ensure_ascii=False, indent=2) + "\n"
                    emit.write_text(folder / filename, text)
                else:
                    extension = TEMPLATE_EXT[client]
                    template = env.get_template(f"{client}/config.{extension}.j2")
                    text = template.render(**context, client=client, filename=filename)
                    emit.write_text(folder / published_filename, text)
                    if client == "shadowrocket":
                        # Existing subscriptions retain a valid compatibility URL.
                        emit.write_text(folder / filename, text)
                if client == "mihomo" and mihomo_bin is not None:
                    ok, output = emit.Converter(mihomo_bin).test_config(folder / filename)
                elif client == "singbox" and singbox_bin is not None:
                    ok, output = emit.test_singbox_config(singbox_bin, folder / filename)
                else:
                    continue
                checks.append(
                    {
                        "file": f"configs/{preset.id}/{tier}/{filename}",
                        "ok": ok,
                        "output": output,
                    }
                )
    return checks
