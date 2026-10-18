from types import SimpleNamespace

import pytest

from pyload.core.network.http import safe_aia_chaser
from pyload.core.utils.web import check


def test_is_global_host_requires_all_resolved_addresses_to_be_global(monkeypatch):
    resolved_addresses = [
        (["8.8.8.8", "1.1.1.1"], True),
        (["2001:4860:4860::8888", "2606:4700:4700::1111"], True),
        (["8.8.8.8", "169.254.169.254"], False),
        (["2001:4860:4860::8888", "fe80::1"], False),
        (["8.8.8.8", "::ffff:10.0.0.1"], False),
        (["8.8.8.8", "2002:0a00:0001::"], False),
        (["8.8.8.8", "64:ff9b::a00:1"], False),
    ]

    for addresses, expected in resolved_addresses:
        monkeypatch.setitem(
            check.__dict__,
            "host_to_ip",
            lambda host, addresses=addresses: addresses,
        )

        assert check.is_global_host("example.test") is expected


def test_validate_aia_url_rejects_private_destination(monkeypatch):
    monkeypatch.setitem(
        safe_aia_chaser.__dict__,
        "is_global_host",
        lambda host: False,
    )

    with pytest.raises(ValueError, match="non-global destination"):
        safe_aia_chaser._validate_aia_url(
            "http://169.254.169.254/latest/meta-data/"
        )


def test_try_download_aia_certificates_allows_public_destination(monkeypatch):
    certificate = object()
    monkeypatch.setitem(
        safe_aia_chaser.__dict__,
        "is_global_host",
        lambda host: True,
    )
    monkeypatch.setattr(
        safe_aia_chaser,
        "_download_aia_certificate",
        lambda url, allow_private_ip=False: [certificate],
    )

    assert safe_aia_chaser._try_download_aia_certificates(
        ["http://ca.example.test/issuer.crt"]
    ) == [certificate]


def test_validate_aia_url_rejects_non_http_scheme():
    with pytest.raises(ValueError, match="non-global destination"):
        safe_aia_chaser._validate_aia_url("file:///etc/passwd")


@pytest.mark.parametrize("host", ["127.0.0.1", "::1", "fe80::1"])
def test_aia_chaser_rejects_private_initial_host(monkeypatch, host):
    chaser = safe_aia_chaser.SafeAiaChaser.__new__(
        safe_aia_chaser.SafeAiaChaser
    )
    chaser.allow_private_ip = False
    monkeypatch.setitem(
        safe_aia_chaser.__dict__,
        "is_global_host",
        lambda resolved_host: check.is_global_address(resolved_host),
    )
    monkeypatch.setattr(
        safe_aia_chaser.AiaChaser,
        "fetch_host_cert",
        lambda *args, **kwargs: pytest.fail("private host must not be connected"),
    )

    with pytest.raises(ValueError, match="non-global destination"):
        chaser.fetch_host_cert(host)


def test_aia_chaser_rejects_private_issuer_before_fetching(monkeypatch):
    chaser = safe_aia_chaser.SafeAiaChaser.__new__(
        safe_aia_chaser.SafeAiaChaser
    )
    chaser.allow_private_ip = False
    chaser._trusted = {}

    cert = object()
    info = SimpleNamespace(
        subject="leaf",
        issuer="issuer",
        aia_ca_issuers=["http://10.0.0.5:8080/internal/status"],
    )
    monkeypatch.setattr(
        safe_aia_chaser.aia_chaser,
        "_extract_aia_info",
        lambda _: info,
    )
    monkeypatch.setitem(
        safe_aia_chaser.__dict__,
        "is_global_host",
        lambda host: False,
    )
    monkeypatch.setattr(
        safe_aia_chaser,
        "_try_download_aia_certificates",
        lambda *args, **kwargs: pytest.fail("private AIA URL must not be fetched"),
    )

    with pytest.raises(ValueError, match="non-global destination"):
        list(chaser.aia_chase_cert(cert))


def test_aia_redirect_handler_rejects_private_redirect(monkeypatch):
    monkeypatch.setitem(
        safe_aia_chaser.__dict__,
        "is_global_host",
        lambda host: False,
    )
    handler = safe_aia_chaser._AiaRedirectHandler()

    with pytest.raises(ValueError, match="non-global destination"):
        handler.redirect_request(None, None, 302, "Found", {}, "http://127.0.0.1/")
