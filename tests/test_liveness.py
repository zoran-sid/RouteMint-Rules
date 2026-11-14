from __future__ import annotations

from pathlib import Path

import pytest

from builder import liveness
from builder.model import Rule
from builder.spec import CategorySpec


def _spec(cid: str, values: list[str]) -> CategorySpec:
    return CategorySpec(
        id=cid,
        path=Path(f"{cid}.yaml"),
        description=cid,
        meta={"description": cid},
        add=[Rule.parse(f"DOMAIN-SUFFIX,{v}") for v in values],
    )


def test_candidates_rotate_and_skip_ip_rules():
    specs = {"a": _spec("a", [f"d{i}.test" for i in range(5)])}
    first = liveness.candidates(specs, 3, seed="2026-11-14")
    second = liveness.candidates(specs, 3, seed="2026-11-15")
    assert len(first) == 3
    assert first != second  # rotation covers different rules on consecutive days


def test_candidates_ignore_ip_and_local():
    specs = {
        "p": CategorySpec(
            id="p",
            path=Path("p.yaml"),
            description="p",
            meta={"description": "p"},
            add=[Rule.parse("IP-CIDR,10.0.0.0/8"), Rule.parse("DOMAIN-SUFFIX,printer.local")],
        )
    }
    assert liveness.candidates(specs, 10, seed="x") == []


def test_check_marks_repeated_nxdomain(monkeypatch):
    calls: dict[str, int] = {}

    def fake_resolve(host: str, timeout: float) -> str:
        calls[host] = calls.get(host, 0) + 1
        return "dead" if host.startswith("dead") else "ok"

    monkeypatch.setattr(liveness, "_resolve", fake_resolve)
    items = [
        ("a", Rule.parse("DOMAIN-SUFFIX,alive.test")),
        ("a", Rule.parse("DOMAIN-SUFFIX,dead.test")),
    ]
    results = liveness.check(items, retries=1)
    assert [r.status for r in results] == ["ok", "dead"]
    assert calls["dead.test"] == 2  # a single NXDOMAIN is not enough


def test_summary_shape():
    results = [
        liveness.LivenessResult(Rule.parse("DOMAIN-SUFFIX,x.test"), "a", "dead"),
        liveness.LivenessResult(Rule.parse("DOMAIN-SUFFIX,y.test"), "a", "ok"),
    ]
    summary = liveness.summarize(results)
    assert summary["checked"] == 2
    assert summary["dead"] == [{"category": "a", "rule": "DOMAIN-SUFFIX,x.test"}]
