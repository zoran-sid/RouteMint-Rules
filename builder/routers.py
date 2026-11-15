"""Native HomeProxy / PassWall (sing-box) routing plans and import bundles."""
from __future__ import annotations

import gzip
import io
import json
import tarfile
from pathlib import Path

from .emit import write_text
from .spec import ADS_TIERS, categories_for

ROUTER_CLIENTS = ("homeproxy", "passwall")
LOCAL_DNS = {"private", "game-download", "steam-direct", "baidu-pan", "cn"}


def router_url(urls: dict, client: str, preset: str, tier: str) -> str:
    return f"{urls['raw']}/{urls['branch']}/routers/{client}/{preset}/{tier}.tar.gz"


def routing_plan(preset, tier: str, builds: dict, urls: dict, client: str) -> dict:
    by_name = {group.name: group for group in preset.groups}
    groups = {}

    def policy(name, final=False):
        if name in {"DIRECT", "REJECT"}:
            return {"DIRECT": "direct", "REJECT": "reject"}[name]
        group = by_name[name]
        if not group.use_providers and len(group.members) == 1 and group.members[0] in {"DIRECT", "REJECT"}:
            return policy(group.members[0])
        if final:
            return policy(group.members[0])
        tag = group.tag.replace("-", "_")
        first = group.members[0] if group.members else ""
        default = "proxy"
        if first in by_name and by_name[first].members == ("DIRECT",):
            default = "direct"
        elif first == "REJECT":
            default = "reject"
        groups[tag] = {"label": group.name, "default": default}
        return tag

    enabled = set(categories_for(preset, tier))
    entries = []
    for ref in preset.rules:
        if ref.final or ref.category not in enabled:
            continue
        item = builds[ref.category]
        if not item.rules:
            continue
        target = policy(ref.policy or "DIRECT")
        entries.append({
            "category": ref.category,
            "policy": target,
            "url": f"{urls['raw']}/{urls['branch']}/rules/{ref.category}/{ref.category}.srs",
            "domains": bool(item.domain_rules or item.keyword_rules),
            "ips": bool(item.ip_rules),
            "dns": "local" if ref.category in LOCAL_DNS else "service",
        })
    default = policy(preset.rules[-1].final, final=True)
    return {"schema": 1, "client": client, "preset": preset.id, "ads": tier,
            "groups": groups, "rules": entries, "default": default,
            "core": "sing-box >= 1.14", "update_interval": "1d"}


def _archive(path: Path, members: dict[str, bytes], root: str) -> None:
    output = io.BytesIO()
    with gzip.GzipFile(fileobj=output, mode="wb", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w") as archive:
            for name, data in members.items():
                info = tarfile.TarInfo(f"{root}/{name}")
                info.size = len(data)
                info.mode = 0o755 if name.endswith(".sh") else 0o644
                archive.addfile(info, io.BytesIO(data))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(output.getvalue())


def render_router_configs(paths, presets: list, builds: dict, urls: dict) -> None:
    installer = (paths.templates / "routers/install.sh").read_text()
    configure = (paths.templates / "routers/configure.uc").read_bytes()
    for client in ROUTER_CLIENTS:
        for preset in presets:
            for tier in ADS_TIERS:
                plan = routing_plan(preset, tier, builds, urls, client)
                data = (json.dumps(plan, ensure_ascii=False, indent=2) + "\n").encode()
                folder = paths.dist / "routers" / client / preset.id / tier
                write_text(folder / "profile.json", data.decode())
                members = {"profile.json": data, "install.sh": installer.replace("@CLIENT@", client).encode(),
                           "configure.uc": configure}
                for name, content in members.items():
                    (folder / name).write_bytes(content)
                _archive(folder.with_suffix(".tar.gz"), members, f"routemint-{client}")
