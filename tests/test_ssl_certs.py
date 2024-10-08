#!/usr/bin/env python3

import os
import sys
import time
import ssl
import datetime
import subprocess
import tempfile
import random
import atexit
import signal
import shutil
import gc
import socket
from multiprocessing import Process
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlsplit

import OpenSSL

import cryptography

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives.serialization import pkcs7


# pyppeteer/util.py
def get_free_port() -> int:
    """Get free port."""
    sock = socket.socket()
    # sock.bind(('localhost', 0))
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    del sock
    gc.collect()
    return port


def create_cert(
    name, issuer_cert=None, issuer_key=None, issuer_cert_url=None, is_leaf=False
):
    """
    create a cryptography certificate and key.

    note: not pyopenssl cert
    """

    print(f"creating cert {repr(name)}")

    # https://cryptography.io/en/latest/x509/tutorial/
    # https://cryptography.io/en/latest/x509/reference/
    # https://stackoverflow.com/questions/56285000
    # https://gist.github.com/major/8ac9f98ae8b07f46b208

    is_root = issuer_cert is None

    key = rsa.generate_private_key(
        public_exponent=65537,
        # key_size=2048 is slow, but python requires 2048 bit RSA keys
        # https://github.com/python/cpython/raw/main/Modules/_ssl.c
        # @SECLEVEL=2: security level 2 with 112 bits minimum security
        # (e.g. 2048 bits RSA key)
        key_size=2048,
        backend=default_backend(),
    )

    subject_name = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Texas"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Austin"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "My Company"),
            x509.NameAttribute(NameOID.COMMON_NAME, name),
        ]
    )

    issuer_name = subject_name if is_root else issuer_cert.subject

    issuer_key = key if is_root else issuer_key

    cert = x509.CertificateBuilder()

    cert = cert.subject_name(subject_name)
    cert = cert.issuer_name(issuer_name)
    cert = cert.public_key(key.public_key())
    cert = cert.serial_number(x509.random_serial_number())
    cert = cert.not_valid_before(datetime.datetime.utcnow())
    cert = cert.not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=3650)
    )

    cert = cert.add_extension(
        x509.SubjectKeyIdentifier.from_public_key(key.public_key()),
        critical=False,
    )

    # https://stackoverflow.com/a/72320618/10440128
    # if is_root: # no. invalid CA certificate @ cert1

    if not is_leaf:
        cert = cert.add_extension(
            x509.BasicConstraints(ca=True, path_length=None), critical=True
        )
        cert = cert.add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
    else:
        cert = cert.add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(
                issuer_cert.extensions.get_extension_for_class(
                    x509.SubjectKeyIdentifier
                ).value
            ),
            critical=False,
        )

    if is_leaf:
        cert = cert.add_extension(
            x509.ExtendedKeyUsage(
                [
                    x509.ExtendedKeyUsageOID.CLIENT_AUTH,
                    x509.ExtendedKeyUsageOID.SERVER_AUTH,
                ]
            ),
            critical=False,
        )

    if issuer_cert_url:
        # add AIA extension
        # https://github.com/pyca/cryptography/raw/main/tests/x509/test_x509.py
        # aia = x509.AuthorityInformationAccess
        cert = cert.add_extension(
            x509.AuthorityInformationAccess(
                [
                    x509.AccessDescription(
                        x509.oid.AuthorityInformationAccessOID.CA_ISSUERS,
                        x509.UniformResourceIdentifier(issuer_cert_url),
                    ),
                ]
            ),
            critical=False,
        )

    # no. certificate signature failure
    # cert = cert.sign(key, hashes.SHA256(), default_backend())
    cert = cert.sign(issuer_key, hashes.SHA256(), default_backend())

    return cert, key


def run_http_server(args):

    host = args.get("host", "127.0.0.1")
    port = args.get("port", 80)
    ssl_cert_file = args.get("ssl_cert_file", None)
    ssl_key_file = args.get("ssl_key_file", None)
    root = args.get("root", "/tmp/www")
    # tmpdir = args.get("tmpdir", "/tmp")

    # https://stackoverflow.com/questions/22429648/ssl-in-python3-with-httpserver

    # SimpleHTTPRequestHandler serves files from workdir
    # this throws FileNotFoundError if root does not exist
    os.chdir(root)

    http_server = HTTPServer((host, port), SimpleHTTPRequestHandler)

    if ssl_cert_file and ssl_key_file:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        # check_hostname: require hostname to match cert subject
        ssl_context.check_hostname = False
        # https://docs.python.org/3/library/ssl.html
        # The certfile string must be the path
        # to a single file in PEM format containing the certificate
        # as well as any number of CA certificates
        # needed to establish the certificate’s authenticity.
        # The keyfile string, if present,
        # must point to a file containing the private key.
        ssl_context.load_cert_chain(ssl_cert_file, ssl_key_file)
        http_server.socket = ssl_context.wrap_socket(
            http_server.socket, server_side=True
        )

    http_server.serve_forever()


def run_test(tmpdir):

    print(f"using tempdir {repr(tmpdir)}")

    server_root = tmpdir + "/www"
    os.mkdir(server_root)

    # SSLContext.wrap_socket
    # Wrap an existing Python socket

    http_port = get_free_port()

    # create certs
    # TODO refactor ... create_cert_chain

    cert0, key0 = create_cert("root cert")
    cert0_path = f"{server_root}/cert0"
    with open(cert0_path, "wb") as f:
        # PEM format
        f.write(cert0.public_bytes(encoding=serialization.Encoding.PEM))
    url0 = f"http://127.0.0.1:{http_port}/cert0"

    cert1, key1 = create_cert("branch cert 1", cert0, key0, url0)
    cert1_path = f"{server_root}/cert1"
    with open(cert1_path, "wb") as f:
        # DER = ASN1 format
        f.write(cert1.public_bytes(encoding=serialization.Encoding.DER))
    url1 = f"http://127.0.0.1:{http_port}/cert1"

    # https://github.com/pyca/cryptography
    #   tests/hazmat/primitives/test_pkcs7.py
    # encoding = serialization.Encoding.PEM
    # encoding = serialization.Encoding.DER
    # p7 = pkcs7.serialize_certificates(certs, encoding)
    # f.write(cert2.public_bytes(encoding=serialization.Encoding.PEM))

    cert2, key2 = create_cert("branch cert 2", cert1, key1, url1)
    cert2_path = f"{server_root}/cert2"
    with open(cert2_path, "wb") as f:
        f.write(pkcs7.serialize_certificates([cert2], Encoding.DER))
    url2 = f"http://127.0.0.1:{http_port}/cert2"

    cert3, key3 = create_cert("branch cert 3", cert2, key2, url2)
    cert3_path = f"{server_root}/cert3"
    with open(cert3_path, "wb") as f:
        f.write(pkcs7.serialize_certificates([cert3], Encoding.PEM))
    url3 = f"http://127.0.0.1:{http_port}/cert3"

    # TODO test invalid url3 with invalid host or port

    # no. pycurl.error: (60, "SSL: certificate subject name 'leaf cert'
    #   does not match target host name '127.0.0.1'")
    # cert4, key4 = create_cert("leaf cert", cert3, key3, url3, is_leaf=True)

    cert4, key4 = create_cert("127.0.0.1", cert3, key3, url3, is_leaf=True)
    # cert4_path = f"{server_root}/cert4"

    all_ca_certs = [
        cert0,  # root cert
        cert1,
        cert2,
        cert3,
        # cert4, # leaf cert
    ]

    all_ca_certs_pem_path = f"{server_root}/all-certs.pem"
    with open(all_ca_certs_pem_path, "wb") as f:
        f.write(
            b"\n".join(
                map(
                    lambda c: c.public_bytes(encoding=serialization.Encoding.PEM),
                    all_ca_certs,
                )
            )
        )

    server_cert, server_key = cert4, key4

    https_server_cert_file = tempfile.mktemp(suffix=".pem", prefix="cert-", dir=tmpdir)
    with open(https_server_cert_file, "wb") as f:
        # cert_pem = OpenSSL.crypto.dump_certificate(
        #     OpenSSL.crypto.FILETYPE_PEM, server_cert
        # ) # pyopenssl
        cert_pem = server_cert.public_bytes(
            encoding=serialization.Encoding.PEM
        )  # cryptography
        f.write(cert_pem)

    https_server_key_file = tempfile.mktemp(suffix=".pem", prefix="key-", dir=tmpdir)
    with open(https_server_key_file, "wb") as f:
        # key_pem = OpenSSL.crypto.dump_privatekey(
        #     OpenSSL.crypto.FILETYPE_PEM, server_key
        # ) # pyopenssl
        # cryptography
        # https://cryptography.io/en/latest/hazmat/primitives/asymmetric/rsa/
        key_pem = server_key.private_bytes(
            encoding=serialization.Encoding.PEM,  # PEM, DER
            # TraditionalOpenSSL, OpenSSH, PKCS8
            format=serialization.PrivateFormat.PKCS8,
            # BestAvailableEncryption, NoEncryption
            encryption_algorithm=serialization.NoEncryption(),
        )
        f.write(key_pem)

    # start http server
    schema = "http"
    http_server_url = f"{schema}://127.0.0.1:{http_port}"
    print(f"starting {schema} server on {http_server_url}")
    http_server_args = dict(
        host="127.0.0.1",
        port=http_port,
        ssl_cert_file=None,
        ssl_key_file=None,
        root=server_root,
        # tmpdir=tmpdir,
    )
    http_server_process = Process(target=run_http_server, args=(http_server_args,))
    http_server_process.start()
    http_server_process.stop = lambda: os.kill(http_server_process.pid, signal.SIGSTOP)
    http_server_process.cont = lambda: os.kill(http_server_process.pid, signal.SIGCONT)

    # start https server
    schema = "https"
    https_port = get_free_port()
    https_server_url = f"{schema}://127.0.0.1:{https_port}"
    print(f"starting {schema} server on {https_server_url}")
    https_server_args = dict(
        host="127.0.0.1",
        port=https_port,
        ssl_cert_file=https_server_cert_file,
        ssl_key_file=https_server_key_file,
        root=server_root,
        # tmpdir=tmpdir,
    )
    https_server_process = Process(target=run_http_server, args=(https_server_args,))
    https_server_process.start()
    https_server_process.stop = lambda: os.kill(
        https_server_process.pid, signal.SIGSTOP
    )
    https_server_process.cont = lambda: os.kill(
        https_server_process.pid, signal.SIGCONT
    )

    def handle_exit():
        process_list = [
            http_server_process,
            https_server_process,
        ]
        for process in process_list:
            try:
                process.kill()
            except Exception:
                pass

    atexit.register(handle_exit)

    print("TODO add trusted root cert:")
    args = [
        "cp",
        cert0_path,
        "~/.pyload/settings/trusted-root-certs/test_ssl_certs.cert0.crt",
    ]
    print("  " + " ".join(args))

    test_file = "test.txt"
    with open(server_root + "/" + test_file, "w") as f:
        f.write("hello\n")

    print("... then start pyload, and add this url:")
    print(f"  {https_server_url}/{test_file}")

    # keep servers running for manual testing
    print(
        f"keeping servers running for 10 minutes: "
        f"{https_server_url} and {http_server_url}"
    )
    time.sleep(10 * 60)

    print(f"cleanup")
    handle_exit()

    print("ok")


def main():

    main_tempdir = f"/run/user/{os.getuid()}"
    if not os.path.exists(main_tempdir):
        main_tempdir = None

    with (
        tempfile.TemporaryDirectory(
            prefix="pyload.test_ssl_certs.",
            dir=main_tempdir,
            # ignore_cleanup_errors=False,
        ) as tmpdir,
    ):

        return run_test(tmpdir)


if __name__ == "__main__":

    main()
