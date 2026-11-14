from __future__ import annotations

import re
from pathlib import Path

import pytest

from builder.qr import CLIENT_FILES, config_url, generate, qr_payload

ROOT = Path(__file__).resolve().parents[1]
QR_DIR = ROOT / "docs" / "qr"
PRESETS = ["cn-mainland", "cn-mainland-lite", "overseas", "overseas-return"]


def test_all_qr_codes_exist():
    expected = {f"{preset}-{client}.png" for preset in PRESETS for client in CLIENT_FILES}
    present = {path.name for path in QR_DIR.glob("*.png")}
    assert expected <= present, sorted(expected - present)


def test_qr_codes_are_current(tmp_path: Path):
    written = generate(
        __import__("builder.config", fromlist=["Paths"]).Paths(ROOT), tmp_path, PRESETS
    )
    assert len(written) == len(PRESETS) * len(CLIENT_FILES)
    for path in written:
        committed = QR_DIR / path.name
        assert committed.read_bytes() == path.read_bytes(), f"{path.name} is stale"


def test_qr_payload_uses_client_scheme():
    url = "https://cdn.jsdelivr.net/gh/o/r@release/configs/cn-mainland/ads-light/mihomo.yaml"
    assert qr_payload("mihomo", url).startswith("clash://install-config?url=https%3A%2F%2F")
    assert qr_payload("loon", url).startswith("loon://import?sub=")
    assert qr_payload("surge", url).startswith("surge:///install-config?url=")
    assert qr_payload("singbox", url).startswith("sing-box://import-remote-profile?url=")
    assert qr_payload("shadowrocket", url) == url


def test_config_url_points_at_release_branch():
    urls = {"jsdelivr": "https://cdn.jsdelivr.net/gh/o/r", "branch": "release"}
    assert config_url(urls, "overseas", "ads-light", "mihomo").endswith(
        "/configs/overseas/ads-light/mihomo.yaml"
    )
    assert "@release" in config_url(urls, "overseas", "ads-light", "mihomo")


def test_readme_references_every_preset_qr():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for preset in PRESETS:
        assert f"docs/qr/{preset}-mihomo.png" in text
    for client in ("surge", "loon", "quantumultx", "singbox"):
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
