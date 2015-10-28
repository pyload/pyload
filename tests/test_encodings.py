# -*- coding: utf-8 -*-

import module.plugins.internal.utils as utils

def test_encodings():
    assert utils.fixurl(u"é") == u"é"
    assert utils.fixurl(u"é", unquote=False) == u"é"
    assert utils.fixname(u"é") == u"é"
    assert utils.parse_name(u"é") == u"é"

