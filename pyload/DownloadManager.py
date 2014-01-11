#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#   Copyright(c) 2008-2014 pyLoad Team
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


class DownloadManager:
    """ Schedules and manages download and decrypter jobs. """

    def __init__(self, core):
        self.core = core

    def work(self):
        """ Does the periodical work """

