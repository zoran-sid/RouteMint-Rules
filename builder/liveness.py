"""Report-only liveness sampling for hand-maintained domains.

Hand-written rules rot: a service shuts down, a domain is parked, a typo lands.
This module resolves a rotating sample of ``sources/*.yaml`` ``add`` entries and
flags the ones that keep returning NXDOMAIN.  It never fails the build — dead
domains are a cleanup hint, not a routing error.
"""

from __future__ import annotations

import socket
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from .model import Rule, RuleType
from .spec import CategorySpec

NXDOMAIN_ERRNOS = {-2, -5}  # EAI_NONAME / EAI_NODATA (platform dependent)


@dataclass(frozen=True)
class LivenessResult:
    rule: Rule
    category: str
    status: str  # ok | dead | unknown


def candidates(specs: dict[str, CategorySpec], limit: int, seed: str) -> list[tuple[str, Rule]]:
    """Pick a deterministic, date-rotated sample of manual domain rules."""
    pool: list[tuple[str, Rule]] = []
    for cid, spec in sorted(specs.items()):
        for rule in spec.add:
            if rule.type in (RuleType.DOMAIN, RuleType.DOMAIN_SUFFIX):
                if "." in rule.value and not rule.value.endswith((".local", ".lan")):
                    pool.append((cid, rule))
    if not pool:
        return []
    # Rotate by seed so consecutive daily builds cover different rules.
    offset = sum(ord(ch) for ch in seed) % len(pool)
    rotated = pool[offset:] + pool[:offset]
    return rotated[:limit]


def _resolve(host: str, timeout: float) -> str:
    previous = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    try:
        socket.getaddrinfo(host, None)
        return "ok"
    except socket.gaierror as exc:
        return "dead" if exc.errno in NXDOMAIN_ERRNOS else "unknown"
    except OSError:
        return "unknown"
    finally:
        socket.setdefaulttimeout(previous)


def check(
    items: list[tuple[str, Rule]], *, timeout: float = 3.0, workers: int = 8, retries: int = 1
) -> list[LivenessResult]:
    """Resolve each candidate; a domain is 'dead' only after repeated NXDOMAIN."""
    results: list[LivenessResult] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        statuses = list(pool.map(lambda item: _resolve(item[1].value, timeout), items))
    for (cid, rule), status in zip(items, statuses, strict=True):
        if status == "dead":
            for _ in range(retries):
                if _resolve(rule.value, timeout) != "dead":
                    status = "unknown"
                    break
        results.append(LivenessResult(rule=rule, category=cid, status=status))
    return results


def summarize(results: list[LivenessResult]) -> dict:
    dead = [r for r in results if r.status == "dead"]
    return {
        "checked": len(results),
        "dead": [
            {"category": r.category, "rule": str(r.rule)} for r in dead
        ],
    }
