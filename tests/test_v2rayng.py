from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from builder.protobuf import parse_geosite_list
from builder.spec import ADS_TIERS
from builder.v2rayng import GEOIP, GEOSITE

ROOT = Path(__file__).resolve().parents[1]


def test_v2rayng_preserves_separate_steam_and_netdisk_routes(built):
    domains = parse_geosite_list((built.dist / "rules" / "v2rayng" / GEOSITE).read_bytes())
    assert any(rule.type == 2 and rule.value == "store.steampowered.com" for rule in domains["game-platform"])
    assert any(rule.type == 2 and rule.value == "steampowered.com" for rule in domains["steam-direct"])
    assert any(rule.type == 2 and rule.value == "bcebos.com" for rule in domains["baidu-pan"])
    assert any(rule.type == 0 and rule.value == "apiproxy-device-prod-nlb-" for rule in domains["netflix"])

    for preset in built.presets:
        for tier in ADS_TIERS:
            path = built.dist / "configs" / preset.id / tier / "v2rayng.json"
            rules = json.loads(path.read_text())
            routes = {ref: (index, rule["outboundTag"]) for index, rule in enumerate(rules)
                      for ref in rule.get("domain", []) + rule.get("ip", [])}
            store = routes[f"ext:{GEOSITE}:game-platform"]
            steam = routes[f"ext:{GEOSITE}:steam-direct"]
            assert store[1] == "proxy" and steam[1] == "direct" and store[0] < steam[0]
            assert routes[f"ext:{GEOIP}:steam-direct"][1] == "direct"
            assert routes[f"ext:{GEOSITE}:baidu-pan"][1] == "direct"
            assert not any("domain" in rule and "ip" in rule for rule in rules)
            assert (f"ext:{GEOSITE}:reject-ads" in routes) == (tier != "ads-off")
            assert rules[-1]["network"] == "tcp,udp"
            assert rules[-1]["outboundTag"] == ("proxy" if preset.id.startswith("cn-mainland") else "direct")
            if preset.id == "overseas":
                assert routes[f"ext:{GEOSITE}:cn"][1] == "direct"
                assert routes[f"ext:{GEOSITE}:google"][1] == "direct"
            if preset.id == "overseas-return":
                assert routes[f"ext:{GEOSITE}:cn-region-locked"][1] == "block"


def test_v2rayn_enables_the_same_ordered_routes(built):
    for preset in built.presets:
        for tier in ADS_TIERS:
            folder = built.dist / "configs" / preset.id / tier
            desktop = json.loads((folder / "v2rayn.json").read_text())
            mobile = json.loads((folder / "v2rayng.json").read_text())
            assert desktop == [{"enabled": True, **rule} for rule in mobile]


@pytest.mark.parametrize("client", ["v2rayng", "v2rayn"])
def test_xray_loads_all_profiles_and_geo_assets(built, tmp_path, client):
    xray = Path(os.environ.get("ROUTEMINT_XRAY_BIN", ROOT / ".cache/bin/xray/xray"))
    if not xray.is_file():
        if os.environ.get("CI"):
            pytest.fail("Xray binary is required on CI")
        pytest.skip("Set ROUTEMINT_XRAY_BIN to verify core compatibility")

    env = dict(os.environ, XRAY_LOCATION_ASSET=str(built.dist / "rules" / "v2rayng"))
    config = tmp_path / "config.json"
    for path in sorted((built.dist / "configs").rglob(f"{client}.json")):
        rules = json.loads(path.read_text())
        # Both clients convert their enabled routing entries to Xray field rules.
        hosts = {domain: "127.0.0.1" for rule in rules if rule["outboundTag"] == "block"
                 for domain in rule.get("domain", [])}
        config.write_text(json.dumps({
            "outbounds": [{"tag": tag, "protocol": protocol} for tag, protocol in
                          (("proxy", "freedom"), ("direct", "freedom"), ("block", "blackhole"))],
            "routing": {"domainStrategy": "AsIs", "rules": [
                {"type": "field", **{k: v for k, v in rule.items() if k not in {"remarks", "enabled"}}}
                for rule in rules if rule.get("enabled", True)
            ]},
            "dns": {"hosts": hosts, "servers": ["localhost"]},
        }))
        result = subprocess.run([str(xray), "run", "-test", "-c", str(config)],
                                env=env, text=True, capture_output=True, timeout=20)
        assert result.returncode == 0, f"{path}: {result.stdout}\n{result.stderr}"
