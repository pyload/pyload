# -*- coding: utf-8 -*-

import os
import re
import sys


def chars(text, chars, repl=""):
    """
    Removes all chars in repl from text.
    """
    return re.sub(rf"[{chars}]+", repl, text)


_UNIXBADCHARS = ("\0", "/", "\\")
_MACBADCHARS = _UNIXBADCHARS + (":",)
_WINBADCHARS = _MACBADCHARS + ("<", ">", '"', "|", "?", "*")
_WINBADWORDS = (
    "com1",
    "com2",
    "com3",
    "com4",
    "com5",
    "com6",
    "com7",
    "com8",
    "com9",
    "lpt1",
    "lpt2",
    "lpt3",
    "lpt4",
    "lpt5",
    "lpt6",
    "lpt7",
    "lpt8",
    "lpt9",
    "con",
    "prn",
)


def name(text, sep="_", allow_whitespaces=False):
    """Remove invalid characters."""
    if os.name == "nt":
        bc = _WINBADCHARS
    elif sys.platform == "darwin":
        bc = _MACBADCHARS
    else:
        bc = _UNIXBADCHARS
    repl = r"".join(bc)
    if not allow_whitespaces:
        repl += " "
    res = chars(text, repl, sep).strip()
    if os.name == "nt" and res.lower() in _WINBADWORDS:
        res = sep + res
    return res


def pattern(text, rules):
    for rule in rules:
        try:
            pattr, repl, flags = rule
        except ValueError:
            pattr, repl = rule
            flags = 0
        text = re.sub(pattr, repl, text, flags)
    return text


def truncate(text, to_length):
    min_length = len(text) // 2
    if to_length <= min_length:
        return
    offset = to_length // 3
    return f"{text[:offset * 2]}~{text[-offset + to_length % 3:]}"


def uniquify(seq):
    """Remove duplicates from list preserving order."""
    seen = set()
    seen_add = seen.add
    return type(seq)(x for x in seq if x not in seen and not seen_add(x))
