# -*- coding: utf-8 -*-

import colorama

colorama.init(autoreset=True)

def color(color, text):
    return colorama.Fore.(c.upper())(text)

for c in colorama.Fore:
    eval("%(color) = lambda msg: color(%(color), msg)" % {'color': c.lower()}


def overline(line, msg):
    print "\033[%(line)s;0H\033[2K%(msg)s" % {'line': str(line), 'msg': msg}
