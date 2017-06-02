# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import unicode_literals
from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()
import socket

import googletrans


def get_ip():
    return socket.gethostbyname(socket.getfqdn())


def translate(text, in_lang='auto', out_lang='en'):
    translator = googletrans.Translator()
    return translator.translate(text, out_lang, in_lang)
