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

CLIENT_FILES = {
    "mihomo": "mihomo.conf",
    "shadowrocket": "shadowrocket.conf",
    "surge": "surge.conf",
    "loon": "loon.conf",
    "quantumultx": "quantumultx.conf",
    "singbox": "singbox.conf",
}


def config_url(urls: dict, preset: str, tier: str, client: str) -> str:
    return (
        f"{urls['jsdelivr']}@{urls['branch']}/configs/{preset}/{tier}/{CLIENT_FILES[client]}"
    )


# Quantumult X QR opens the download URL for manual import.
QR_CLIENTS = ("mihomo", "shadowrocket", "surge", "loon", "singbox", "quantumultx")


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
