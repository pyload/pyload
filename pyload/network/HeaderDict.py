#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from bottle import HeaderDict as BottleHeaderDict


class HeaderDict(BottleHeaderDict):
    """ Multidict for header values  """

    def to_headerlist(self):
        """  Converts all entries to header list usable by curl """
        header = []
        for key in self.keys():
            fields = ",".join(self.getall(key))

            if fields:
                header.append("%s: %s" % (key, fields))
            else:
                # curl will remove this header
                header.append("%s:" % key)

        return header
