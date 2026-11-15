from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from builder.evaluate import explain

ROOT = Path(__file__).resolve().parents[1]
CASES = yaml.safe_load((ROOT / "tests" / "expectations.yaml").read_text(encoding="utf-8"))["cases"]


@pytest.mark.parametrize("case", CASES, ids=[c["domain"] for c in CASES])
def test_domain_routes_to_expected_category(built, preset_map, case):
    preset = preset_map[case["preset"]]
    result = explain(built.dist, preset, preset.ads, case["domain"])
    assert result is not None, f"{case['domain']} matched no rule in {preset.id}"
    category, policy = result
    assert category == case["category"], f"{case['domain']} hit {category}"
    assert policy == case["policy"], f"{case['domain']} routed to {policy}"


def test_ai_domain_is_not_in_proxy(built):
    proxy = built.categories["proxy"].rules
    proxy_values = {rule.value for rule in proxy}
    for value in ("openai.com", "anthropic.com", "claude.ai", "perplexity.ai"):
        assert value not in proxy_values, f"{value} leaked into proxy"


def test_cn_and_proxy_are_disjoint(built):
    cn = {rule.value for rule in built.categories["cn"].rules}
    proxy = {rule.value for rule in built.categories["proxy"].rules}
    assert not (cn & proxy), sorted(cn & proxy)[:5]


@pytest.mark.parametrize("preset_id", ["cn-mainland", "cn-mainland-lite", "overseas", "overseas-return"])
def test_game_downloads_direct_but_stores_proxy(built, preset_map, preset_id):
    preset = preset_map[preset_id]
    for domain in (
        "cache1-sgp1.steamcontent.com", "steampipe.akamaized.net", "dl.steam.clngaa.com",
        "st.dl.bscstorage.net", "blzddist1-a.akamaihd.net", "us.cdn.blizzard.com",
        "blzdist-wow.necdn.leihuo.netease.com", "download2.epicgames.com",
        "epicgames-download1-1251447533.file.myqcloud.com", "egdownload.fastly-edge.com",
        "prod.cloudflare.cdn.ea.com", "origin-a.akamaihd.net",
        "uplaypc-s-ubisoft-ww.cdn.ubi.com", "gog-cdn.akamaized.net",
        "lol.secure.dyn.riotcdn.net", "gamedownloads-rockstargames-com.akamaized.net",
        "assets1.xboxlive.com", "dl.playstation.net", "cdn.nintendo.net",
    ):
        assert explain(built.dist, preset, "ads-light", domain) == ("game-download", "🎯 全球直连"), domain
    for domain in ("store.steampowered.com", "steamcommunity.com", "store.epicgames.com", "battle.net", "ea.com", "gog.com", "ubisoft.com"):
        category, policy = explain(built.dist, preset, "ads-light", domain)
        assert category == "game-platform", (domain, category)
        assert policy in {"🚀 节点选择", "🌍 境外服务"}, (domain, policy)
    for domain in ("pan.baidu.com", "yun.baidu.com", "d.pcs.baidu.com", "download.baidupcs.com", "baiduyuncdn.com"):
        category, policy = explain(built.dist, preset, "ads-light", domain)
        assert (category, policy) == ("baidu-pan", "🎯 全球直连"), (domain, category, policy)
