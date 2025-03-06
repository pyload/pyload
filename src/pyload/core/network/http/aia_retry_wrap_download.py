# -*- coding: utf-8 -*-

import os
import datetime
from functools import wraps
from urllib.parse import urlsplit

import OpenSSL
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import Encoding
import pycurl


if not hasattr(pycurl, "PROXYTYPE_HTTPS"):
    pycurl.PROXYTYPE_HTTPS = 2


def aia_retry_wrap_download(download):
    """
    decorator for HTTPRequest.load and HTTPDownload._download
    """

    # https://stackoverflow.com/a/36944992/10440128
    @wraps(download)
    def download_wrapper_aia_retry(self, *args, **kwargs):
        try:
            return download(self, *args, **kwargs)
        except pycurl.error as exc:
            if exc.args != (
                60,
                "SSL certificate problem: unable to get local issuer certificate",
            ):
                raise

        pyload = self.options["pyload"]

        try:
            # HTTPRequest
            # self.c = pycurl.Curl()
            curl_instance = self.c
            # def load(self, url, ...
            url = args[0]
        except AttributeError:
            # HTTPDownload
            # self.m = self.manager = pycurl.CurlMulti()
            curl_instance = self.m
            # def __init__(self, url, ...
            url = self.url

        url_parsed = urlsplit(url)
        host = url_parsed.netloc  # host and port

        try:
            _verified_cert_chain, missing_certs = pyload.aia_session.aia_chase(
                host,
                timeout=10,
            )
        except OpenSSL.crypto.X509StoreContextError as exc:
            if exc.errors[0] == 19:
                # assert exc.errors[2] == "self-signed certificate in certificate chain"
                # exc._aia_verified_cert_chain[-1] is the untrusted root cert
                cert = exc._aia_verified_cert_chain[-1].to_cryptography()
                cert_hash = cert.fingerprint(hashes.SHA256()).hex()
                untrusted_root_certs_dir = (
                    pyload.userdir + "/cache/untrusted-root-certs"
                )
                os.makedirs(untrusted_root_certs_dir, exist_ok=True)
                untrusted_cert_path = untrusted_root_certs_dir + f"/{cert_hash}.crt"
                with open(untrusted_cert_path, "wb") as f:
                    f.write(cert.public_bytes(Encoding.PEM))
                trusted_root_certs_dir = pyload.userdir + "/settings/trusted-root-certs"
                os.makedirs(trusted_root_certs_dir, exist_ok=True)
                trusted_cert_path = trusted_root_certs_dir + f"/{cert_hash}.crt"
                self.log.info(
                    f"found untrusted root cert in cert chain of {url}. "
                    f"to trust this root cert, move it with "
                    f"`mv {untrusted_cert_path} {trusted_cert_path}` "
                    f"and restart pyload."
                )
                # TODO handle untrusted root cert
                # show popup and let user decide on trust
            raise
        except Exception:
            raise

        assert len(missing_certs) > 0

        # https://stackoverflow.com/a/28147286/10440128
        def datetime_str():
            return datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S.%fZ")

        # create new ca-bundle.crt including missing certs
        ca_bundle_dir = pyload.userdir + "/cache/ca-bundle"
        os.makedirs(ca_bundle_dir, exist_ok=True)
        new_ca_bundle_path = ca_bundle_dir + f"/{datetime_str()}.crt"
        with (
            open(pyload.ca_bundle_path, "rb") as src,
            open(new_ca_bundle_path, "wb") as dst,
        ):
            dst.write(
                src.read()
                + b"\n"
                + b"\n".join(
                    map(
                        lambda c: OpenSSL.crypto.dump_certificate(
                            OpenSSL.crypto.FILETYPE_PEM, c
                        ),  # pyopenssl
                        # lambda c: c.public_bytes(
                        #     encoding=serialization.Encoding.PEM
                        # ), # cryptography
                        missing_certs,
                    )
                )
            )

        if pyload.ca_bundle_path.startswith(ca_bundle_dir):
            try:
                os.unlink(pyload.ca_bundle_path)
                self.log.debug(f"deleted old ca-bundle {pyload.ca_bundle_path}")
            except Exception as exc:
                self.log.debug(f"failed to delete old ca-bundle {pyload.ca_bundle_path}: {exc}")

        pyload.ca_bundle_path = new_ca_bundle_path

        # update curl config
        # note: the new ca-bundle file must have a different path
        # http_request: self.c = pycurl.Curl()
        # http_download: self.m = self.manager = pycurl.CurlMulti()
        curl_instance = self.c if hasattr(self, "c") else self.m
        # TODO verify. does this work with CurlMulti
        curl_instance.setopt(
            pycurl.CAINFO, self.options["pyload"].ca_bundle_path
        )  # http_request

        # retry download
        try:
            return download(self, *args, **kwargs)
        except pycurl.error as exc:
            if exc.args != (
                60,
                "SSL certificate problem: unable to get local issuer certificate",
            ):
                raise
            self.log.error(f"failed to fetch missing SSL certificates for {url}")
            raise

    return download_wrapper_aia_retry
