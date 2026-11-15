from __future__ import annotations

from builder.model import RuleType
from builder.parse import (
    parse_apnic,
    parse_cidr,
    parse_domains,
    parse_hosts,
    parse_v2fly,
    parse_v2fly_dat,
)
from builder.protobuf import read_varint


def test_v2fly_grammar():
    text = """
# comment
example.com
full:www.example.com
keyword:tracker
regexp:^ad[0-9]+\\.example\\.net$
include:another-list
full:cn.example.com @cn @ads
"""
    doc = parse_v2fly(text)
    assert [str(r.rule) for r in doc.rules] == [
        "DOMAIN-SUFFIX,example.com",
        "DOMAIN,www.example.com",
        "DOMAIN,cn.example.com",
    ]
    assert doc.includes == ["another-list"]
    assert len(doc.unsupported) == 2  # keyword + regexp are not exported
    assert doc.rules[-1].attributes == {"cn", "ads"}


def test_hosts_grammar_skips_noise():
    text = """
# header
0.0.0.0 ads.example.com
127.0.0.1 localhost
0.0.0.0 tracker.example.net # trailing
"""
    doc = parse_hosts(text)
    assert [str(r.rule) for r in doc.rules] == [
        "DOMAIN-SUFFIX,ads.example.com",
        "DOMAIN-SUFFIX,tracker.example.net",
    ]


def test_plain_domain_list_ignores_bang_comments():
    text = "! Updated: now\nads.example.com\n# hash\n"
    doc = parse_domains(text)
    assert [str(r.rule) for r in doc.rules] == ["DOMAIN-SUFFIX,ads.example.com"]


def test_apnic_ipv4_count_becomes_prefixes():
    text = "apnic|CN|ipv4|1.0.1.0|256|20110414|allocated\napnic|CN|ipv4|1.0.2.0|512|20110414|allocated\n"
    doc = parse_apnic(text)
    assert [r.rule.value for r in doc.rules] == ["1.0.1.0/24", "1.0.2.0/23"]


def test_apnic_ipv6_uses_prefix_length():
    text = "apnic|CN|ipv6|2001:250::|35|20000426|allocated\napnic|JP|ipv6|2001:200::|35|20000426|allocated\n"
    doc = parse_apnic(text)
    assert [r.rule.value for r in doc.rules] == ["2001:250::/35"]


def test_apnic_ignores_unallocated():
    text = "apnic|CN|ipv4|1.0.1.0|256|20110414|reserved\n"
    assert parse_apnic(text).rules == []


def test_cidr_list():
    doc = parse_cidr("1.0.1.0/24\n2001:db8::/32\nbroken\n")
    assert [r.rule.type for r in doc.rules] == [RuleType.IP_CIDR, RuleType.IP_CIDR6]
    assert doc.invalid == 1


# -- protobuf ---------------------------------------------------------------
def _varint(value: int) -> bytes:
    out = bytearray()
    while True:
        bits = value & 0x7F
        value >>= 7
        if value:
            out.append(bits | 0x80)
        else:
            out.append(bits)
            return bytes(out)


def _field(number: int, wire: int, payload: bytes | int) -> bytes:
    key = _varint((number << 3) | wire)
    if wire == 2:
        return key + _varint(len(payload)) + payload  # type: ignore[arg-type]
    return key + _varint(int(payload))


def _domain(kind: int, value: str, attrs: tuple[str, ...] = ()) -> bytes:
    body = _field(1, 0, kind) + _field(2, 2, value.encode())
    for attr in attrs:
        body += _field(3, 2, _field(1, 2, attr.encode()))
    return body


def _geosite(name: str, domains: list[bytes]) -> bytes:
    body = _field(1, 2, name.encode())
    for domain in domains:
        body += _field(2, 2, domain)
    return body


def test_dlc_dat_decoder():
    blob = _field(1, 2, _geosite("OPENAI", [_domain(2, "openai.com"), _domain(3, "chat.openai.com")]))
    blob += _field(1, 2, _geosite("CN", [_domain(2, "baidu.com", ("cn",))]))
    documents = parse_v2fly_dat(blob)
    assert [str(r.rule) for r in documents["openai"].rules] == [
        "DOMAIN-SUFFIX,openai.com",
        "DOMAIN,chat.openai.com",
    ]
    assert documents["cn"].rules[0].attributes == {"cn"}


def test_varint_roundtrip():
    for value in (0, 1, 127, 128, 300, 2**32):
        encoded = _varint(value)
        assert read_varint(encoded, 0) == (value, len(encoded))


def test_steam_cm_directory_uses_exact_public_addresses():
    import json
    import pytest
    from builder.parse import parse_steam_cm

    doc = parse_steam_cm(json.dumps({"response": {"result": 1, "serverlist": [
        "103.10.124.123:27017", "[2606:4700:4700::1111]:27017", "127.0.0.1:27017", "0.0.0.0/0:27017", "example.com:27017"
    ]}}))
    assert [str(r.rule) for r in doc.rules] == ["IP-CIDR,103.10.124.123/32", "IP-CIDR6,2606:4700:4700::1111/128"]
    with pytest.raises(ValueError):
        parse_steam_cm('{"response":{"result":1,"serverlist":[]}}')
    with pytest.raises(ValueError):
        parse_steam_cm('{"response":{"result":2}}')
