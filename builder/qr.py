"""Generate the import QR codes used by the README.

One image per preset x client, committed under ``docs/qr/`` so GitHub can render
them without a third-party service.  CI regenerates them and fails if the
committed files are stale.
"""

from __future__ import annotations

import urllib.parse
from pathlib import Path

import segno

from .build import load_distribution
from .config import Paths
from .render import client_filename
from .routers import ROUTER_CLIENTS, router_url


def config_url(urls: dict, preset: str, tier: str, client: str) -> str:
    if client in ROUTER_CLIENTS:
        return router_url(urls, client, preset, tier)
    if client == "v2rayng":
        return f"{urls['raw']}/{urls['branch']}/configs/{preset}/{tier}/v2rayng.json"
    base_url = (f"{urls['raw']}/{urls['branch']}" if client == "shadowrocket"
                else f"{urls['jsdelivr']}@{urls['branch']}")
    return f"{base_url}/configs/{preset}/{tier}/{client_filename(client, preset, tier)}"


# Quantumult X and v2rayNG QR codes open the download for manual import.
QR_CLIENTS = ("mihomo", "shadowrocket", "surge", "loon", "singbox", "quantumultx", "v2rayng", *ROUTER_CLIENTS)


def qr_payload(client: str, url: str) -> str:
    """Encode the client's import scheme.

    Shadowrocket must use ``shadowrocket://config/add/<url>``; a bare https URL
    is interpreted as a *proxy subscription*, not as a config file.
    """
    encoded = urllib.parse.quote(url, safe="")
    if client == "mihomo":
        return f"clash://install-config?url={encoded}"
    if client == "shadowrocket":
        return f"shadowrocket://config/add/{url}"
    if client == "surge":
        return f"surge:///install-config?url={encoded}"
    if client == "loon":
        return f"loon://import?sub={encoded}"
    if client == "singbox":
        return f"sing-box://import-remote-profile?url={encoded}"
    return url


def generate(paths: Paths, out: Path, presets: list[str] | None = None) -> list[Path]:
    urls = load_distribution(paths)
    preset_ids = presets or ["cn-mainland", "cn-mainland-lite", "overseas", "overseas-return"]
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for preset in preset_ids:
        tier = "ads-light"
        for client in QR_CLIENTS:
            path = out / f"{preset}-{client}.png"
            payload = qr_payload(client, config_url(urls, preset, tier, client))
            segno.make(payload, error="m").save(
                path, scale=5, border=4, dark="#111111", light="#ffffff"
            )
            written.append(path)
    return written
