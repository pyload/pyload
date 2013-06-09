#!/usr/bin/env python
# -*- coding: utf-8 -*-

def blue(string):
    return "\033[1;34m" + unicode(string) + "\033[0m"

def green(string):
    return "\033[1;32m" + unicode(string) + "\033[0m"

def yellow(string):
    return "\033[1;33m" + unicode(string) + "\033[0m"

def red(string):
    return "\033[1;31m" + unicode(string) + "\033[0m"

def cyan(string):
    return "\033[1;36m" + unicode(string) + "\033[0m"

def mag(string):
    return "\033[1;35m" + unicode(string) + "\033[0m"

def white(string):
    return "\033[1;37m" + unicode(string) + "\033[0m"

def println(line, content):
        print "\033[" + str(line) + ";0H\033[2K" + content