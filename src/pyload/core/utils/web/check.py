# -*- coding: utf-8 -*-

import os
import random
import re
import time

from ...network.request_factory import get_url
# import validators
from ..convert import to_str
from . import format

# import idna
# import requests


# from .convert import splitaddress


# def is_ipv4(value):
# try:
# validators.ipv4(value)
# except validators.ValidationFailure:
# return False
# return True


# def is_ipv6(value):
# try:
# validators.ipv6(value)
# except validators.ValidationFailure:
# return False
# return True


# def is_ip(value):
# return is_ipv4(value) or is_ipv6(value)


# def is_port(value):
#     return 0 <= value <= 65535


# _RE_ISH = re.compile(r"(?!-)[\w^_]{1,63}(?<!-)$", flags=re.I)

# def is_host(value):
#     MAX_HOSTNAME_LEN = 253
#     try:
#         # returns bytestring, then encode to str
#         value = to_str(idna.encode(value))
#     except AttributeError:
#         pass
#     if value.endswith("."):
#         value = value[:-1]
#     if not value or len(value) > MAX_HOSTNAME_LEN:
#         return False
#     return all(map(_RE_ISH.match, value.split(".")))


# def is_socket(value):
# ip, port = splitaddress(value)
# return is_ip(ip) and is_port(port)


# def is_endpoint(value):
#     host, port = splitaddress(value)
#     return is_host(host) and is_port(port)


# def is_online(url, *args, **kwargs):
#     online = True
#     url = format.url(url)

#     kwargs.setdefault("allow_redirects", True)
#     kwargs.setdefault("verify", False)
#     try:
#         requests.head(url, *args, **kwargs).raise_for_status()
#     except requests.TooManyRedirects:
#         online = True
#     except (requests.ConnectionError, requests.ConnectTimeout):
#         online = None
#     except requests.RequestException:
#         online = False

#     return online


# def is_resource(url, *args, **kwargs):
#     url = format.url(url)

#     kwargs.setdefault("allow_redirects", True)
#     kwargs.setdefault("verify", False)
#     r = requests.head(url, *args, **kwargs)

#     if "content-disposition" in r.headers:
#         return True

#     mime = ""
#     content = r.headers.get("content-type")
#     if content:
#         mime, _, _ = content.rpartition("charset=")
#     else:
#         from . import parse

#         name = parse.name(url)
#         _, ext = os.path.splitext(name)
#         if ext:
#             mime = parse.mime(name)

#     if "html" not in mime:
#         return True

#     return False


# TODO: Recheck in 0.5.x
# def is_url(url):
#     url = format.url(url)
#     try:
#         return validators.url(url)
#     except validators.ValidationFailure:
#         return False

def get_public_ipv4():
    """
    retrieve current public ipv4.
    """
    services = [
        ("https://ipv4.icanhazip.com/", r"(\S+)"),
        ("https://checkip.amazonaws.com/", r"(\S+)"),
        ("https://whatismyip.akamai.com/", r"(\S+)"),
        ("http://checkip.dyndns.org/", r".*Current IP Address: (\S+)</body>.*"),
        ("https://api4.ipify.org/", r"(\S+)"),
        ("https://v4.ident.me/", r"(\S+)"),
    ]

    ip = ""
    for i in range(10):
        try:
            sv = random.choice(services)
            ip = get_url(sv[0])
            ip = re.match(sv[1], ip).group(1)
            break
        except Exception:
            ip = ""
            time.sleep(0.5)

    return ip

