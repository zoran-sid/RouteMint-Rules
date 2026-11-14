from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from builder.evaluate import load_ruleset_list
from builder.spec import ADS_TIERS

ROOT = Path(__file__).resolve().parents[1]

CONFIGS = {
    "mihomo.yaml",
    "shadowrocket.conf",
    "surge.conf",
    "loon.conf",
    "quantumultx.conf",
    "singbox.json",
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
            assert present == CONFIGS, f"{preset.id}/{tier}: {sorted(present)}"


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
    for path in _configs(built, "mihomo.yaml"):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert data["mode"] == "rule"
        assert data["dns"]["enhanced-mode"] == "fake-ip"
        assert data["rules"][-1].startswith("MATCH,")
        assert "airport" in data["proxy-providers"]


def test_mihomo_provider_urls_resolve_to_files(built):
    prefix = "https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/"
    for path in _configs(built, "mihomo.yaml"):
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line.startswith("url:") or prefix not in line:
                continue
            relative = line.split(prefix, 1)[1].strip('"')
            assert (built.dist / relative).is_file(), f"{path.name}: missing {relative}"


def test_mihomo_providers_match_rules(built):
    for path in _configs(built, "mihomo.yaml"):
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
    for path in _configs(built, "singbox.json"):
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
        assert data["route"]["default_domain_resolver"]["server"] == "domestic"


def test_singbox_rule_files(built):
    seen = 0
    for path in sorted((built.dist / "rules").rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["version"] == 5
        assert data["rules"]
        seen += 1
    assert seen >= 20


ALLOWED_RULE_SUFFIXES = {"-qx.list", ".list", ".yaml", ".mrs", ".json", ".srs"}


def test_rule_dirs_contain_only_expected_files(built):
    for path in (built.dist / "rules").rglob("*"):
        if not path.is_file():
            continue
        assert any(path.name.endswith(suffix) for suffix in ALLOWED_RULE_SUFFIXES), path
