"""Build orchestration: sources -> rules -> dist.

The pipeline is intentionally linear and boring:

    resolve -> normalise -> optimise -> arbitrate -> budget -> emit -> render
    -> report

Each step returns data instead of mutating globals, so tests can call a single
stage without building the world.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from . import emit
from .config import ConfigError, Paths, load_yaml
from .fetch import FetchError, Fetcher
from .model import Rule, RuleType
from .optimize import (
    ConflictDecision,
    OptimizationStats,
    collapse_ips,
    dedupe,
    prune_shadowed_domains,
    resolve_conflicts,
)
from .render import render_client_configs
from .report import (
    update_readme_table,
    write_changelog,
    write_manifest,
    write_notices,
    write_report,
)
from .resolve import ResolvedCategory, Resolver
from .spec import (
    ADS_TIERS,
    CategorySpec,
    Preset,
    load_budgets,
    load_categories,
    load_presets,
    load_upstreams,
)


class BuildError(Exception):
    pass


@dataclass
class CategoryBuild:
    spec: CategorySpec
    rules: list[Rule]
    resolved: ResolvedCategory
    stats: OptimizationStats = field(default_factory=OptimizationStats)

    @property
    def domain_rules(self) -> list[Rule]:
        return [r for r in self.rules if r.type in (RuleType.DOMAIN, RuleType.DOMAIN_SUFFIX)]

    @property
    def ip_rules(self) -> list[Rule]:
        return [r for r in self.rules if r.is_ip]

    @property
    def keyword_rules(self) -> list[Rule]:
        return [r for r in self.rules if r.type is RuleType.DOMAIN_KEYWORD]

    @property
    def counts(self) -> dict[str, int]:
        return {
            "domain": len(self.domain_rules),
            "ip": len(self.ip_rules),
            "keyword": len(self.keyword_rules),
            "total": len(self.rules),
        }


@dataclass
class BuildResult:
    categories: dict[str, CategoryBuild]
    presets: list[Preset]
    manifest: dict
    dist: Path
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    config_checks: list[dict] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.violations


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _used_categories(presets: list[Preset], categories: dict[str, CategorySpec]) -> set[str]:
    used = set(categories)
    for preset in presets:
        used.update(ref.category for ref in preset.rules if ref.category)
    return used


def optimize_category(build: CategoryBuild) -> list[Rule]:
    rules = list(build.rules)
    stats = build.stats
    stats.input_rules = len(rules)
    rules, stats.duplicates = dedupe(rules)
    rules, stats.shadowed = prune_shadowed_domains(rules)
    rules, stats.ip_merged = collapse_ips(rules)
    return rules


def load_previous_manifest(path: Path | None) -> dict | None:
    if path is None or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def build(
    paths: Paths,
    *,
    refresh: bool = False,
    offline: bool = False,
    mihomo_bin: Path | None = None,
    validate: bool = False,
    previous_manifest: Path | None = None,
    previous_dist: Path | None = None,
    allow_drop: bool = False,
) -> BuildResult:
    upstreams = load_upstreams(paths)
    budgets = load_budgets(paths)
    categories = load_categories(paths)
    defaults = load_yaml(paths.presets / "_defaults.yaml")
    presets = load_presets(paths, categories)
    precedence = [str(c) for c in defaults.get("precedence", [])]
    if not precedence:
        raise BuildError("presets/_defaults.yaml: precedence list is required")

    for preset in presets:
        for ref in preset.rules:
            if ref.category and ref.category not in categories:
                raise BuildError(f"preset {preset.id}: unknown category {ref.category}")

    buildable = {cid for cid, spec in categories.items() if not spec.compose}
    for cid, spec in categories.items():
        for member in spec.compose:
            if member not in buildable:
                raise BuildError(f"{cid}: compose member {member!r} is unknown or itself composed")

    paths.dist.mkdir(parents=True, exist_ok=True)
    fetcher = Fetcher(
        paths.cache,
        timeout=upstreams.timeout_seconds,
        retries=upstreams.retries,
        ttl_hours=upstreams.cache_ttl_hours,
        offline=offline,
        refresh=refresh,
    )
    resolver = Resolver(upstreams, fetcher)

    builds: dict[str, CategoryBuild] = {}
    try:
        for cid in sorted(buildable):
            resolved = resolver.resolve(categories[cid])
            builds[cid] = CategoryBuild(spec=categories[cid], rules=resolved.rules, resolved=resolved)
    except FetchError as exc:
        raise BuildError(str(exc)) from exc
    finally:
        fetcher.close()

    for build_item in builds.values():
        build_item.rules = optimize_category(build_item)

    ordered = [c for c in precedence if c in builds]
    ordered += [c for c in builds if c not in ordered]
    arbitrated, conflict_stats = resolve_conflicts(
        {cid: builds[cid].rules for cid in ordered}, ordered
    )
    for cid, rules in arbitrated.items():
        builds[cid].rules = rules
        builds[cid].stats.conflicts = sum(
            1 for d in conflict_stats.decisions if d.category == cid
        )

    # Composed categories are built from already-arbitrated members, so they
    # can never change another category's routing.
    for cid, spec in categories.items():
        if not spec.compose:
            continue
        merged: list[Rule] = []
        for member in spec.compose:
            merged.extend(builds[member].rules)
        merged, dups = dedupe(merged)
        merged, shadowed = prune_shadowed_domains(merged)
        merged, merged_ips = collapse_ips(merged)
        stats = OptimizationStats(
            input_rules=len(merged), duplicates=dups, shadowed=shadowed, ip_merged=merged_ips
        )
        builds[cid] = CategoryBuild(
            spec=spec,
            rules=merged,
            resolved=ResolvedCategory(spec=spec),
            stats=stats,
        )

    violations: list[str] = []
    warnings: list[str] = []
    for cid, item in sorted(builds.items()):
        limit = budgets.category_limit(cid)
        if item.counts["total"] > limit:
            violations.append(
                f"category {cid}: {item.counts['total']} rules exceeds budget {limit}"
            )
        if item.counts["keyword"] > budgets.keyword_per_category:
            violations.append(
                f"category {cid}: {item.counts['keyword']} keyword rules exceeds budget "
                f"{budgets.keyword_per_category}"
            )
        if item.resolved.invalid:
            warnings.append(f"{cid}: {item.resolved.invalid} lines skipped as invalid")
        if item.resolved.unsupported:
            warnings.append(
                f"{cid}: {item.resolved.unsupported} upstream entries unsupported (regexp/keyword)"
            )
        for missing in item.resolved.missing:
            warnings.append(f"{cid}: upstream category {missing!r} not found")
        if item.resolved.degraded:
            warnings.append(f"{cid}: an upstream was stale, previous snapshot was reused")

    previous = load_previous_manifest(previous_manifest)
    drop_ratio = budgets.drop_ratio
    if previous and not allow_drop:
        for cid, item in builds.items():
            if not item.spec.drop_guard:
                continue
            before = (previous.get("categories", {}).get(cid) or {}).get("total", 0)
            after = item.counts["total"]
            if before >= 50 and after < before * (1 - drop_ratio):
                violations.append(
                    f"category {cid}: {before} -> {after} rules "
                    f"(-{(1 - after / before):.0%}) exceeds drop guard {drop_ratio:.0%}"
                )

    for preset in presets:
        for tier in ADS_TIERS:
            total = preset_total(builds, preset, tier)
            limit = budgets.preset_limit(preset.id)
            if total > limit:
                violations.append(
                    f"preset {preset.id} ({tier}): {total} rules exceeds budget {limit}"
                )
            else:
                warnings.append(f"preset {preset.id} ({tier}): {total} rules")

    generated_at = _now().isoformat(timespec="seconds")
    urls = load_distribution(paths)
    artifacts = write_rule_artifacts(
        paths, builds, urls, mihomo_bin, violations, warnings, budgets.files_kb
    )
    config_checks = render_client_configs(
        paths, presets, builds, urls, generated_at, mihomo_bin=mihomo_bin
    )
    if validate and mihomo_bin is None:
        violations.append("--validate requested but no mihomo binary was provided")

    manifest = {
        "schema": 1,
        "generated_at": generated_at,
        "categories": {
            cid: {**item.counts, "degraded": item.resolved.degraded}
            for cid, item in sorted(builds.items())
        },
        "presets": {
            preset.id: {
                "tier": preset.ads,
                "rules": {tier: preset_total(builds, preset, tier) for tier in ADS_TIERS},
                "configs": {
                    client: f"configs/{preset.id}/{preset.ads}/{client}"
                    for client in ("mihomo.yaml", "shadowrocket.conf")
                },
            }
            for preset in presets
        },
        "artifacts": artifacts,
        "upstreams": [
            {
                "id": upstream.id,
                "title": upstream.title,
                "license": upstream.license,
                "url": upstream.url or upstream.url_template,
            }
            for upstream in upstreams.upstreams.values()
        ],
    }

    write_manifest(paths.dist / "manifest.json", manifest)
    write_notices(paths.root / "THIRD_PARTY_NOTICES.md", upstreams.upstreams, urls["source_url"])
    update_readme_table(paths.root / "README.md", builds)
    write_report(
        paths.dist / "build-report.md",
        builds=builds,
        presets=presets,
        budgets=budgets,
        fetcher_stats={},
        conflicts=conflict_stats,
        violations=violations,
        warnings=warnings,
        previous=previous,
        config_checks=config_checks,
        generated_at=generated_at,
    )
    write_changelog(
        paths.root / "CHANGELOG.md",
        builds=builds,
        previous=previous,
        previous_dist=previous_dist,
        generated_at=generated_at,
        presets=presets,
    )

    result = BuildResult(
        categories=builds,
        presets=presets,
        manifest=manifest,
        dist=paths.dist,
        violations=violations,
        warnings=warnings,
        config_checks=config_checks,
    )
    return result


def preset_categories(preset: Preset, tier: str) -> list[str]:
    enabled_ads = set(ADS_TIERS[tier])
    cats = []
    for ref in preset.rules:
        if not ref.category:
            continue
        if ref.category.startswith("reject-") and ref.category not in enabled_ads:
            continue
        cats.append(ref.category)
    return cats


def preset_total(builds: dict[str, CategoryBuild], preset: Preset, tier: str) -> int:
    return sum(builds[cid].counts["total"] for cid in preset_categories(preset, tier))


def load_distribution(paths: Paths) -> dict:
    data = load_yaml(paths.root / "repo.yaml")
    github = data.get("github") or {}
    if not github.get("owner") or not github.get("repo"):
        raise ConfigError("repo.yaml: github.owner and github.repo are required")
    base = f"https://cdn.jsdelivr.net/gh/{github['owner']}/{github['repo']}"
    return {
        "owner": github["owner"],
        "repo": github["repo"],
        "branch": github.get("release_branch", "release"),
        "jsdelivr": base,
        "raw": f"https://raw.githubusercontent.com/{github['owner']}/{github['repo']}",
        "source_url": f"https://github.com/{github['owner']}/{github['repo']}",
    }


def write_rule_artifacts(
    paths: Paths,
    builds: dict[str, CategoryBuild],
    urls: dict,
    mihomo_bin: Path | None,
    violations: list[str],
    warnings: list[str],
    file_limit_kb: int = 20480,
) -> dict:
    artifacts: dict[str, dict] = {}
    converter = emit.Converter(mihomo_bin) if mihomo_bin else None
    for cid, item in sorted(builds.items()):
        title = item.spec.description
        folder = paths.dist / "rules" / cid
        files: dict[str, str] = {}
        if item.rules:
            path = folder / f"{cid}.list"
            emit.write_text(path, emit.surge_list(item.rules, title))
            files["surge"] = f"rules/{cid}/{cid}.list"
        if item.domain_rules:
            path = folder / f"{cid}.yaml"
            emit.write_text(path, emit.mihomo_domain_yaml(item.domain_rules, title))
            files["mihomo_domain"] = f"rules/{cid}/{cid}.yaml"
            if converter:
                mrs = folder / f"{cid}.mrs"
                converter.to_mrs("domain", path, mrs)
                files["mihomo_domain_mrs"] = f"rules/{cid}/{cid}.mrs"
        if item.ip_rules:
            suffix = "-ip" if item.domain_rules else ""
            path = folder / f"{cid}{suffix}.yaml"
            emit.write_text(path, emit.mihomo_ip_yaml(item.ip_rules, title))
            files["mihomo_ip"] = f"rules/{cid}/{cid}{suffix}.yaml"
            if converter:
                mrs = folder / f"{cid}{suffix}.mrs"
                converter.to_mrs("ipcidr", path, mrs)
                files["mihomo_ip_mrs"] = f"rules/{cid}/{cid}{suffix}.mrs"
        artifacts[cid] = {
            "files": files,
            "jsdelivr": {k: f"{urls['jsdelivr']}@{urls['branch']}/{v}" for k, v in files.items()},
        }
        for rel in files.values():
            _check_file_size(paths.dist / rel, violations, file_limit_kb)
    return artifacts


def _check_file_size(path: Path, violations: list[str], limit_kb: int) -> None:
    size_kb = path.stat().st_size / 1024
    if size_kb > limit_kb:
        violations.append(f"{path.name}: {size_kb:.0f} KB exceeds jsDelivr file limit {limit_kb} KB")


def clean_dist(paths: Paths) -> None:
    for folder in ("rules", "configs"):
        target = paths.dist / folder
        if target.exists():
            shutil.rmtree(target)
