# -*- coding: utf-8 -*-

import re

# Prepare some dummy requirements for module importing
import __builtin__
__builtin__._ = lambda x: x

from module.plugins.hoster.UpleaCom import UpleaCom

def test_uplea_name_regex():
    def test(name):
        sample = ur'<span class="gold-text">%s</span>' % name
        assert re.match(UpleaCom.NAME_PATTERN, sample)
        assert re.match(UpleaCom.NAME_PATTERN, sample).group('N') == name
    test(ur"°1 Caractères accentués.bin")

def test_uplea_size_regex():
    def test(size_str, size):
        sample = ur'<span class="label label-info agmd">%s</span>' % size_str
        assert re.match(UpleaCom.SIZE_PATTERN, sample)
        assert re.match(UpleaCom.SIZE_PATTERN, sample).group('S') == size
    test("666.66 Mo", "666.66")

if __name__ == "__main":
    test_uplea_regex()

