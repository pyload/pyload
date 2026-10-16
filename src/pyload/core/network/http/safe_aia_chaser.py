import collections
import http
import urllib.parse
import urllib.request

from aia_chaser import AiaChaser
from aia_chaser import chaser as aia_chaser
from aia_chaser.constants import DEFAULT_URLOPEN_TIMEOUT
from aia_chaser.exceptions import (
    AiaChaseExhaustedError, CertificateDownloadError, CertificateParseError, NoValidAiaCaUrlError,
    RootCertificateNotFoundError)

from pyload.core.utils.web.check import is_global_host


def _validate_aia_url(url, allow_private_ip=False):
    try:
        parsed_url = urllib.parse.urlsplit(url)
        host = parsed_url.hostname
    except ValueError:
        parsed_url = None
        host = None

    if (
        parsed_url is None
        or parsed_url.scheme.lower() not in ("http", "https")
        or not host
        or (not allow_private_ip and not is_global_host(host))
    ):
        raise ValueError("AIA CA issuer URL has a non-global destination")


class _AiaRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, allow_private_ip=False):
        self.allow_private_ip = allow_private_ip
        super().__init__()

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _validate_aia_url(newurl, allow_private_ip=self.allow_private_ip)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _download_aia_certificate(url, allow_private_ip=False):
    opener = urllib.request.build_opener(
        _AiaRedirectHandler(allow_private_ip=allow_private_ip)
    )
    with opener.open(url, timeout=DEFAULT_URLOPEN_TIMEOUT) as response:
        if response.status != http.HTTPStatus.OK:
            raise CertificateDownloadError(
                message=f"could not download {url}",
                url_string=url,
            )

        try:
            return aia_chaser._try_parse_certificate(response.read())
        except CertificateParseError as err:
            raise CertificateDownloadError(
                message=str(err),
                url_string=url,
            ) from None


def _try_download_aia_certificates(urls, allow_private_ip=False):
    http_urls = [url for url in urls if url.lower().startswith(("http:", "https:"))]
    if not http_urls:
        raise NoValidAiaCaUrlError(urls=urls)

    errors = []
    for url in http_urls:
        _validate_aia_url(url, allow_private_ip=allow_private_ip)
        try:
            return _download_aia_certificate(
                url,
                allow_private_ip=allow_private_ip,
            )
        except (CertificateDownloadError, CertificateParseError, OSError) as err:
            errors.append(err)

    raise AiaChaseExhaustedError(errors=errors)


class SafeAiaChaser(AiaChaser):
    def __init__(self, allow_private_ip=False):
        self.allow_private_ip = allow_private_ip
        super().__init__()

    def fetch_host_cert(self, host, port=443):
        if not self.allow_private_ip and not is_global_host(host):
            raise ValueError("AIA chaser blocked a non-global destination")
        return super().fetch_host_cert(host, port)

    def aia_chase_cert(self, certificate):
        to_process = collections.deque([certificate])
        while True:
            cert = to_process.popleft()
            cert_info = aia_chaser._extract_aia_info(cert)

            if cert_info.subject in self._trusted:
                yield self._trusted[cert_info.subject]
                break
            if cert_info.subject == cert_info.issuer:
                if cert_info.issuer not in self._trusted:
                    raise RootCertificateNotFoundError(
                        subject=cert_info.issuer.rfc4514_string(),
                    )
                yield self._trusted[cert_info.issuer]
                break

            yield cert

            if not cert_info.aia_ca_issuers:
                if not to_process and cert_info.issuer not in self._trusted:
                    raise RootCertificateNotFoundError(
                        subject=cert_info.issuer.rfc4514_string(),
                    )
                yield self._trusted[cert_info.issuer]
                break

            if not self.allow_private_ip:
                for url in cert_info.aia_ca_issuers:
                    if url.lower().startswith(("http:", "https:")):
                        _validate_aia_url(
                            url,
                            allow_private_ip=self.allow_private_ip,
                        )

            to_process.extend(
                _try_download_aia_certificates(
                    cert_info.aia_ca_issuers,
                    allow_private_ip=self.allow_private_ip,
                )
            )
