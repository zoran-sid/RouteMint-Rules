"""Upstream text -> normalised rules, one parser per declared format.

Every parser is tolerant: a malformed line is skipped and counted, never
raised, because upstream lists contain the occasional oddity and one bad line
must not block the daily build.  Format documentation lives next to each
parser and is linked from ``upstreams.yaml``.
"""

from __future__ import annotations

import ipaddress
import json
import re
from dataclasses import dataclass, field

from .model import Rule, RuleError, RuleType

# Hosts-file entries that are infrastructure, not routable domains.
_HOSTS_NOISE = {
    "localhost",
    "localhost.localdomain",
    "local",
    "broadcasthost",
    "ip6-localhost",
    "ip6-loopback",
    "ip6-localnet",
    "ip6-mcastprefix",
    "ip6-allnodes",
    "ip6-allrouters",
    "ip6-allhosts",
    "0.0.0.0",
}

_COMMENT_RE = re.compile(r"\s+#.*$")


@dataclass
class ParsedRule:
    rule: Rule
    attributes: frozenset[str] = frozenset()
    raw: str = ""


@dataclass
class ParsedDocument:
    rules: list[ParsedRule] = field(default_factory=list)
    includes: list[str] = field(default_factory=list)
    invalid: int = 0
    unsupported: list[str] = field(default_factory=list)


def _add(doc: ParsedDocument, rule_type: RuleType, value: str, attrs: set[str], raw: str) -> None:
    """Validate through ``Rule.parse`` so upstream junk cannot fake a rule."""
    try:
        if rule_type is RuleType.DOMAIN_KEYWORD:
            rule = Rule(rule_type, value.strip().lower())
        else:
            rule = Rule.parse(f"{rule_type},{value}")
        doc.rules.append(ParsedRule(rule=rule, attributes=frozenset(attrs), raw=raw))
    except (RuleError, ValueError):
        doc.invalid += 1


def parse_v2fly(text: str) -> ParsedDocument:
    """v2fly domain-list-community source format.

    Docs: https://github.com/v2fly/domain-list-community/tree/master/data
    Grammar (one entry per line):

        example.com            # suffix match (same as domain:)
        full:www.example.com   # exact match
        keyword:example        # substring match
        regexp:^ad[0-9]        # regular expression (not exported by us)
        include:another-list   # merge another data file
        full:example.com @cn   # trailing attributes, used for regional splits
    """
    doc = ParsedDocument()
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        tokens = line.split()
        value_token, attrs = tokens[0], {t[1:] for t in tokens[1:] if t.startswith("@")}
        if value_token.startswith("include:"):
            doc.includes.append(value_token.split(":", 1)[1].strip())
            continue
        if value_token.startswith("regexp:"):
            doc.unsupported.append(value_token)
            continue
        if ":" in value_token:
            prefix, value = value_token.split(":", 1)
        else:
            prefix, value = "domain", value_token
        kind = {
            "domain": RuleType.DOMAIN_SUFFIX,
            "full": RuleType.DOMAIN,
            "keyword": RuleType.DOMAIN_KEYWORD,
        }.get(prefix)
        if kind is None:
            doc.unsupported.append(value_token)
            continue
        if kind is RuleType.DOMAIN_KEYWORD:
            # Keywords are hand-curated only; upstream keywords are skipped and
            # reported so that the keyword budget stays meaningful.
            doc.unsupported.append(value_token)
            continue
        _add(doc, kind, value, attrs, raw_line.strip())
    return doc


def parse_hosts(text: str) -> ParsedDocument:
    """Hosts file (``0.0.0.0 domain``), e.g. StevenBlack/hosts."""
    doc = ParsedDocument()
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        fields = line.split()
        if len(fields) >= 2 and _looks_like_ip(fields[0]):
            domains = fields[1:]
        elif len(fields) == 1:
            domains = fields
        else:
            doc.invalid += 1
            continue
        for domain in domains:
            if domain.lower() in _HOSTS_NOISE:
                continue
            _add(doc, RuleType.DOMAIN_SUFFIX, domain, set(), raw_line.strip())
    return doc


def parse_domains(text: str) -> ParsedDocument:
    """Plain domain list, one domain per line (comments with ``#``)."""
    doc = ParsedDocument()
    for raw_line in text.splitlines():
        line = _COMMENT_RE.sub("", raw_line).strip()
        if not line:
            continue
        fields = line.split()
        domain = fields[1] if len(fields) >= 2 and _looks_like_ip(fields[0]) else fields[0]
        if domain.lower() in _HOSTS_NOISE:
            continue
        _add(doc, RuleType.DOMAIN_SUFFIX, domain, set(), raw_line.strip())
    return doc


def parse_apnic(text: str, country: str = "CN") -> ParsedDocument:
    """APNIC delegated stats (``registry|cc|type|start|value|date|status``).

    IPv4 ``value`` is an address *count*; IPv6 ``value`` is a prefix length.
    Docs: https://www.apnic.net/manage-ip/manage-ip-data/statistics/
    """
    doc = ParsedDocument()
    wanted = country.upper()
    for raw_line in text.splitlines():
        fields = raw_line.strip().split("|")
        if len(fields) < 7 or fields[1].upper() != wanted:
            continue
        kind, start, value, status = fields[2], fields[3], fields[4], fields[6]
        if status not in ("allocated", "assigned"):
            continue
        try:
            if kind == "ipv4":
                first = ipaddress.IPv4Address(start)
                last = ipaddress.IPv4Address(int(first) + int(value) - 1)
                nets = ipaddress.summarize_address_range(first, last)
            elif kind == "ipv6":
                nets = [ipaddress.ip_network(f"{start}/{value}", strict=False)]
            else:
                continue
        except (ValueError, ipaddress.AddressValueError):
            doc.invalid += 1
            continue
        for net in nets:
            doc.rules.append(
                ParsedRule(
                    rule=Rule(
                        RuleType.IP_CIDR if net.version == 4 else RuleType.IP_CIDR6, str(net)
                    ),
                    raw=raw_line.strip(),
                )
            )
    return doc


def _looks_like_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def parse_v2fly_dat(content: bytes) -> dict[str, "ParsedDocument"]:
    """Decode ``dlc.dat`` (GeoSiteList protobuf) into one document per category."""
    from .protobuf import parse_geosite_list

    result: dict[str, ParsedDocument] = {}
    for name, domains in parse_geosite_list(content).items():
        doc = ParsedDocument()
        for entry in domains:
            if entry.type == 1:  # regexp: deliberately not exported
                doc.unsupported.append(entry.value)
                continue
            rule_type = RuleType.DOMAIN if entry.type == 3 else RuleType.DOMAIN_SUFFIX
            _add(doc, rule_type, entry.value, set(entry.attributes), entry.value)
        result[name] = doc
    return result


def parse_cidr(text: str) -> ParsedDocument:
    """Bare CIDR list (one prefix per line), e.g. china-operator-ip."""
    doc = ParsedDocument()
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        try:
            net = ipaddress.ip_network(line, strict=False)
        except ValueError:
            doc.invalid += 1
            continue
        doc.rules.append(
            ParsedRule(
                rule=Rule(RuleType.IP_CIDR if net.version == 4 else RuleType.IP_CIDR6, str(net)),
                raw=raw_line.strip(),
            )
        )
    return doc


def parse_steam_cm(text: str) -> ParsedDocument:
    """Valve's public GetCMList endpoints, exported as exact public host IPs."""
    response = json.loads(text).get("response", {})
    endpoints = response.get("serverlist")
    if response.get("result") != 1 or not isinstance(endpoints, list):
        raise ValueError("Steam CM directory returned an invalid response")
    doc = ParsedDocument()
    for endpoint in endpoints:
        if not isinstance(endpoint, str):
            doc.invalid += 1
            continue
        host, separator, port = endpoint.rpartition(":")
        try:
            address = ipaddress.ip_address(host.strip("[]"))
            if not separator or not port.isdigit() or not 1 <= int(port) <= 65535 or not address.is_global:
                raise ValueError("not a public CM endpoint")
        except ValueError:
            doc.invalid += 1
            continue
        kind = RuleType.IP_CIDR if address.version == 4 else RuleType.IP_CIDR6
        _add(doc, kind, f"{address}/{address.max_prefixlen}", set(), endpoint)
    if not doc.rules:
        raise ValueError("Steam CM directory contains no public server addresses")
    return doc


PARSERS = {
    "steam-cm": parse_steam_cm,
    "v2fly": parse_v2fly,
    "hosts": parse_hosts,
    "domains": parse_domains,
    "apnic": parse_apnic,
    "cidr": parse_cidr,
}
