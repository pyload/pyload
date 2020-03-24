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

from __future__ import with_statement

import logging
from os.path import exists
from os.path import join


CONF_VERSION = 1

########################################################################
class ConfigParser:

    #----------------------------------------------------------------------
    def __init__(self, configdir):
        """Constructor"""
        self.log = logging.getLogger("guilog")
        self.configdir = configdir
        self.config = {}

        if self.checkVersion():
            self.readConfig()

    #----------------------------------------------------------------------
    def checkVersion(self):

        if not exists(join(self.configdir, "pyload.conf")):
            return False
        f = open(join(self.configdir, "pyload.conf"), "rb")
        v = f.readline()
        f.close()
        v = v[v.find(":")+1:].strip()

        if int(v) < CONF_VERSION:
            return False

        return True

    #----------------------------------------------------------------------
    def readConfig(self):
        """reads the config file"""

        self.config = self.parseConfig(join(self.configdir, "pyload.conf"))


    #----------------------------------------------------------------------
    def parseConfig(self, config):
        """parses a given configfile"""

        f = open(config)

        config = f.read()

        config = config.split("\n")[1:]

        conf = {}

        section, option, value, typ, desc = "","","","",""

        listmode = False

        for line in config:

            line = line.rpartition("#") # removes comments

            if line[1]:
                line = line[0]
            else:
                line = line[2]

            line = line.strip()

            try:

                if line == "":
                    continue
                elif line.endswith(":"):
                    section, dummy, desc = line[:-1].partition('-')
                    section = section.strip()
                    desc = desc.replace('"', "").strip()
                    conf[section] = { "desc" : desc }
                else:
                    if listmode:

                        if line.endswith("]"):
                            listmode = False
                            line = line.replace("]","")

                        value += [self.cast(typ, x.strip()) for x in line.split(",") if x]

                        if not listmode:
                            conf[section][option] = { "desc" : desc,
                                                      "type" : typ,
                                                      "value" : value}


                    else:
                        content, dummy, value = line.partition("=")

                        content, dummy, desc = content.partition(":")

                        desc = desc.replace('"', "").strip()

                        typ, option = content.split()

                        value = value.strip()

                        if value.startswith("["):
                            if value.endswith("]"):
                                listmode = False
                                value = value[:-1]
                            else:
                                listmode = True

                            value = [self.cast(typ, x.strip()) for x in value[1:].split(",") if x]
                        else:
                            value = self.cast(typ, value)

                        if not listmode:
                            conf[section][option] = { "desc" : desc,
                                                      "type" : typ,
                                                      "value" : value}

            except Exception:
                pass


        f.close()
        return conf

    #----------------------------------------------------------------------
    @classmethod
    def cast(self, typ, value):
        """cast value to given format"""
        if not isinstance(value, (str, unicode)):
            return value

        if typ == "int":
            return int(value)
        elif typ == "bool":
            return True if value.lower() in ("1","true", "on", "an","yes") else False
        else:
            return value

    #----------------------------------------------------------------------
    def get(self, section, option):
        """get value"""
        return self.config[section][option]["value"]

    #----------------------------------------------------------------------
    def __getitem__(self, section):
        """provides dictonary like access: c['section']['option']"""
        return Section(self, section)

########################################################################
class Section:
    """provides dictionary like access for configparser"""

    #----------------------------------------------------------------------
    def __init__(self, parser, section):
        """Constructor"""
        self.log = logging.getLogger("guilog")
        self.parser = parser
        self.section = section

    #----------------------------------------------------------------------
    def __getitem__(self, item):
        """getitem"""
        return self.parser.get(self.section, item)
