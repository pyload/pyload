# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, division, unicode_literals

from future import standard_library

from pyload.plugins import Base

standard_library.install_aliases()


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
