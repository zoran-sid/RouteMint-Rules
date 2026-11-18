"""v2rayNG clipboard routing profiles and Xray geo assets."""
from __future__ import annotations

import ipaddress
import json

from .emit import write_text
from .model import RuleType
from .spec import ADS_TIERS, Preset, categories_for

GEOSITE = "routemint-geosite.dat"
GEOIP = "routemint-geoip.dat"
DOMAIN_KIND = {
    RuleType.DOMAIN_KEYWORD: 0,
    RuleType.DOMAIN_SUFFIX: 2,
    RuleType.DOMAIN: 3,
}


def _varint(value: int) -> bytes:
    encoded = bytearray()
    while value >= 128:
        encoded.append((value & 127) | 128)
        value >>= 7
    encoded.append(value)
    return bytes(encoded)


def _bytes_field(number: int, value: bytes) -> bytes:
    return _varint((number << 3) | 2) + _varint(len(value)) + value


def _append_category(asset: bytearray, category: str, entries: list[bytes]) -> None:
    if entries:
        message = _bytes_field(1, category.upper().encode())
        message += b"".join(_bytes_field(2, entry) for entry in entries)
        asset.extend(_bytes_field(1, message))


def _assets(builds: dict) -> tuple[bytes, bytes]:
    """Encode Xray GeoSiteList and GeoIPList from the published rule model."""
    geosite, geoip = bytearray(), bytearray()
    for category, item in sorted(builds.items()):
        domains, ips = [], []
        for rule in item.rules:
            if rule.is_ip:
                network = ipaddress.ip_network(rule.value)
                ips.append(_bytes_field(1, network.network_address.packed)
                           + b"\x10" + _varint(network.prefixlen))
            else:
                domains.append(b"\x08" + _varint(DOMAIN_KIND[rule.type])
                               + _bytes_field(2, rule.value.encode()))
        _append_category(geosite, category, domains)
        _append_category(geoip, category, ips)
    return bytes(geosite), bytes(geoip)


def profile(preset: Preset, tier: str, builds: dict) -> list[dict]:
    groups = {group.name: group for group in preset.groups}
    builtin = {"DIRECT": "direct", "REJECT": "block"}

    def outbound(name: str) -> str:
        seen = set()
        while name not in builtin:
            if name in seen:
                raise ValueError(f"{preset.id}: circular policy default at {name}")
            seen.add(name)
            group = groups[name]
            if not group.members:
                return "proxy"
            name = group.members[0]
        return builtin[name]

    rules = []
    active = set(categories_for(preset, tier))
    for ref in preset.rules:
        if ref.final:
            rules.append({
                "remarks": "RouteMint · 默认出口",
                "network": "tcp,udp",
                "outboundTag": outbound(ref.final),
            })
        elif ref.category in active:
            item = builds[ref.category]
            policy = outbound(ref.policy or "DIRECT")
            # Xray ANDs different match fields on one rule. Emit domain and
            # IP matches separately so either can select this category.
            if item.domain_rules or item.keyword_rules:
                rules.append({
                    "remarks": f"RouteMint · {ref.category} · 域名",
                    "domain": [f"ext:{GEOSITE}:{ref.category}"],
                    "outboundTag": policy,
                })
            if item.ip_rules:
                rules.append({
                    "remarks": f"RouteMint · {ref.category} · IP",
                    "ip": [f"ext:{GEOIP}:{ref.category}"],
                    "outboundTag": policy,
                })
    return rules


def render_v2rayng(paths, presets: list[Preset], builds: dict) -> None:
    assets = paths.dist / "rules" / "v2rayng"
    assets.mkdir(parents=True, exist_ok=True)
    geosite, geoip = _assets(builds)
    (assets / GEOSITE).write_bytes(geosite)
    (assets / GEOIP).write_bytes(geoip)
    for preset in presets:
        for tier in ADS_TIERS:
            dest = paths.dist / "configs" / preset.id / tier / "v2rayng.json"
            write_text(dest, json.dumps(profile(preset, tier, builds), ensure_ascii=False, indent=2))
