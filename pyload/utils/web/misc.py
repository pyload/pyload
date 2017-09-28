# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

import socket

import googletrans
from future import standard_library

standard_library.install_aliases()


def get_ip():
    return socket.gethostbyname(socket.getfqdn())


def translate(text, in_lang='auto', out_lang='en'):
    translator = googletrans.Translator()
    return translator.translate(text, out_lang, in_lang).text
