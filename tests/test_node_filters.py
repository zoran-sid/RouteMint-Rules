from __future__ import annotations

import re
from pathlib import Path

import pytest

from builder.config import Paths
from builder.spec import Group, load_categories, load_presets

ROOT = Path(__file__).resolve().parents[1]
PRESETS = load_presets(Paths(ROOT), load_categories(Paths(ROOT)))
PRESET_MAP = {preset.id: preset for preset in PRESETS}

# Node names seen in the wild. "US01" is the important one: `\bus\b` does not
# match it, and a positive region filter used to empty the AI group, which
# makes mihomo fall back to DIRECT silently.
SUPPORTED = [
    "US01",
    "US-02",
    "🇺🇸 美国 03",
    "美国 04",
    "JP01",
    "Japan-Tokyo",
    "SG-01",
    "新加坡 02",
    "TW01",
    "UK02",
    "DE01",
    "CA-01",
    "AU01",
    "FR01",
]
UNSUPPORTED_AI = [
    "HK01",
    "🇭🇰 香港 02",
    "香港 03",
    "MO01",
    "澳门 02",
    "CN2 上海",
    "上海 01",
    "回国 01",
    "Russia",
    "RU01",
    "Moscow",
    "伊朗",
]


def _group(preset_id: str, name: str) -> Group:
    preset = PRESET_MAP[preset_id]
    return next(group for group in preset.groups if group.name == name)


def _matches(pattern: str | None, name: str) -> bool:
    return bool(pattern and re.search(pattern, name))


@pytest.mark.parametrize("preset_id", ["cn-mainland", "overseas", "overseas-return", "cn-mainland-lite"])
def test_ai_group_excludes_only_unsupported_regions(preset_id):
    group = _group(preset_id, "🤖 AI 服务")
    assert group.exclude_filter, f"{preset_id}: AI group needs an exclude filter"
    for name in SUPPORTED:
        assert not _matches(group.exclude_filter, name), f"{preset_id}: {name} wrongly excluded"
    for name in UNSUPPORTED_AI:
        assert _matches(group.exclude_filter, name), f"{preset_id}: {name} should be excluded"


@pytest.mark.parametrize("preset_id", ["cn-mainland", "overseas", "overseas-return", "cn-mainland-lite"])
def test_ai_auto_group_has_no_positive_filter(preset_id):
    """A positive region allow-list empties the group for names like US01."""
    group = _group(preset_id, "♻️ AI 自动选择")
    assert group.filter is None
    assert group.exclude_filter


@pytest.mark.parametrize("preset_id", ["cn-mainland", "overseas", "overseas-return", "cn-mainland-lite"])
def test_ai_group_offers_manual_fallback(preset_id):
    group = _group(preset_id, "🤖 AI 服务")
    assert "🚀 节点选择" in group.members
    assert "🎯 全球直连" in group.members


def test_return_group_filters_chinese_nodes():
    group = _group("overseas-return", "🏠 回国")
    for name in ["回国 01", "CN2 上海", "上海-01", "🇨🇳 北京"]:
        assert _matches(group.filter, name), name
    for name in ["US01", "日本 01", "Singapore", "CN2 US01"]:
        assert not _matches(group.filter, name), name


def test_overseas_routes_tiktok_to_its_own_group():
    preset = PRESET_MAP["overseas"]
    refs = {ref.category: ref.policy for ref in preset.rules if ref.category}
    assert refs.get("tiktok") == "🎬 TikTok"
    group = _group("overseas", "🎬 TikTok")
    for name in ["HK01", "香港 02", "CN2 上海"]:
        assert _matches(group.exclude_filter, name), name
    assert not _matches(group.exclude_filter, "US01")


def test_overseas_keeps_unknown_traffic_direct():
    preset = PRESET_MAP["overseas"]
    final = next(ref.final for ref in preset.rules if ref.final)
    group = _group("overseas", final)
    assert group.members[0] == "🎯 全球直连"


def test_return_requires_explicit_mainland_exit():
    group = _group("overseas-return", "🏠 回国")
    assert group.members == ("REJECT",)


def test_streaming_does_not_follow_automatic_latency_switches():
    assert _group("overseas", "🌍 流媒体").members == ()
    for service in ("🎬 Netflix", "🎬 Disney+", "🎬 Max", "🎬 Prime Video"):
        group = _group("overseas", service)
        assert group.type == "select"
        assert group.members[0] == "🌍 流媒体"
