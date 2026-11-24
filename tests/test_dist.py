from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from builder.evaluate import load_ruleset_list
from builder.spec import ADS_TIERS
from builder.render import client_filename

ROOT = Path(__file__).resolve().parents[1]

CONFIGS = {
    "mihomo.conf",
    "shadowrocket.conf",
    "surge.conf",
    "loon.conf",
    "quantumultx.conf",
    "singbox.conf",
    "v2rayng.json",
    "v2rayn.json",
}

ALLOWED_URL_PREFIXES = (
    "https://cdn.jsdelivr.net/gh/",
    "https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/",
    "https://www.gstatic.com/generate_204",
    "http://www.gstatic.com/generate_204",
    "https://sub.example.com/",
    "https://dns.alidns.com/",
    "https://doh.pub/",
    "https://1.1.1.1/",
)


def _configs(built, suffix: str):
    paths = sorted(
        path
        for path in (built.dist / "configs").rglob("*")
        if path.is_file() and (path.name.endswith(suffix) if suffix else path.name in CONFIGS)
    )
    assert paths, f"no config files for suffix {suffix!r}"
    return paths


def test_no_budget_violations(built):
    assert built.violations == []


def test_every_preset_and_tier_has_all_configs(built):
    for preset in built.presets:
        for tier in ADS_TIERS:
            folder = built.dist / "configs" / preset.id / tier
            present = {path.name for path in folder.iterdir() if path.is_file()}
            assert present == CONFIGS | {client_filename("shadowrocket", preset.id, tier)}, f"{preset.id}/{tier}: {sorted(present)}"


def test_manifest_counts_match_rule_files(built):
    manifest = json.loads((built.dist / "manifest.json").read_text(encoding="utf-8"))
    for category, info in manifest["categories"].items():
        path = built.dist / "rules" / category / f"{category}.list"
        if not path.is_file():
            continue
        assert len(load_ruleset_list(path)) == info["total"], category


def test_config_urls_are_allowlisted(built):
    for path in _configs(built, ""):
        for line in path.read_text(encoding="utf-8").splitlines():
            for token in line.replace(",", " ").split():
                token = token.strip('",;')
                if token.startswith(("http://", "https://")):
                    assert token.startswith(ALLOWED_URL_PREFIXES), f"{path.name}: {token}"


def test_no_credentials_are_embedded(built):
    forbidden = re.compile(r"(password|passwd|secret|private-key|uuid)\s*[:=]", re.I)
    for path in _configs(built, ""):
        text = path.read_text(encoding="utf-8")
        assert not forbidden.search(text), path.name
        if "token=" in text:
            assert "token=YOUR_TOKEN" in text, path.name


def test_generated_files_stay_under_jsdelivr_limit(built):
    for path in built.dist.rglob("*"):
        if path.is_file():
            assert path.stat().st_size < 20 * 1024 * 1024, path


def test_config_validation_passed(built):
    assert built.config_checks, "mihomo / sing-box validation did not run"
    assert len(built.config_checks) == len(built.presets) * len(ADS_TIERS) * 2
    failures = [check for check in built.config_checks if not check["ok"]]
    assert failures == [], failures


def test_keyword_rules_are_documented(built):
    for category in built.categories.values():
        for rule in category.keyword_rules:
            assert rule.value in category.spec.keyword_reasons


# -- per-client structural checks -------------------------------------------
def test_mihomo_yaml_is_wellformed(built):
    for path in _configs(built, "mihomo.conf"):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert data["mode"] == "rule"
        assert data["dns"]["enhanced-mode"] == "fake-ip"
        assert data["rules"][-1].startswith("MATCH,")
        assert "airport" in data["proxy-providers"]


def test_mihomo_provider_urls_resolve_to_files(built):
    prefix = "https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/"
    for path in _configs(built, "mihomo.conf"):
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line.startswith("url:") or prefix not in line:
                continue
            relative = line.split(prefix, 1)[1].strip('"')
            assert (built.dist / relative).is_file(), f"{path.name}: missing {relative}"


def test_mihomo_providers_match_rules(built):
    for path in _configs(built, "mihomo.conf"):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        declared = set(data.get("rule-providers") or {})
        used = {r.split(",")[1] for r in data["rules"] if r.startswith("RULE-SET,")}
        assert used == declared, f"{path.name}: used={used} declared={declared}"


def test_shadowrocket_has_managed_config_header(built):
    for path in _configs(built, "shadowrocket.conf"):
        text = path.read_text(encoding="utf-8")
        assert "[General]" in text and "[Rule]" in text
        assert "update-url" in text
        assert text.rstrip().splitlines()[-1].startswith("FINAL,")


def test_surge_config(built):
    for path in _configs(built, "surge.conf"):
        text = path.read_text(encoding="utf-8")
        assert text.startswith("#!MANAGED-CONFIG "), path.name
        assert "policy-path=https://sub.example.com/" in text
        assert "[Proxy Group]" in text and "[Rule]" in text
        assert text.rstrip().splitlines()[-1].startswith("FINAL,")
        assert "RULE-SET,https://cdn.jsdelivr.net/gh/" in text


def test_loon_config(built):
    for path in _configs(built, "loon.conf"):
        text = path.read_text(encoding="utf-8")
        assert "[Remote Proxy]" in text
        assert "[Remote Rule]" in text
        assert "policy=🛑 广告拦截" in text or "policy=" in text
        assert text.rstrip().splitlines()[-1].startswith("FINAL,")
        assert "RULE-SET" not in text, "Loon uses [Remote Rule], not RULE-SET"


def test_quantumultx_config(built):
    for path in _configs(built, "quantumultx.conf"):
        text = path.read_text(encoding="utf-8")
        assert "[server_remote]" in text
        assert "tag=Airport" in text
        assert "[filter_remote]" in text
        assert "force-policy=" in text
        assert re.search(r"^final, ", text, re.M)


def test_qx_rule_files_use_qx_grammar(built):
    pattern = re.compile(r"^(host|host-suffix|host-keyword|ip-cidr|ip6-cidr), \S+$")
    seen = 0
    for path in sorted((built.dist / "rules").rglob("*-qx.list")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#"):
                continue
            assert pattern.match(line), f"{path.name}: {line}"
            seen += 1
    assert seen > 1000


def test_singbox_config_structure(built):
    for path in _configs(built, "singbox.conf"):
        data = json.loads(path.read_text(encoding="utf-8"))
        tags = [outbound["tag"] for outbound in data["outbounds"]]
        assert len(tags) == len(set(tags)), f"{path.name}: duplicate outbound tag"
        assert "direct" in tags and "block" in tags and "airport" in tags
        rule_set_tags = {rs["tag"] for rs in data["route"]["rule_set"]}
        for rule in data["route"]["rules"]:
            if "rule_set" in rule:
                assert rule["rule_set"] in rule_set_tags, f"{path.name}: {rule}"
            if "outbound" in rule:
                assert rule["outbound"] in tags, f"{path.name}: {rule}"
        for rs in data["route"]["rule_set"]:
            assert rs["url"].endswith(".srs")
        assert data["route"]["final"] in tags
        assert data["route"]["default_domain_resolver"]["server"] == (
            "domestic" if any(part.startswith("cn-mainland") for part in path.parts) else "local"
        )


def test_singbox_rule_files(built):
    seen = 0
    for path in sorted((built.dist / "rules").rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["version"] == 5
        assert data["rules"]
        seen += 1
    assert seen >= 20


ALLOWED_RULE_SUFFIXES = {"-qx.list", ".list", ".yaml", ".mrs", ".json", ".srs", ".dat"}


def test_rule_dirs_contain_only_expected_files(built):
    for path in (built.dist / "rules").rglob("*"):
        if not path.is_file():
            continue
        assert any(path.name.endswith(suffix) for suffix in ALLOWED_RULE_SUFFIXES), path


def test_config_extensions_follow_client_format(built):
    for path in (built.dist / "configs").rglob("*"):
        if path.is_file():
            assert path.suffix == (".json" if path.name in {"v2rayng.json", "v2rayn.json"} else ".conf"), path.name


def test_readme_has_no_stale_config_extensions():
    text = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")
    assert "/mihomo.yaml" not in text
    assert "/singbox.json" not in text


def test_qx_downloads_qx_rules_and_keeps_local_keyword_grammar(built):
    prefix = "https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/"
    for path in _configs(built, "quantumultx.conf"):
        text = path.read_text()
        remote = text.split("[filter_remote]\n", 1)[1].split("[filter_local]", 1)[0]
        for line in remote.splitlines():
            if line.startswith(prefix):
                url = line.split(",", 1)[0]
                assert url.endswith("-qx.list")
                assert (built.dist / url.removeprefix(prefix)).is_file()
        local = text.split("[filter_local]\n", 1)[1]
        assert "DOMAIN-KEYWORD" not in local
        if path.parts[-3] == "overseas":
            assert "host-keyword, apiproxy-device-prod-nlb-, 🎬 Netflix" in local


def test_return_group_remains_selectable_and_rejects_until_configured(built):
    folder = built.dist / "configs/overseas-return/ads-light"
    qx = (folder / "quantumultx.conf").read_text()
    assert "static = 🏠 回国, reject, resource-tag-regex=^Airport$" in qx
    assert "tag=cn-region-locked, force-policy=🏠 回国" in qx
    assert "static = 🤖 AI 服务, direct," in qx
    assert "final, direct" in qx
    for client in ("surge", "loon", "shadowrocket"):
        text = (folder / f"{client}.conf").read_text()
        line = next(line for line in text.splitlines() if line.startswith("🏠 回国 ="))
        assert "REJECT" in line and "🚀 节点选择" not in line
        if client in {"loon", "shadowrocket"}:
            assert line.startswith("🏠 回国 = select, REJECT,")
    mh = yaml.safe_load((folder / "mihomo.conf").read_text())
    group = next(g for g in mh["proxy-groups"] if g["name"] == "🏠 回国")
    assert group["proxies"] == ["REJECT"]
    sb = json.loads((folder / "singbox.conf").read_text())
    group = next(g for g in sb["outbounds"] if g["tag"] == "cn-return")
    assert group["default"] == "block" and "airport" in group["outbounds"]


def test_service_dns_uses_the_service_exit_and_overseas_defaults_are_local(built):
    for scene, category, policy, sbtag in (
        ("overseas", "netflix", "🎬 Netflix", "netflix"),
        ("overseas", "ai-openai", "🤖 AI 服务", "ai"),
        ("overseas-return", "cn-region-locked", "🏠 回国", "cn-return"),
    ):
        folder = built.dist / "configs" / scene / "ads-light"
        mh = yaml.safe_load((folder / "mihomo.conf").read_text())
        assert mh["dns"]["nameserver"] == ["system"]
        assert all(server.endswith(f"#{policy}") for server in mh["dns"]["nameserver-policy"][f"rule-set:{category}"])
        sb = json.loads((folder / "singbox.conf").read_text())
        assert sb["dns"]["final"] == "local"
        rule = next(rule for rule in sb["dns"]["rules"] if rule["rule_set"] == f"rs-{category}")
        server = next(server for server in sb["dns"]["servers"] if server["tag"] == rule["server"])
        assert server["detour"] == sbtag
        assert "/" not in server["server"] and server["path"] == "/dns-query"


def test_shadowrocket_update_url_is_a_plain_url_and_named_profile_exists(built):
    from urllib.parse import urlsplit

    names = set()
    for preset in built.presets:
        for tier in ADS_TIERS:
            folder = built.dist / "configs" / preset.id / tier
            legacy = folder / "shadowrocket.conf"
            named = folder / client_filename("shadowrocket", preset.id, tier)
            assert named.read_bytes() == legacy.read_bytes()
            assert named.stem.startswith("RouteMint-")
            names.add(named.name)
            line = next(line for line in named.read_text().splitlines() if line.startswith("update-url ="))
            url = line.split("=", 1)[1].strip()
            assert not any(c.isspace() for c in url), "Shadowrocket treats trailing interval text as URL path"
            assert urlsplit(url).scheme == "https"
            assert url.startswith("https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/")
            relative = urlsplit(url).path.split("/release/", 1)[1]
            assert (built.dist / relative).read_bytes() == named.read_bytes()
            rule_urls = [line.split(",")[1] for line in named.read_text().splitlines() if line.startswith("RULE-SET,")]
            assert rule_urls and all(u.startswith("https://raw.githubusercontent.com/") for u in rule_urls)
    assert len(names) == len(built.presets) * len(ADS_TIERS)


def test_downloads_and_netdisk_use_local_dns_in_every_scene(built):
    for preset in built.presets:
        folder = built.dist / "configs" / preset.id / "ads-light"
        mh = yaml.safe_load((folder / "mihomo.conf").read_text())
        sb = json.loads((folder / "singbox.conf").read_text())
        for category in ("game-download", "baidu-pan", "steam-direct"):
            assert mh["dns"]["nameserver-policy"][f"rule-set:{category}"] == ["system"]
            assert f"RULE-SET,{category},🎯 全球直连" in mh["rules"]
            rule = next(r for r in sb["dns"]["rules"] if r["rule_set"] == f"rs-{category}")
            assert rule["server"] == "local"
        game_download = next(i for i, r in enumerate(mh["rules"]) if r.startswith("RULE-SET,game-download,"))
        game_platform = next(i for i, r in enumerate(mh["rules"]) if r.startswith("RULE-SET,game-platform,"))
        assert game_download < game_platform
