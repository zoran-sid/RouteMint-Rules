from __future__ import annotations

import re
from pathlib import Path

import pytest

from builder.qr import QR_CLIENTS, config_url, generate, qr_payload

ROOT = Path(__file__).resolve().parents[1]
QR_DIR = ROOT / "docs" / "qr"
PRESETS = ["cn-mainland", "cn-mainland-lite", "overseas", "overseas-return"]


def test_all_qr_codes_exist():
    expected = {f"{preset}-{client}.png" for preset in PRESETS for client in QR_CLIENTS}
    present = {path.name for path in QR_DIR.glob("*.png")}
    assert expected <= present, sorted(expected - present)


def test_qr_codes_are_current(tmp_path: Path):
    written = generate(
        __import__("builder.config", fromlist=["Paths"]).Paths(ROOT), tmp_path, PRESETS
    )
    assert len(written) == len(PRESETS) * len(QR_CLIENTS)
    for path in written:
        committed = QR_DIR / path.name
        assert committed.read_bytes() == path.read_bytes(), f"{path.name} is stale"


def test_qr_payload_uses_client_scheme():
    url = "https://cdn.jsdelivr.net/gh/o/r@release/configs/cn-mainland/ads-light/mihomo.conf"
    assert qr_payload("mihomo", url).startswith("clash://install-config?url=https%3A%2F%2F")
    assert qr_payload("loon", url).startswith("loon://import?sub=")
    assert qr_payload("surge", url).startswith("surge:///install-config?url=")
    assert qr_payload("singbox", url).startswith("sing-box://import-remote-profile?url=")
    assert qr_payload("shadowrocket", url) == f"shadowrocket://config/add/{url}"


def test_config_url_points_at_release_branch():
    urls = {"jsdelivr": "https://cdn.jsdelivr.net/gh/o/r", "branch": "release"}
    assert config_url(urls, "overseas", "ads-light", "mihomo").endswith(
        "/configs/overseas/ads-light/mihomo.conf"
    )
    assert "@release" in config_url(urls, "overseas", "ads-light", "mihomo")


def test_readme_references_every_preset_qr():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for preset in PRESETS:
        assert f"docs/qr/{preset}-mihomo.png" in text
    for client in ("surge", "loon", "singbox"):
        assert f"docs/qr/cn-mainland-{client}.png" in text


def test_readme_links_resolve():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for target in re.findall(r"\]\((docs/[^)#]+)", text):
        assert (ROOT / target).is_file(), target


def test_category_table_is_rendered_in_docs():
    text = (ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")
    assert "<!-- BEGIN CATEGORY TABLE -->" in text
    body = text.split("<!-- BEGIN CATEGORY TABLE -->")[1].split("<!-- END CATEGORY TABLE -->")[0]
    assert "| `cn` |" in body
    assert "| 分类 | 内容 | 条数 | 推荐策略 |" in body


@pytest.mark.parametrize("name", ["architecture.md", "quality.md", "development.md"])
def test_docs_are_not_empty(name):
    path = ROOT / "docs" / name
    assert path.is_file()
    assert len(path.read_text(encoding="utf-8")) > 500


def test_shadowrocket_qr_is_not_a_subscription():
    """Regression: a bare https QR made Shadowrocket add a subscription."""
    import zxingcpp
    from PIL import Image

    image = Image.open(QR_DIR / "cn-mainland-shadowrocket.png")
    payload = zxingcpp.read_barcodes(image)[0].text
    assert payload.startswith("shadowrocket://config/add/https://")
    assert not payload.startswith("https://")


def test_every_qr_decodes_to_its_client_scheme():
    import zxingcpp
    from PIL import Image

    prefixes = {
        "mihomo": "clash://install-config?url=",
        "shadowrocket": "shadowrocket://config/add/https://",
        "surge": "surge:///install-config?url=",
        "loon": "loon://import?sub=",
        "singbox": "sing-box://import-remote-profile?url=",
        "quantumultx": "https://cdn.jsdelivr.net/gh/",
        "v2rayng": "https://raw.githubusercontent.com/",
        "homeproxy": "https://raw.githubusercontent.com/",
        "passwall": "https://raw.githubusercontent.com/",
    }
    for path in sorted(QR_DIR.glob("*.png")):
        client = next(c for c in prefixes if path.name.endswith(f"-{c}.png"))
        payload = zxingcpp.read_barcodes(Image.open(path))[0].text
        assert payload.startswith(prefixes[client]), f"{path.name}: {payload[:60]}"
        from builder.build import load_distribution
        from builder.config import Paths

        preset = path.name.removesuffix(f"-{client}.png")
        url = config_url(load_distribution(Paths(ROOT)), preset, "ads-light", client)
        assert payload == qr_payload(client, url), f"{path.name}: wrong configuration URL"


def test_readme_offers_full_urls_and_matching_qr_for_each_client():
    from builder.build import load_distribution
    from builder.config import Paths

    text = (ROOT / "README.md").read_text()
    urls = load_distribution(Paths(ROOT))
    for preset in PRESETS:
        for client in QR_CLIENTS:
            assert config_url(urls, preset, "ads-light", client) in text
            assert f"docs/qr/{preset}-{client}.png" in text
