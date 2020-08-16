# -*- coding: utf-8 -*-

import socket

# import googletrans


def get_ip():
    return socket.gethostbyname(socket.getfqdn())


# def translate(text, in_lang="auto", out_lang="en"):
# translator = googletrans.Translator()
# return translator.translate(text, out_lang, in_lang).text
