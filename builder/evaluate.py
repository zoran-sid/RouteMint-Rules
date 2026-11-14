"""Evaluate which category a domain/IP lands in, using the built artifacts.

Used by the smoke tests (``tests/expectations.yaml``) and by
``python -m builder explain`` style debugging.  It deliberately reads
``dist/rules/**/*.list`` rather than in-memory data: the test must prove that
what users download actually routes correctly.
"""

from __future__ import annotations

from pathlib import Path

from .model import Rule, RuleError
from .spec import Preset, categories_for

_CACHE: dict[Path, list[Rule]] = {}


def load_ruleset_list(path: Path) -> list[Rule]:
    key = path.resolve()
    if key in _CACHE:
        return _CACHE[key]
    rules: list[Rule] = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                # Lists may carry a trailing ",no-resolve"; Rule.parse ignores it.
                rules.append(Rule.parse(line))
            except (RuleError, ValueError):
                continue
    _CACHE[key] = rules
    return rules


def tier_categories(preset: Preset, tier: str) -> list[str]:
    return categories_for(preset, tier)


def explain(dist: Path, preset: Preset, tier: str, target: str) -> tuple[str, str] | None:
    """Return ``(category, policy)`` for the first rule that matches."""
    import ipaddress

    is_ip = True
    try:
        ipaddress.ip_address(target)
    except ValueError:
        is_ip = False

    for ref in preset.rules:
        if not ref.category or ref.category not in tier_categories(preset, tier):
            continue
        path = dist / "rules" / ref.category / f"{ref.category}.list"
        for rule in load_ruleset_list(path):
            if is_ip and rule.matches_ip(target):
                return ref.category, ref.policy or "DIRECT"
            if not is_ip and rule.matches_domain(target):
                return ref.category, ref.policy or "DIRECT"
    final = next((ref.final for ref in preset.rules if ref.final), None)
    if final:
        return "FINAL", final
    return None
