#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from subprocess import Popen, PIPE
from time import time, gmtime, strftime

aliases = {"zoidber": "zoidberg", "zoidberg10": "zoidberg", "webmaster": "dhmh", "mast3rranan": "ranan",
           "ranan2": "ranan"}
exclude = ["locale/*", "module/lib/*"]
date_format = "%Y-%m-%d"
line_re = re.compile(r" (\d+) \**", re.I)

def add_exclude_flags(args):
    for dir in exclude:
        args.extend(["-X", dir])

# remove small percentages
def wipe(data, perc=1):
    s = (sum(data.values()) * perc) / 100
    for k, v in data.items():
        if v < s: del data[k]

    return data

# remove aliases
def de_alias(data):
    for k, v in aliases.iteritems():
        if k not in data: continue
        alias = aliases[k]

        if alias in data: data[alias] += data[k]
        else: data[alias] = data[k]

        del data[k]

    return data


def output(data):
    s = float(sum(data.values()))
    print "Total Lines: %d" % s
    for k, v in data.iteritems():
        print "%15s: %.1f%% | %d" % (k, (v * 100) / s, v)
    print


def file_list():
    args = ["hg", "status", "-A"]
    add_exclude_flags(args)
    p = Popen(args, stdout=PIPE)
    out, err = p.communicate()
    return [x.split()[1] for x in out.splitlines() if x.split()[0] in "CMA"]


def hg_annotate(path):
    args = ["hg", "annotate", "-u", path]
    p = Popen(args, stdout=PIPE)
    out, err = p.communicate()

    data = {}

    for line in out.splitlines():
        author, non, line = line.partition(":")

        # probably binary file
        if author == path: return {}

        author = author.strip().lower()
        if not line.strip(): continue # don't count blank lines

        if author in data: data[author] += 1
        else: data[author] = 1

    return de_alias(data)


def hg_churn(days=None):
    args = ["hg", "churn"]
    if days:
        args.append("-d")
        t = time() - 60 * 60 * 24 * days
        args.append("%s to %s" % (strftime(date_format, gmtime(t)), strftime(date_format)))

    add_exclude_flags(args)
    p = Popen(args, stdout=PIPE)
    out, err = p.communicate()

    data = {}

    for line in out.splitlines():
        m = line_re.search(line)
        author = line.split()[0]
        lines = int(m.group(1))

        if "@" in author:
            author, n, email = author.partition("@")

        author = author.strip().lower()

        if author in data: data[author] += lines
        else: data[author] = lines

    return de_alias(data)


def complete_annotate():
    files = file_list()
    data = {}
    for f in files:
        tmp = hg_annotate(f)
        for k, v in tmp.iteritems():
            if k in data: data[k] += v
            else: data[k] = v

    return data


if __name__ == "__main__":
    for d in (30, 90, 180):
        c = wipe(hg_churn(d))
        print "Changes in %d days:" % d
        output(c)

    c = wipe(hg_churn())
    print "Total changes:"
    output(c)

    print "Current source code version:"
    data = wipe(complete_annotate())
    output(data)


