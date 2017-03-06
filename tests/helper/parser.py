# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, unicode_literals

import io

from future import standard_library

standard_library.install_aliases()


def parse_config(path):
    result = {}

    current_section = None
    with io.open(path, mode='rb') as fp:
        for line in fp.readlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("["):
                current_section = line.replace("[", "").replace("]", "")
                result[current_section] = []
            else:
                if not current_section:
                    raise Exception("Line without section: {}".format(line))
                result[current_section].append(line)

    return result
