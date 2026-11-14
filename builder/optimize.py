"""Rule-set optimisation and cross-category conflict arbitration.

Order matters: dedupe -> suffix prune -> IP collapse -> removals -> conflict
resolution.  Every drop that changes routing semantics is recorded so the build
report can explain it.
"""

from __future__ import annotations

import ipaddress
from collections import defaultdict
from dataclasses import dataclass, field

from .model import Rule, RuleType


@dataclass
class ConflictDecision:
    category: str
    winner: str
    rule: Rule
    reason: str


@dataclass
class OptimizationStats:
    input_rules: int = 0
    duplicates: int = 0
    shadowed: int = 0
    ip_merged: int = 0
    removed: int = 0
    conflicts: int = 0
    decisions: list[ConflictDecision] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "input_rules": self.input_rules,
            "duplicates": self.duplicates,
            "shadowed_by_suffix": self.shadowed,
            "ip_merged": self.ip_merged,
            "removed": self.removed,
            "cross_category_conflicts": self.conflicts,
        }


def dedupe(rules: list[Rule]) -> tuple[list[Rule], int]:
    seen: set[Rule] = set()
    out: list[Rule] = []
    for rule in rules:
        if rule in seen:
            continue
        seen.add(rule)
        out.append(rule)
    return out, len(rules) - len(out)


def prune_shadowed_domains(rules: list[Rule]) -> tuple[list[Rule], int]:
    """Drop ``a.example.com`` when ``example.com`` is already a suffix rule."""
    domains = [r for r in rules if r.type.is_domain and r.type is not RuleType.DOMAIN_KEYWORD]
    suffixes = {r.value for r in rules if r.type is RuleType.DOMAIN_SUFFIX}
    keywords = [r for r in rules if r.type is RuleType.DOMAIN_KEYWORD]
    others = [r for r in rules if r.is_ip]
    kept: list[Rule] = []
    dropped = 0
    for rule in domains:
        labels = rule.value.split(".")
        # Include the TLD itself: a suffix rule "cn" really does cover "x.cn".
        covered = any(".".join(labels[i:]) in suffixes for i in range(1, len(labels)))
        if covered:
            dropped += 1
            continue
        kept.append(rule)
    kept.sort()
    return kept + sorted(keywords) + sorted(others), dropped


def collapse_ips(rules: list[Rule]) -> tuple[list[Rule], int]:
    out: list[Rule] = [r for r in rules if not r.is_ip]
    merged = 0
    for rule_type in (RuleType.IP_CIDR, RuleType.IP_CIDR6):
        nets = [ipaddress.ip_network(r.value) for r in rules if r.type is rule_type]
        collapsed = list(ipaddress.collapse_addresses(nets))
        merged += len(nets) - len(collapsed)
        out.extend(Rule(rule_type, str(net)) for net in collapsed)
    out.sort()
    return out, merged


def apply_removals(rules: list[Rule], removes: dict[str, str]) -> tuple[list[Rule], int]:
    if not removes:
        return rules, 0
    kept = [r for r in rules if r.value not in removes]
    return kept, len(rules) - len(kept)


def _supernets(net: ipaddress._BaseNetwork):
    for prefix in range(net.prefixlen, -1, -1):
        yield ipaddress.ip_network((net.network_address, prefix), strict=False)


def resolve_conflicts(
    per_category: dict[str, list[Rule]],
    precedence: list[str],
    allowed_winners: dict[str, set[str]] | None = None,
) -> tuple[dict[str, list[Rule]], OptimizationStats]:
    """Higher-precedence categories win; losers are dropped and recorded.

    A rule loses only when it is *fully* covered by a higher-precedence rule:
    a suffix beneath a winning suffix, an exact domain matched by a winning
    suffix/exact rule, or an IP network inside a winning network.  Partial
    overlaps stay in place because dropping them would lose coverage.
    """
    rank = {c: i for i, c in enumerate(precedence)}
    ordered = sorted(per_category, key=lambda c: (rank.get(c, len(rank)), c))

    suffix_owner: dict[str, str] = {}
    exact_owner: dict[str, str] = {}
    keyword_owner: dict[str, str] = {}
    net_owner: dict[int, dict[ipaddress._BaseNetwork, str]] = {4: {}, 6: {}}
    stats = OptimizationStats()

    resolved: dict[str, list[Rule]] = {}
    for category in ordered:
        kept: list[Rule] = []
        for rule in per_category[category]:
            winner: str | None = None
            reason = ""
            if rule.type is RuleType.DOMAIN:
                winner = exact_owner.get(rule.value)
                reason = "exact domain already owned"
                for candidate in rule.suffix_candidates():
                    if candidate in suffix_owner:
                        winner, reason = suffix_owner[candidate], f"covered by suffix {candidate}"
                        break
            elif rule.type is RuleType.DOMAIN_SUFFIX:
                for candidate in rule.suffix_candidates():
                    if candidate in suffix_owner:
                        winner, reason = suffix_owner[candidate], f"covered by suffix {candidate}"
                        break
            elif rule.type is RuleType.DOMAIN_KEYWORD:
                winner = keyword_owner.get(rule.value)
                reason = "keyword already owned"
            else:
                net = ipaddress.ip_network(rule.value)
                owners = net_owner[net.version]
                for supernet in _supernets(net):
                    if supernet in owners:
                        winner, reason = owners[supernet], f"inside {supernet}"
                        break

            if winner is not None and allowed_winners is not None:
                if winner not in allowed_winners.get(category, set()):
                    winner = None
            if winner is not None:
                stats.conflicts += 1
                if len(stats.decisions) < 200:
                    stats.decisions.append(
                        ConflictDecision(category=category, winner=winner, rule=rule, reason=reason)
                    )
                continue

            kept.append(rule)
            if rule.type is RuleType.DOMAIN:
                exact_owner[rule.value] = category
            elif rule.type is RuleType.DOMAIN_SUFFIX:
                suffix_owner[rule.value] = category
            elif rule.type is RuleType.DOMAIN_KEYWORD:
                keyword_owner[rule.value] = category
            else:
                net_owner[ipaddress.ip_network(rule.value).version][
                    ipaddress.ip_network(rule.value)
                ] = category
        resolved[category] = kept
    return resolved, stats


def category_stats(rules: list[Rule]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for rule in rules:
        counts[rule.type.value] += 1
    counts["total"] = len(rules)
    return dict(counts)
