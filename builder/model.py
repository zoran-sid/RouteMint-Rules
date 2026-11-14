"""Core rule model: one normalised rule, one canonical string form.

The whole build pipeline speaks in ``Rule`` objects.  Every writer converts a
``Rule`` into its client syntax at the very last moment, so the same rule can
never mean two different things in two different outputs.
"""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from enum import StrEnum

_LABEL_RE = re.compile(r"^[a-z0-9_](?:[a-z0-9_-]{0,61}[a-z0-9_])?$")


class RuleType(StrEnum):
    DOMAIN = "DOMAIN"
    DOMAIN_SUFFIX = "DOMAIN-SUFFIX"
    DOMAIN_KEYWORD = "DOMAIN-KEYWORD"
    IP_CIDR = "IP-CIDR"
    IP_CIDR6 = "IP-CIDR6"

    @property
    def is_domain(self) -> bool:
        return self in (RuleType.DOMAIN, RuleType.DOMAIN_SUFFIX, RuleType.DOMAIN_KEYWORD)

    @property
    def is_ip(self) -> bool:
        return self in (RuleType.IP_CIDR, RuleType.IP_CIDR6)


class RuleError(ValueError):
    """Raised when a rule cannot be parsed or normalised."""


def normalize_domain(value: str, *, allow_tld: bool = False) -> str:
    """Lowercase, strip a trailing dot, IDNA-encode and validate a domain.

    ``*.example.com`` written by some upstreams is treated as a suffix.
    ``allow_tld`` permits single-label values such as ``cn`` for suffix rules.
    """
    domain = value.strip().lower().strip(".")
    if domain.startswith("*."):
        domain = domain[2:]
    if not domain or len(domain) > 253 or ("." not in domain and not allow_tld):
        raise RuleError(f"not a valid domain: {value!r}")
    try:
        domain = domain.encode("idna").decode("ascii")
    except UnicodeError as exc:  # pragma: no cover - exotic input
        raise RuleError(f"cannot IDNA-encode {value!r}: {exc}") from exc
    for label in domain.split("."):
        if not _LABEL_RE.match(label):
            raise RuleError(f"invalid label {label!r} in {value!r}")
    return domain


def normalize_ip_cidr(value: str) -> str:
    try:
        network = ipaddress.ip_network(value.strip(), strict=False)
    except ValueError as exc:
        raise RuleError(f"not a valid CIDR: {value!r}") from exc
    return str(network)


@dataclass(frozen=True, order=True, slots=True)
class Rule:
    type: RuleType
    value: str

    def __str__(self) -> str:
        return f"{self.type},{self.value}"

    @classmethod
    def parse(cls, text: str) -> "Rule":
        """Parse ``TYPE,value`` (whitespace tolerated, params ignored)."""
        parts = [p.strip() for p in str(text).split(",")]
        if len(parts) < 2 or not parts[0]:
            raise RuleError(f"expected 'TYPE,value': {text!r}")
        raw_type = parts[0].upper()
        # Upstream lists occasionally carry trailing parameters (no-resolve).
        value = parts[1]
        try:
            rule_type = RuleType(raw_type)
        except ValueError as exc:
            raise RuleError(f"unsupported rule type {raw_type!r}") from exc
        if rule_type.is_domain:
            # Single-label hosts are legitimate: "localhost", TLD-wide "cn".
            return cls(rule_type, normalize_domain(value, allow_tld=True))
        expected = 4 if rule_type is RuleType.IP_CIDR else 6
        network = ipaddress.ip_network(normalize_ip_cidr(value))
        if network.version != expected:
            raise RuleError(f"{rule_type} expects IPv{expected}, got {value!r}")
        return cls(rule_type, str(network))

    @property
    def is_ip(self) -> bool:
        return self.type.is_ip

    def suffix_candidates(self) -> list[str]:
        """All suffixes of a domain rule, longest first (itself included)."""
        if not self.type.is_domain:
            return []
        labels = self.value.split(".")
        return [".".join(labels[i:]) for i in range(len(labels) - 1)]

    def matches_domain(self, domain: str) -> bool:
        domain = normalize_domain(domain) if not domain.endswith(".") else domain.lower().rstrip(".")
        if self.type is RuleType.DOMAIN:
            return domain == self.value
        if self.type is RuleType.DOMAIN_SUFFIX:
            return domain == self.value or domain.endswith("." + self.value)
        if self.type is RuleType.DOMAIN_KEYWORD:
            return self.value in domain
        return False

    def matches_ip(self, ip: str) -> bool:
        if not self.type.is_ip:
            return False
        return ipaddress.ip_address(ip) in ipaddress.ip_network(self.value)


def parse_rules(texts: list[str]) -> list[Rule]:
    return [Rule.parse(t) for t in texts]
