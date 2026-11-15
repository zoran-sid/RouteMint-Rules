"""Typed, validated views over the YAML that defines the repository.

Everything that can be wrong in a source file is checked here, with a message
that names the file and field, so ``pytest`` and CI can fail fast and humans
can fix the input instead of reading a stack trace.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .config import ConfigError, Paths, load_yaml
from .model import Rule, RuleError, RuleType

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_KNOWN_UPSTREAM_KEYS = {
    "title",
    "format",
    "url",
    "url_template",
    "ref",
    "license",
    "license_url",
    "homepage",
    "notice",
    "on_failure",
    "notes",
    "options",
}
_KNOWN_CATEGORY_KEYS = {"id", "meta", "include", "add", "remove", "compose", "drop_guard"}
_KNOWN_PRESET_KEYS = {
    "id",
    "label",
    "tagline",
    "audience",
    "summary",
    "order",
    "ads",
    "groups",
    "rules",
    "notes",
}

# The canonical order from README/design doc.  Presets may omit categories but
# must never reorder them: rule order is the routing contract.
CATEGORY_ORDER = [
    "private",
    "reject-malware",
    "reject-tracker",
    "reject-ads",
    "ai",
    "ai-openai",
    "ai-anthropic",
    "ai-gemini",
    "ai-copilot",
    "ai-perplexity",
    "ai-others",
    "netflix",
    "disney",
    "youtube",
    "spotify",
    "tiktok",
    "max",
    "primevideo",
    "streaming-others",
    "cn-region-locked",
    "dev",
    "game-download",
    "baidu-pan",
    "game-platform",
    "telegram",
    "apple",
    "microsoft",
    "google",
    "proxy",
    "cn",
    "cn-ip",
    "cn-ip6",
]

ADS_TIERS = {
    "ads-off": [],
    "ads-light": ["reject-ads", "reject-tracker"],
    "ads-strict": ["reject-ads", "reject-tracker", "reject-malware"],
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ConfigError(message)


def _as_list(value: object, where: str) -> list:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ConfigError(f"{where}: expected a list")
    return value


@dataclass(frozen=True)
class Upstream:
    id: str
    title: str
    format: str
    url: str | None
    url_template: str | None
    ref: str
    license: str
    license_url: str
    homepage: str
    notice: str = ""
    on_failure: str = "snapshot"
    options: dict = field(default_factory=dict)

    def url_for(self, category: str | None = None) -> str:
        if self.url_template:
            _require(category is not None, f"{self.id}: category required for url_template")
            return self.url_template.format(category=category, ref=self.ref)
        _require(self.url is not None, f"{self.id}: neither url nor url_template set")
        return self.url


@dataclass(frozen=True)
class Upstreams:
    upstreams: dict[str, Upstream]
    timeout_seconds: float
    retries: int
    cache_ttl_hours: float

    def get(self, upstream_id: str) -> Upstream:
        if upstream_id not in self.upstreams:
            raise ConfigError(f"unknown upstream {upstream_id!r}")
        return self.upstreams[upstream_id]


@dataclass(frozen=True)
class Include:
    upstream: str
    categories: tuple[str, ...] = ()
    exclude_attributes: tuple[str, ...] = ()


@dataclass
class CategorySpec:
    id: str
    path: Path
    description: str
    meta: dict
    includes: list[Include] = field(default_factory=list)
    add: list[Rule] = field(default_factory=list)
    keyword_reasons: dict[str, str] = field(default_factory=dict)
    removes: dict[str, str] = field(default_factory=dict)
    compose: tuple[str, ...] = ()
    drop_guard: bool = True


@dataclass(frozen=True)
class Group:
    name: str
    type: str
    members: tuple[str, ...]
    tag: str = ""
    use_providers: bool = False
    filter: str | None = None
    exclude_filter: str | None = None
    test_url: str = "https://www.gstatic.com/generate_204"
    interval: int = 300


@dataclass(frozen=True)
class RuleRef:
    category: str | None = None
    policy: str | None = None
    no_resolve: bool = False
    final: str | None = None


@dataclass(frozen=True)
class Preset:
    id: str
    label: str
    tagline: str
    audience: str
    summary: str
    order: int
    ads: str
    groups: tuple[Group, ...]
    rules: tuple[RuleRef, ...]
    notes: str = ""

    def active_categories(self) -> list[str]:
        return categories_for(self, self.ads)

    def policy_for(self, category: str) -> str | None:
        for ref in self.rules:
            if ref.category == category:
                return ref.policy
        return None


@dataclass(frozen=True)
class Budgets:
    default_category: int
    keyword_per_category: int
    drop_ratio: float
    categories: dict[str, int]
    presets: dict[str, int]
    files_kb: int
    repo_mb: int

    def category_limit(self, category: str) -> int:
        return self.categories.get(category, self.default_category)

    def preset_limit(self, preset: str) -> int:
        return self.presets.get(preset, 10**9)


def categories_for(preset: Preset, tier: str) -> list[str]:
    """Categories a preset actually emits for one ads tier, in canonical order."""
    enabled_ads = set(ADS_TIERS[tier])
    cats: list[str] = []
    for ref in preset.rules:
        if not ref.category:
            continue
        if ref.category.startswith("reject-") and ref.category not in enabled_ads:
            continue
        if ref.category not in cats:
            cats.append(ref.category)
    return cats


# --------------------------------------------------------------------------
# loaders
# --------------------------------------------------------------------------
def load_upstreams(paths: Paths) -> Upstreams:
    data = load_yaml(paths.upstreams)
    defaults = data.get("defaults") or {}
    entries = data.get("upstreams")
    _require(isinstance(entries, dict) and entries, f"{paths.upstreams}: missing 'upstreams'")

    upstreams: dict[str, Upstream] = {}
    for uid, raw in entries.items():
        where = f"upstreams.yaml:{uid}"
        _require(isinstance(raw, dict), f"{where}: must be a mapping")
        unknown = set(raw) - _KNOWN_UPSTREAM_KEYS
        _require(not unknown, f"{where}: unknown keys {sorted(unknown)}")
        for required in ("title", "format", "license"):
            _require(bool(raw.get(required)), f"{where}: missing {required}")
        _require(
            bool(raw.get("url")) ^ bool(raw.get("url_template")),
            f"{where}: set exactly one of url / url_template",
        )
        _require(raw["format"] in {"v2fly", "v2fly-dat", "hosts", "domains", "apnic", "cidr"}, f"{where}: bad format")
        upstreams[uid] = Upstream(
            id=uid,
            title=str(raw["title"]),
            format=str(raw["format"]),
            url=raw.get("url"),
            url_template=raw.get("url_template"),
            ref=str(raw.get("ref", "master")),
            license=str(raw["license"]),
            license_url=str(raw.get("license_url", "")),
            homepage=str(raw.get("homepage", "")),
            notice=str(raw.get("notice", "")),
            on_failure=str(raw.get("on_failure", "snapshot")),
            options=dict(raw.get("options") or {}),
        )
    return Upstreams(
        upstreams=upstreams,
        timeout_seconds=float(defaults.get("timeout_seconds", 30)),
        retries=int(defaults.get("retries", 2)),
        cache_ttl_hours=float(defaults.get("cache_ttl_hours", 24)),
    )


def load_category(path: Path) -> CategorySpec:
    data = load_yaml(path)
    where = f"sources/{path.name}"
    unknown = set(data) - _KNOWN_CATEGORY_KEYS
    _require(not unknown, f"{where}: unknown keys {sorted(unknown)}")
    category_id = str(data.get("id", ""))
    _require(bool(category_id), f"{where}: missing id")
    _require(_ID_RE.match(category_id) is not None, f"{where}: bad id {category_id!r}")
    _require(category_id == path.stem, f"{where}: id must equal file name ({path.stem})")
    meta = data.get("meta") or {}
    _require(isinstance(meta, dict), f"{where}: meta must be a mapping")
    _require(bool(meta.get("description")), f"{where}: meta.description is required")

    includes: list[Include] = []
    for entry in _as_list(data.get("include"), where):
        _require(isinstance(entry, dict), f"{where}: include items must be mappings")
        unknown = set(entry) - {"upstream", "categories", "exclude_attributes"}
        _require(not unknown, f"{where}: unknown include keys {sorted(unknown)}")
        _require(bool(entry.get("upstream")), f"{where}: include.upstream is required")
        includes.append(
            Include(
                upstream=str(entry["upstream"]),
                categories=tuple(str(c) for c in entry.get("categories", [])),
                exclude_attributes=tuple(str(a) for a in entry.get("exclude_attributes", [])),
            )
        )

    add: list[Rule] = []
    keyword_reasons: dict[str, str] = {}
    for entry in _as_list(data.get("add"), where):
        if isinstance(entry, str):
            text = entry
        elif isinstance(entry, dict):
            text = str(entry.get("rule", ""))
            reason = str(entry.get("reason", "")).strip()
            _require(bool(reason), f"{where}: add item {text!r} needs a reason")
        else:
            raise ConfigError(f"{where}: add items must be strings or mappings")
        try:
            rule = Rule.parse(text)
        except (RuleError, ValueError) as exc:
            raise ConfigError(f"{where}: bad rule {text!r}: {exc}") from exc
        if rule.type is RuleType.DOMAIN_KEYWORD:
            reason = entry.get("reason", "") if isinstance(entry, dict) else ""
            _require(
                bool(str(reason).strip()),
                f"{where}: DOMAIN-KEYWORD {rule.value!r} must document a reason",
            )
            keyword_reasons[rule.value] = str(reason).strip()
        add.append(rule)

    removes: dict[str, str] = {}
    for entry in _as_list(data.get("remove"), where):
        _require(isinstance(entry, dict), f"{where}: remove items must be mappings")
        unknown = set(entry) - {"value", "reason"}
        _require(not unknown, f"{where}: unknown remove keys {sorted(unknown)}")
        value = str(entry.get("value", "")).strip().lower().rstrip(".")
        reason = str(entry.get("reason", "")).strip()
        _require(bool(value), f"{where}: remove.value is required")
        _require(bool(reason), f"{where}: remove {value!r} needs a reason")
        removes[value] = reason

    compose = tuple(str(c) for c in _as_list(data.get("compose"), where))
    if compose:
        _require(
            not (includes or add or removes),
            f"{where}: a compose category cannot also include/add/remove rules",
        )
    else:
        _require(bool(includes or add), f"{where}: needs at least one include or add entry")

    return CategorySpec(
        id=category_id,
        path=path,
        description=str(meta["description"]),
        meta=meta,
        includes=includes,
        add=add,
        keyword_reasons=keyword_reasons,
        removes=removes,
        compose=compose,
        drop_guard=bool(data.get("drop_guard", True)),
    )


def load_categories(paths: Paths) -> dict[str, CategorySpec]:
    specs: dict[str, CategorySpec] = {}
    for path in sorted(paths.sources.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        spec = load_category(path)
        specs[spec.id] = spec
    _require(bool(specs), f"{paths.sources}: no category files found")
    return specs


def load_preset(path: Path, categories: dict[str, CategorySpec]) -> Preset:
    data = load_yaml(path)
    where = f"presets/{path.name}"
    unknown = set(data) - _KNOWN_PRESET_KEYS
    _require(not unknown, f"{where}: unknown keys {sorted(unknown)}")
    for required in ("id", "label", "summary", "groups", "rules"):
        _require(bool(data.get(required)), f"{where}: missing {required}")
    preset_id = str(data["id"])
    _require(preset_id == path.stem, f"{where}: id must equal file name")
    ads = str(data.get("ads", "ads-light"))
    _require(ads in ADS_TIERS, f"{where}: ads must be one of {sorted(ADS_TIERS)}")

    groups: list[Group] = []
    for raw in _as_list(data["groups"], where):
        _require(isinstance(raw, dict), f"{where}: groups must be mappings")
        unknown = set(raw) - {
            "name",
            "tag",
            "type",
            "members",
            "use_providers",
            "filter",
            "exclude_filter",
            "test_url",
            "interval",
        }
        _require(not unknown, f"{where}: unknown group keys {sorted(unknown)}")
        _require(bool(raw.get("name")), f"{where}: group name is required")
        gtype = str(raw.get("type", "select"))
        _require(
            gtype in {"select", "url-test", "fallback", "load-balance"},
            f"{where}: bad group type {gtype!r}",
        )
        groups.append(
            Group(
                name=str(raw["name"]),
                type=gtype,
                tag=str(raw.get("tag", "")),
                members=tuple(str(m) for m in raw.get("members", [])),
                use_providers=bool(raw.get("use_providers", False)),
                filter=raw.get("filter"),
                exclude_filter=raw.get("exclude_filter"),
                test_url=str(raw.get("test_url", "https://www.gstatic.com/generate_204")),
                interval=int(raw.get("interval", 300)),
            )
        )
    names = [g.name for g in groups]
    _require(len(names) == len(set(names)), f"{where}: duplicate group names")
    for group in groups:
        _require(
            group.use_providers or group.members,
            f"{where}: group {group.name!r} has neither members nor use_providers",
        )
        for member in group.members:
            _require(
                member in names or member in {"DIRECT", "REJECT"},
                f"{where}: group {group.name!r} references unknown policy {member!r}",
            )

    rules: list[RuleRef] = []
    for raw in _as_list(data["rules"], where):
        _require(isinstance(raw, dict), f"{where}: rules must be mappings")
        if "final" in raw:
            _require(raw["final"] in names, f"{where}: final policy {raw['final']!r} is not a group")
            rules.append(RuleRef(final=str(raw["final"])))
            continue
        category = str(raw.get("category", ""))
        _require(category in categories, f"{where}: unknown category {category!r}")
        policy = raw.get("policy")
        _require(policy is not None, f"{where}: rule for {category!r} needs a policy")
        _require(
            policy in names or policy in {"DIRECT", "REJECT"}, f"{where}: unknown policy {policy!r}"
        )
        rules.append(
            RuleRef(category=category, policy=str(policy), no_resolve=bool(raw.get("no_resolve")))
        )
    _require(rules and rules[-1].final, f"{where}: last rule must be 'final'")
    _require(
        all(r.final is None for r in rules[:-1]), f"{where}: 'final' may only appear once, last"
    )

    referenced = [r.category for r in rules if r.category]
    _require(len(referenced) == len(set(referenced)), f"{where}: category listed twice")
    expected = [c for c in CATEGORY_ORDER if c in referenced]
    expected += [c for c in referenced if c not in CATEGORY_ORDER]
    _require(expected == referenced, f"{where}: categories must follow canonical order {CATEGORY_ORDER}")

    return Preset(
        id=preset_id,
        label=str(data["label"]),
        tagline=str(data.get("tagline", "")),
        audience=str(data.get("audience", "")),
        summary=str(data["summary"]),
        order=int(data.get("order", 100)),
        ads=ads,
        groups=tuple(groups),
        rules=tuple(rules),
        notes=str(data.get("notes", "")),
    )


def load_presets(paths: Paths, categories: dict[str, CategorySpec]) -> list[Preset]:
    presets = [
        load_preset(p, categories)
        for p in sorted(paths.presets.glob("*.yaml"))
        if not p.name.startswith("_")
    ]
    _require(bool(presets), f"{paths.presets}: no presets found")
    return sorted(presets, key=lambda p: (p.order, p.id))


def load_budgets(paths: Paths) -> Budgets:
    data = load_yaml(paths.budgets)
    defaults = data.get("defaults") or {}
    return Budgets(
        default_category=int(defaults.get("category_rules", 20000)),
        keyword_per_category=int(defaults.get("keyword_rules", 3)),
        drop_ratio=float(defaults.get("drop_ratio", 0.30)),
        categories={k: int(v) for k, v in (data.get("categories") or {}).items()},
        presets={k: int(v) for k, v in (data.get("presets") or {}).items()},
        files_kb=int((data.get("distribution") or {}).get("file_kb", 20000)),
        repo_mb=int((data.get("distribution") or {}).get("repo_mb", 500)),
    )
