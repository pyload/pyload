#!/usr/bin/env python
# -*- coding: utf-8 -*-

from builtins import str
def blue(string):
    return "\033[1;34m" + str(string) + "\033[0m"

def green(string):
    return "\033[1;32m" + str(string) + "\033[0m"

def yellow(string):
    return "\033[1;33m" + str(string) + "\033[0m"

def red(string):
    return "\033[1;31m" + str(string) + "\033[0m"

def cyan(string):
    return "\033[1;36m" + str(string) + "\033[0m"

def mag(string):
    return "\033[1;35m" + str(string) + "\033[0m"

def white(string):
    return "\033[1;37m" + str(string) + "\033[0m"

def println(line, content):
        print("\033[" + str(line) + ";0H\033[2K" + content)