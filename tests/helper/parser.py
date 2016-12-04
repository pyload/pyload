# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import codecs

def parse_config(path):
    f = codecs.open(path, "rb", "utf_8")
    result = {}

    current_section = None
    for line in f.readlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("["):
            current_section = line.replace("[", "").replace("]", "")
            result[current_section] = []
        else:
            if not current_section:
                raise Exception("Line without section: %s" % line)
            result[current_section].append(line)

    return result
