# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, unicode_literals

from future import standard_library
standard_library.install_aliases()

from pyload.plugins import Base


class ContentProvider(Base):
    """
    Base class to implement services that enables the user to search for content and add it for downloading.
    """

    def newest(self):
        """
        TODO.
        """

    def search(self, query):
        """
        TODO.
        """

    def suggest(self, query):
        """
        TODO.
        """
