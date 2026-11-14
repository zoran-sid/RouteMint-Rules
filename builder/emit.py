"""Client-specific serialisers and the CLI bridge to the mihomo/sing-box tools.

Only this module knows client syntax.  Everything upstream deals in ``Rule``.
Documentation links for each syntax are kept next to the code that emits it.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .model import Rule, RuleType


class EmitError(Exception):
    pass


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def _header(title: str, count: int) -> str:
    # Deliberately no timestamp: identical rule sets must produce byte-identical
    # files so CI can skip the release push when nothing changed.
    return (
        f"# RouteMint-Rules · {title}\n"
        f"# {count} rules\n"
        "# https://github.com/zoran-sid/RouteMint-Rules\n"
    )


def surge_list(rules: list[Rule], title: str) -> str:
    """Surge / Shadowrocket / Loon rule list.

    Surge: https://manual.nssurge.com/rules/domain.html
    Loon:  https://nsloon.app/en/docs/Rule/domain_rule/
    Rule lists carry no policy column; the policy is chosen by the config.
    """
    lines = [_header(title, len(rules)).rstrip("\n")]
    lines += [
        f"{rule},no-resolve" if rule.is_ip else str(rule)
        for rule in rules
    ]
    return "\n".join(lines) + "\n"


def quantumultx_list(rules: list[Rule], title: str) -> str:
    """Quantumult X remote filter.

    Grammar (official sample): ``host,`` / ``host-suffix,`` / ``host-keyword,``
    / ``ip-cidr,`` / ``ip6-cidr,`` with NO policy column — the policy is set by
    the ``[filter_remote]`` line that references this file.
    Docs: https://github.com/crossutility/Quantumult-X/blob/master/sample.conf
    """
    kind = {
        RuleType.DOMAIN: "host",
        RuleType.DOMAIN_SUFFIX: "host-suffix",
        RuleType.DOMAIN_KEYWORD: "host-keyword",
        RuleType.IP_CIDR: "ip-cidr",
        RuleType.IP_CIDR6: "ip6-cidr",
    }
    lines = [_header(title, len(rules)).rstrip("\n")]
    lines += [f"{kind[rule.type]}, {rule.value}" for rule in rules]
    return "\n".join(lines) + "\n"


def mihomo_domain_yaml(rules: list[Rule], title: str) -> str:
    """mihomo domain-behaviour rule-provider.

    Payload grammar: ``+.example.com`` = suffix, ``example.com`` = exact.
    Keyword rules cannot be expressed here and are inlined into the config.
    Docs: https://wiki.metacubex.one/en/config/rule-providers/
    """
    items: list[str] = []
    for rule in rules:
        if rule.type is RuleType.DOMAIN:
            items.append(rule.value)
        elif rule.type is RuleType.DOMAIN_SUFFIX:
            items.append(f"+.{rule.value}")
    body = "\n".join(f"  - {_dq(item)}" for item in items)
    return f"# {title} · {len(items)} rules\npayload:\n{body}\n"


def mihomo_ip_yaml(rules: list[Rule], title: str) -> str:
    items = [rule.value for rule in rules if rule.is_ip]
    body = "\n".join(f"  - {_dq(item)}" for item in items)
    return f"# {title} · {len(items)} rules\npayload:\n{body}\n"


def _dq(value: str) -> str:
    return '"' + value.replace('"', '\\"') + '"'


@dataclass(frozen=True)
class Converter:
    """Wraps ``mihomo convert-ruleset`` with a pinned binary."""

    binary: Path

    def to_mrs(self, behavior: str, source: Path, target: Path) -> None:
        cmd = [str(self.binary), "convert-ruleset", behavior, "yaml", str(source), str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0 or not target.is_file():
            raise EmitError(f"{' '.join(cmd)} failed: {result.stderr.strip()}")
        # mihomo prints "convert ... done" on success; keep the build log quiet.

    def test_config(self, config: Path) -> tuple[bool, str]:
        # A throwaway -d directory keeps mihomo from writing cache.db into dist/
        # (and from trying to create ~/.config/mihomo on CI).
        with tempfile.TemporaryDirectory(prefix="routemint-test-") as workdir:
            result = subprocess.run(
                [str(self.binary), "-t", "-d", workdir, "-f", str(config)],
                capture_output=True,
                text=True,
                check=False,
            )
        output = (result.stdout + result.stderr).strip()
        return result.returncode == 0, output


def validate_with_mihomo(binary: Path, configs: list[Path]) -> list[tuple[Path, bool, str]]:
    """Run ``mihomo -t`` against every config; returns per-file results."""
    converter = Converter(binary)
    return [(path, *converter.test_config(path)) for path in configs]


def test_singbox_config(binary: Path, config: Path) -> tuple[bool, str]:
    """``sing-box check`` validates structure only; it does not fetch rule-sets."""
    result = subprocess.run(
        [str(binary), "check", "-c", str(config)],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def validate_with_singbox(binary: Path, configs: list[Path]) -> list[tuple[Path, bool, str]]:
    """``sing-box check -c``; does not fetch remote rule-sets by design."""
    results = []
    for path in configs:
        result = subprocess.run(
            [str(binary), "check", "-c", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        results.append((path, result.returncode == 0, (result.stdout + result.stderr).strip()))
    return results


def singbox_source_json(rules: list[Rule]) -> dict:
    """sing-box source rule-set, schema version 5 (sing-box 1.14).

    Docs: https://sing-box.sagernet.org/configuration/rule-set/source-format/
    """
    domains = sorted({r.value for r in rules if r.type is RuleType.DOMAIN})
    suffixes = sorted({r.value for r in rules if r.type is RuleType.DOMAIN_SUFFIX})
    keywords = sorted({r.value for r in rules if r.type is RuleType.DOMAIN_KEYWORD})
    cidrs = sorted({r.value for r in rules if r.is_ip})
    headless: dict = {}
    if domains:
        headless["domain"] = domains
    if suffixes:
        headless["domain_suffix"] = suffixes
    if keywords:
        headless["domain_keyword"] = keywords
    rules_out: list[dict] = []
    if headless:
        rules_out.append(headless)
    if cidrs:
        rules_out.append({"ip_cidr": cidrs})
    return {"version": 5, "rules": rules_out}


def compile_srs(binary: Path, source: dict, target: Path) -> None:
    import json

    handle, name = tempfile.mkstemp(suffix=".json", prefix="routemint-srs-")
    tmp_json = Path(name)
    try:
        with open(handle, "w", encoding="utf-8") as stream:
            json.dump(source, stream, ensure_ascii=False)
        result = subprocess.run(
            [str(binary), "rule-set", "compile", "--output", str(target), str(tmp_json)],
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        tmp_json.unlink(missing_ok=True)
    if result.returncode != 0 or not target.is_file():
        raise EmitError(f"sing-box compile failed: {result.stderr.strip()}")


def require_binary(name: str, explicit: str | None) -> Path:
    candidate = explicit or shutil.which(name)
    if not candidate:
        raise EmitError(
            f"{name} binary not found. Install it or pass --{name}-bin. "
            "CI downloads the pinned release (see .github/workflows/build.yml)."
        )
    path = Path(candidate).resolve()
    if not path.is_file():
        raise EmitError(f"{name} binary not found at {path}")
    return path
