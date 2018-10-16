# -*- coding: utf-8 -*-

from builtins import str


def blue(string):
    return "\033[1;34m{}\033[0m".format(string)


def green(string):
    return "\033[1;32m{}\033[0m".format(string)


def yellow(string):
    return "\033[1;33m{}\033[0m".format(string)


def red(string):
    return "\033[1;31m{}\033[0m".format(string)


def cyan(string):
    return "\033[1;36m{}\033[0m".format(string)


def mag(string):
    return "\033[1;35m{}\033[0m".format(string)


def white(string):
    return "\033[1;37m{}\033[0m".format(string)


def println(line, content):
    print("\033[{};0H\033[2K{}".format(line, content)
