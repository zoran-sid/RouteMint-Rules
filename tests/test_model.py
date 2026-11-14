from __future__ import annotations

import pytest

from builder.model import Rule, RuleError, RuleType


def test_parse_suffix_lowercases_and_strips_dot():
    rule = Rule.parse("DOMAIN-SUFFIX, Example.COM. ")
    assert rule == Rule(RuleType.DOMAIN_SUFFIX, "example.com")


def test_wildcard_becomes_suffix():
    assert Rule.parse("DOMAIN-SUFFIX,*.example.com") == Rule(RuleType.DOMAIN_SUFFIX, "example.com")


def test_single_label_allowed_for_tld_and_localhost():
    assert Rule.parse("DOMAIN-SUFFIX,cn").value == "cn"
    assert Rule.parse("DOMAIN,localhost").value == "localhost"


def test_idna_is_encoded():
    value = Rule.parse("DOMAIN-SUFFIX,中国移动.中国").value
    assert value.startswith("xn--") and value.endswith(".xn--fiqs8s")


def test_ip_rules_are_canonicalised():
    assert Rule.parse("IP-CIDR,1.2.3.4/24") == Rule(RuleType.IP_CIDR, "1.2.3.0/24")
    assert Rule.parse("IP-CIDR6,2001:db8::1/32").value == "2001:db8::/32"


@pytest.mark.parametrize(
    "text",
    [
        "DOMAIN",
        "BOGUS,example.com",
        "IP-CIDR,not-an-ip",
        "IP-CIDR6,1.2.3.0/24",
        "IP-CIDR,2001:db8::/32",
        "DOMAIN-SUFFIX,exa mple.com",
    ],
)
def test_invalid_rules_raise(text):
    with pytest.raises((RuleError, ValueError)):
        Rule.parse(text)


def test_suffix_matching_includes_subdomains_and_apex():
    rule = Rule.parse("DOMAIN-SUFFIX,openai.com")
    assert rule.matches_domain("openai.com")
    assert rule.matches_domain("api.openai.com")
    assert not rule.matches_domain("notopenai.com")


def test_exact_domain_does_not_match_subdomain():
    rule = Rule.parse("DOMAIN,openai.com")
    assert rule.matches_domain("openai.com")
    assert not rule.matches_domain("api.openai.com")


def test_keyword_matching():
    rule = Rule.parse("DOMAIN-KEYWORD,openai")
    assert rule.matches_domain("my-openai-proxy.net")


def test_ip_matching_respects_family():
    rule = Rule.parse("IP-CIDR,10.0.0.0/8")
    assert rule.matches_ip("10.1.1.1")
    assert not rule.matches_ip("11.1.1.1")
