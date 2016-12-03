# -*- coding: utf-8 -*-

from __future__ import absolute_import
import re
from random import choice
from time import sleep

from .RequestFactory import getURL


def get_ip(n=10):
    """retrieve current ip. try n times for n seconds"""
    services = [
        ("http://checkip.dyndns.org", r".*Current IP Address: (\S+)</body>.*"),
        ("http://myexternalip.com/raw", r"(\S+)"),
        ("http://icanhazip.com", r"(\S+)"),
        ("http://ifconfig.me/ip", r"(\S+)")
    ]

    ip = ""
    for i in range(n):
        try:
            sv = choice(services)
            ip = getURL(sv[0])
            ip = re.match(sv[1], ip).group(1)
            break
        except:
            ip = ""
            sleep(1)

    return ip
