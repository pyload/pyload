import pytest

from pyload.core.utils.web.check import (
    is_global_address,
    is_loopback_address,
)


# Plain IPv4 + IPv6 baseline (should match prior behaviour).

@pytest.mark.parametrize(
    "addr",
    [
        "127.0.0.1",
        "10.0.0.1",
        "172.16.0.1",
        "192.168.1.1",
        "169.254.169.254",
        "::1",
        "fc00::1",
        "fe80::1",
    ],
)
def test_is_global_address_rejects_plain_internal(addr):
    assert is_global_address(addr) is False


# IPv4-mapped IPv6 - already covered by ipaddress.ip_address(value).is_global
# returning False for ::ffff:<v4>.

@pytest.mark.parametrize(
    "addr",
    [
        "::ffff:127.0.0.1",
        "::ffff:10.0.0.1",
        "::ffff:169.254.169.254",
    ],
)
def test_is_global_address_rejects_ipv4_mapped(addr):
    assert is_global_address(addr) is False


# 6to4 - regression test for the bypass on Python 3.9 / 3.10 / 3.11 where
# ipaddress.IPv6Address.is_global returns True for 2002::/16 even when the
# embedded IPv4 is loopback / RFC 1918 / link-local.

@pytest.mark.parametrize(
    "addr",
    [
        "2002:7f00:0001::",   # 6to4 wrap of 127.0.0.1
        "2002:0a00:0001::",   # 6to4 wrap of 10.0.0.1
        "2002:ac10:0001::",   # 6to4 wrap of 172.16.0.1
        "2002:c0a8:0101::",   # 6to4 wrap of 192.168.1.1
        "2002:a9fe:a9fe::",   # 6to4 wrap of 169.254.169.254 (AWS IMDS)
        "2002:6440:6440::",   # 6to4 wrap of 100.64.0.0 (CGNAT)
    ],
)
def test_is_global_address_rejects_6to4_internal(addr):
    assert is_global_address(addr) is False


# NAT64 - universal regression (every Python version classifies 64:ff9b::/96
# as globally routable in is_global).

@pytest.mark.parametrize(
    "addr",
    [
        "64:ff9b::7f00:1",      # NAT64 wrap of 127.0.0.1
        "64:ff9b::a9fe:a9fe",   # NAT64 wrap of 169.254.169.254
        "64:ff9b::a00:1",       # NAT64 wrap of 10.0.0.1
        "64:ff9b:1::a9fe:a9fe", # RFC 8215 discovery prefix
    ],
)
def test_is_global_address_rejects_nat64_internal(addr):
    assert is_global_address(addr) is False


# Teredo - block the prefix wholesale; the IPv4 in the last 32 bits is the
# client's external address, not a destination.

@pytest.mark.parametrize(
    "addr",
    [
        "2001::a9fe:a9fe",
        "2001:0:abcd::ef00:1234",
    ],
)
def test_is_global_address_rejects_teredo(addr):
    assert is_global_address(addr) is False


# Positive cases - public destinations remain reachable, including 6to4
# wraps of a public IPv4 (no need to penalise those).

@pytest.mark.parametrize(
    "addr",
    [
        "8.8.8.8",
        "1.1.1.1",
        "2001:4860:4860::8888",  # Google Public DNS over IPv6
        "2002:0808:0808::",      # 6to4 wrap of 8.8.8.8 (public v4)
    ],
)
def test_is_global_address_allows_public(addr):
    assert is_global_address(addr) is True


# Loopback unwrapping - is_loopback_address should also recognise the
# transition forms.

@pytest.mark.parametrize(
    "addr",
    [
        "127.0.0.1",
        "::1",
        "::ffff:127.0.0.1",
        "2002:7f00:0001::",
        "64:ff9b::7f00:1",
    ],
)
def test_is_loopback_address_recognises_transition_forms(addr):
    assert is_loopback_address(addr) is True


def test_is_loopback_address_rejects_public_6to4_wrap():
    # 6to4 wrap of 8.8.8.8 is not loopback
    assert is_loopback_address("2002:0808:0808::") is False
