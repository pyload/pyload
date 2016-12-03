# -*- coding: utf-8 -*-

###############################################################################
#   Copyright(c) 2009-2017 pyLoad Team
#   http://www.pyload.org
#
#   This file is part of pyLoad.
#   pyLoad is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   Subjected to the terms and conditions in LICENSE
#
#   @author: RaNaN
###############################################################################


from __future__ import absolute_import
from __future__ import unicode_literals
from .Base import Base

class ContentProvider(Base):
    """
    Base class to implement services that enables the user to search for content and add it for downloading.
    """

    def newest(self):
        """ TODO  """

    def search(self, query):
        """  TODO """

    def suggest(self, query):
        """  TODO   """
