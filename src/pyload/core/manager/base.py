# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

from future import standard_library
standard_library.install_aliases()
from builtins import object

from pyload.utils.layer.safethreading import Lock


class BaseManager(object):
    """
    Base manager
    """

    def __init__(self, core):
        """
        Constructor.
        """
        self.pyload = core
        self._ = core._
        self.lock = Lock()
