# -*- coding: utf-8 -*-

import re


def chars(text, chars, repl=""):
    """
    Removes all chars in repl from text.
    """
    chars = chars.replace("\\", "\\\\")
    return re.sub(rf"[{chars}]", repl, text)


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


def name(text, sep="_", allow_whitespaces=True):
    """Remove invalid characters."""
    bc = uniquify(_WINBADCHARS + _MACBADCHARS + _UNIXBADCHARS)
    repl = r"".join(bc)
    if not allow_whitespaces:
        repl += " "
    res = chars(text, repl, sep).strip()
    if res.lower() in _WINBADWORDS:
        res = (sep or "_") + res
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
        raise OSError("File name too long")
    offset = to_length // 3
    return f"{text[:offset * 2]}~{text[-(offset - 1 + to_length % 3):]}"


def uniquify(seq):
    """Remove duplicates from seq preserving order."""

    seen = set()

    def make_hashable(item):
        if isinstance(item, list):
            return tuple(make_hashable(x) for x in item)
        elif isinstance(item, dict):
            return tuple(sorted((k, make_hashable(v)) for k, v in item.items()))
        elif isinstance(item, set):
            return tuple(sorted(make_hashable(x) for x in item))
        return item

    return type(seq)(x for x in seq if not (make_hashable(x) in seen or seen.add(make_hashable(x))))
