from __future__ import annotations

import json
from pathlib import Path

import pytest

from builder.evaluate import load_ruleset_list
from builder.spec import ADS_TIERS

ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER = "https://sub.example.com/api/v1/client/subscribe?token=YOUR_TOKEN"


def test_no_budget_violations(built):
    assert built.violations == []


def test_every_preset_and_tier_has_both_configs(built):
    for preset in built.presets:
        for tier in ADS_TIERS:
            for name in ("mihomo.yaml", "shadowrocket.conf"):
                path = built.dist / "configs" / preset.id / tier / name
                assert path.is_file(), path
                assert path.stat().st_size > 500


def test_manifest_counts_match_rule_files(built):
    manifest = json.loads((built.dist / "manifest.json").read_text(encoding="utf-8"))
    for category, info in manifest["categories"].items():
        path = built.dist / "rules" / category / f"{category}.list"
        if not path.is_file():
            continue
        assert len(load_ruleset_list(path)) == info["total"], category


ALLOWED_URL_PREFIXES = (
    "https://cdn.jsdelivr.net/gh/",
    "https://www.gstatic.com/generate_204",
    "https://sub.example.com/",
    "https://dns.alidns.com/",
    "https://doh.pub/",
    "https://1.1.1.1/",
    "https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/",
)


def test_config_urls_are_allowlisted(built):
    for path in (built.dist / "configs").rglob("*"):
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            for token in line.split():
                token = token.strip('",;')
                if token.startswith("http://") or token.startswith("https://"):
                    assert token.startswith(ALLOWED_URL_PREFIXES), f"{path.name}: {token}"


def test_no_real_subscription_is_embedded(built):
    for path in built.dist.rglob("*"):
        if path.is_file() and path.suffix in {".yaml", ".conf", ".list", ".json"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "token=" in text:
                assert "token=YOUR_TOKEN" in text, path
            assert "PLACEHOLDER" not in text


def test_generated_files_stay_under_jsdelivr_limit(built):
    for path in built.dist.rglob("*"):
        if path.is_file():
            assert path.stat().st_size < 20 * 1024 * 1024, path


def test_config_validation_passed(built):
    assert built.config_checks, "mihomo validation did not run"
    failures = [check for check in built.config_checks if not check["ok"]]
    assert failures == [], failures


def test_keyword_rules_are_documented(built):
    specs = {cid: item.spec for cid, item in built.categories.items()}
    for category in built.categories.values():
        for rule in category.keyword_rules:
            assert rule.value in specs[category.spec.id].keyword_reasons


def test_mihomo_yaml_is_wellformed(built):
    import yaml

    for path in (built.dist / "configs").rglob("mihomo.yaml"):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert data["mode"] == "rule"
        assert data["dns"]["enhanced-mode"] == "fake-ip"
        assert data["rules"][-1].startswith("MATCH,")
        assert "airport" in data["proxy-providers"]


def test_shadowrocket_has_managed_config_header(built):
    for path in (built.dist / "configs").rglob("shadowrocket.conf"):
        text = path.read_text(encoding="utf-8")
        assert "[General]" in text and "[Rule]" in text
        assert "update-url" in text
        assert text.rstrip().splitlines()[-1].startswith("FINAL,")
