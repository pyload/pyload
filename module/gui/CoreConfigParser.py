# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.
"""

import logging
from os.path import exists

from module.ConfigParser import ConfigParser, CONF_VERSION

class CoreConfigParser(ConfigParser):
    """
        read the local server configuration file
    """
    def __init__(self, pyloadConf):
        self.log = logging.getLogger("guilog")
        self.pyloadConf = pyloadConf
        self.config = {} # the config values

        if self.checkVersion():
            self.config = self.parseConfig(self.pyloadConf)

    def checkVersion(self):
        if not exists(self.pyloadConf):
            self.log.info("Local server config file not found: %s" % self.pyloadConf)
            return False

        f = open(self.pyloadConf, "rb")
        v = f.readline()
        f.close()
        v = v[v.find(":") + 1:].strip()

        if not v or int(v) < CONF_VERSION:
            self.log.info("Ignoring old version of local server config file: %s" % self.pyloadConf)
            return False

        return True


