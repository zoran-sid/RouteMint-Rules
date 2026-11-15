from __future__ import annotations

import json
import os
import subprocess
import tarfile
from pathlib import Path

import pytest

from builder.routers import ROUTER_CLIENTS
from builder.spec import ADS_TIERS, categories_for

ROOT = Path(__file__).resolve().parents[1]


def _folder(built, app, scene="cn-mainland", tier="ads-light"):
    return built.dist / "routers" / app / scene / tier


def test_router_bundles_share_the_preset_rule_order(built):
    for app in ROUTER_CLIENTS:
        for preset in built.presets:
            for tier in ADS_TIERS:
                folder = _folder(built, app, preset.id, tier)
                plan = json.loads((folder / "profile.json").read_text())
                assert [r["category"] for r in plan["rules"]] == categories_for(preset, tier)
                assert plan["default"] == ("proxy" if preset.id.startswith("cn-mainland") else "direct")
                assert plan["client"] == app
                for rule in plan["rules"]:
                    relative = rule["url"].split("/release/", 1)[1]
                    assert (built.dist / relative).is_file()
                    assert rule["policy"] in {"direct", "reject"} | set(plan["groups"])
                with tarfile.open(folder.with_suffix(".tar.gz")) as archive:
                    assert set(archive.getnames()) == {f"routemint-{app}/{n}" for n in ("install.sh", "configure.uc", "profile.json")}
                    assert archive.extractfile(f"routemint-{app}/profile.json").read() == (folder / "profile.json").read_bytes()
                subprocess.run(["sh", "-n", str(folder / "install.sh")], check=True)


@pytest.fixture(scope="module")
def ucode():
    binary = Path(os.environ.get("ROUTEMINT_UCODE_BIN", ROOT / ".cache/ucode-build/ucode"))
    if not binary.is_file():
        if os.environ.get("CI"):
            pytest.fail("ucode runtime is required on CI")
        pytest.skip("Build ucode or set ROUTEMINT_UCODE_BIN for router integration tests")
    return binary.resolve()


def _run(ucode, folder, tmp_path, app, *, node="node1", rerun=False):
    config = tmp_path / "config"
    config.mkdir(exist_ok=True)
    (tmp_path / "delta").mkdir(exist_ok=True)
    if not rerun:
        if app == "homeproxy":
            state = {"config": {".name": "config", ".type": "homeproxy", "main_node": "node1"},
                     "node1": {".name": "node1", ".type": "node", "address": "private.example", "password": "preserved"},
                     "custom_old": {".name": "custom_old", ".type": "routing_rule", "enabled": "1"}}
        else:
            state = {"global": {".name": "global", ".type": "global", "tcp_node": "node1"},
                     "node1": {".name": "node1", ".type": "nodes", "type": "sing-box", "protocol": "trojan", "password": "preserved"},
                     "custom_old": {".name": "custom_old", ".type": "shunt_rules", "group": "Other", "domain_list": "domain:example.com"}}
        (config / app).write_text(json.dumps(state))
    source = (folder / "configure.uc").read_text()
    # Redirect only the device-specific source path; execute the real adapter logic.
    generator = tmp_path / "generate_client.uc"
    generator.write_text("const uci = cursor();\nwritefile(RUN_DIR + '/sing-box-c.json', '{}');\n")
    source = source.replace("'/etc/homeproxy/scripts/generate_client.uc'", json.dumps(str(generator)))
    script = tmp_path / "configure.uc"
    script.write_text(source)
    env = {**os.environ, "RM_STAGE": str(tmp_path), "RM_PLAN": str(folder / "profile.json"), "RM_APP": app, "RM_PROXY_NODE": node}
    result = subprocess.run([str(ucode), "-L", str(ucode.parent), "-L", str(ROOT / "tests/fixtures/router"), "-S", str(script)], env=env, text=True, capture_output=True)
    return result, json.loads((config / app).read_text())


@pytest.mark.parametrize("app", ROUTER_CLIENTS)
@pytest.mark.parametrize("scene", ["cn-mainland", "cn-mainland-lite", "overseas", "overseas-return"])
def test_native_ucode_import_keeps_credentials_and_order(built, ucode, tmp_path, app, scene):
    result, state = _run(ucode, _folder(built, app, scene), tmp_path, app)
    assert result.returncode == 0, result.stderr
    assert state["node1"]["password"] == "preserved"
    order = list(state)
    assert order.index("rm_route_game_platform") < order.index("rm_route_steam_direct")
    assert order.index("rm_route_steam_direct") < order.index("rm_route_cn")
    if app == "homeproxy":
        assert state["rm_route_steam_direct"]["outbound"] == "direct-out"
        assert state["rm_query_steam_direct"]["server"] == "default-dns"
        assert state["rm_query_baidu_pan"]["server"] == "default-dns"
        assert state["custom_old"]["enabled"] == "0"
        assert state["config"]["routing_mode"] == "custom"
        assert state["routing"]["default_outbound"] == ("rm_proxy" if scene.startswith("cn-mainland") else "direct-out")
        if scene == "overseas-return":
            assert state["rm_route_cn_region_locked"]["action"] == "reject"
            assert state["rm_route_ai_openai"]["outbound"] == "direct-out"
        assert "RM_STAGE" in (tmp_path / "generate-preview.uc").read_text()
    else:
        assert state["rm_shunt"]["protocol"] == "_shunt"
        assert state["rm_shunt"]["rm_route_steam_direct"] == "_direct"
        assert state["rm_shunt"]["rm_route_game_platform"] == "node1"
        assert state["rm_shunt"]["default_node"] == ("node1" if scene.startswith("cn-mainland") else "_direct")
        assert state["rm_route_cn_ip"]["ip_list"].startswith("rule-set:remote:https://")
        assert state["global"]["tcp_node"] == "node1"  # activation is explicit in LuCI
        assert state["custom_old"]["group"] == "Other"
    result, again = _run(ucode, _folder(built, app, scene), tmp_path, app, rerun=True)
    assert result.returncode == 0 and again == state, result.stderr


@pytest.mark.parametrize("app", ROUTER_CLIENTS)
def test_invalid_node_aborts_before_staged_commit(built, ucode, tmp_path, app):
    result, state = _run(ucode, _folder(built, app), tmp_path, app, node="does_not_exist")
    assert result.returncode != 0
    assert not any(key.startswith("rm_") for key in state)
    assert state["node1"]["password"] == "preserved"
