# -*- coding: utf-8 -*-


def blue(text):
    return f"\033[1;34m{text}\033[0m"


def green(text):
    return f"\033[1;32m{text}\033[0m"


def yellow(text):
    return f"\033[1;33m{text}\033[0m"


def red(text):
    return f"\033[1;31m{text}\033[0m"


def cyan(text):
    return f"\033[1;36m{text}\033[0m"


def mag(text):
    return f"\033[1;35m{text}\033[0m"


def white(text):
    return f"\033[1;37m{text}\033[0m"


def println(line, content):
    print(f"\033[{line};0H\033[2K", content)
