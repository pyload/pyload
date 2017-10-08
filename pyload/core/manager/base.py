# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

from abc import ABCMeta, abstractmethod

from future import standard_library
from future.builtins import object
from future.utils import with_metaclass

from pyload.utils.layer.safethreading import Lock

standard_library.install_aliases()


class BaseManager(with_metaclass(ABCMeta, object)):
    """Base manager."""

    def __init__(self, core):
        """Constructor."""
        self._ = core._
        self.pyload = core
        self.lock = Lock()
        self.setup()

    @abstractmethod
    def setup(self):
        pass
