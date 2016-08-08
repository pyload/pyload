#!/usr/bin/env python
# coding:utf-8

import re
from os import listdir


class Wrapper(object):
    pass


def filter_info(line):
    reject_list = [
       "object at 0x",
       " at line ",
       " <DownloadThread(",
       "<class '",
       "PyFile ",
       " <module '"
    ]
    for reject_text in reject_list:
        if reject_text in line:
            return False
    return True


def appendName(lines, name):
    test = re.compile("^[a-zA-z0-9]+ = ")
    for i, line in enumerate(lines):
        if test.match(line):
            lines[i] = name + "." + line
    return lines


def initReport():
    reports = []
    for f in listdir("."):
        if f.startswith("debug_"):
            reports.append(f)

    for i, f in enumerate(reports):
        print "%s. %s" % (i, f)

    choice = raw_input("Choose Report: ")
    report = reports[int(choice)]
    f = open(report, "rb")
    content = f.readlines()
    content = [x.strip() for x in content if x.strip()]

    frame = Wrapper()
    plugin = Wrapper()
    pyfile = Wrapper()

    frame_c = []
    plugin_c = []
    pyfile_c = []

    dest = None

    for line in content:
        if line == "FRAMESTACK:":
            dest = frame_c
            continue
        elif line == "PLUGIN OBJECT DUMP:":
            dest = plugin_c
            continue
        elif line == "PYFILE OBJECT DUMP:":
            dest = pyfile_c
            continue
        elif line == "CONFIG:":
            dest = None
        if dest is not None:
            dest.append(line)

    frame_c = filter(filter_info, frame_c)
    plugin_c = filter(filter_info, plugin_c)
    pyfile_c = filter(filter_info, pyfile_c)

    frame_c = appendName(frame_c, "frame")
    plugin_c = appendName(plugin_c, "plugin")
    pyfile_c = appendName(pyfile_c, "pyfile")

    "\n".join(frame_c + plugin_c + pyfile_c)
    return frame, plugin, pyfile


if __name__ == '__main__':
    print "No main method, use this module with your python shell"
