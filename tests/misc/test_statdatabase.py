# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()
from builtins import object

from tests.helper.stubs import Core


class TestStatDatabase(object):

    @classmethod
    def setUpClass(cls):
        cls.core = Core()

    def test_simple(self):
        assert 1 == 0
