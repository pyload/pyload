# -*- coding: utf-8 -*-

from __future__ import with_statement

import re

from time import sleep
from os.path import exists, join
from shutil import copy

from traceback import print_exc
from utils import chmod

# ignore these plugin configs, mainly because plugins were wiped out
IGNORE = (
    "FreakshareNet", "SpeedManager", "ArchiveTo", "ShareCx", ('hooks', 'UnRar'),
    'EasyShareCom', 'FlyshareCz'
    )

CONF_VERSION = 1

class ConfigParser:
    """
    holds and manage the configuration
    
    current dict layout:
    
    {
    
     section : { 
      option : { 
            value:
            type:
            desc:
      }
      desc: 
    
    }
    
    
    """

    CONFLINE = re.compile(r'^\s*(?P<T>.+?)\s+(?P<N>[^ ]+?)\s*:\s*"(?P<D>.+?)"\s*=\s?(?P<V>.*)')

    def __init__(self):
        """Constructor"""
        self.config = {} # the config values
        self.plugin = {} # the config for plugins
        self.oldRemoteData = {}

        self.pluginCB = None # callback when plugin config value is changed

        self.checkVersion()

        self.readConfig()

        self.deleteOldPlugins()


    def checkVersion(self, n=0):
        """determines if config need to be copied"""
        try:
            if not exists("pyload.conf"):
                copy(join(pypath, "module", "config", "default.conf"), "pyload.conf")
                chmod("pyload.conf", 0600)

            if not exists("plugin.conf"):
                f = open("plugin.conf", "wb")
                f.write("version: " + str(CONF_VERSION))
                f.close()
                chmod("plugin.conf", 0600)

            f = open("pyload.conf", "rb")
            v = f.readline()
            f.close()
            v = v[v.find(":") + 1:].strip()

            if not v or int(v) < CONF_VERSION:
                copy(join(pypath, "module", "config", "default.conf"), "pyload.conf")
                print "Old version of config was replaced"

            f = open("plugin.conf", "rb")
            v = f.readline()
            f.close()
            v = v[v.find(":") + 1:].strip()

            if not v or int(v) < CONF_VERSION:
                f = open("plugin.conf", "wb")
                f.write("version: " + str(CONF_VERSION))
                f.close()
                print "Old version of plugin-config replaced"
        except:
            if n < 3:
                sleep(0.3)
                self.checkVersion(n + 1)
            else:
                raise

    def readConfig(self):
        """reads the config file"""

        self.config = self.parseConfig(join(pypath, "module", "config", "default.conf"))
        self.plugin = self.parseConfig("plugin.conf")

        try:
            homeconf = self.parseConfig("pyload.conf")
            if "username" in homeconf["remote"]:
                if "password" in homeconf["remote"]:
                    self.oldRemoteData = {"username": homeconf["remote"]["username"]["value"],
                                          "password": homeconf["remote"]["username"]["value"]}
                    del homeconf["remote"]["password"]
                del homeconf["remote"]["username"]
            self.updateValues(homeconf, self.config)

        except Exception, e:
            print "Config Warning"
            print_exc()


    def parseConfig(self, config):
        """parses a given configfile"""

        f = open(config)

        config = f.read()

        config = config.splitlines()[1:]

        conf = {}

        section, option, value, typ, desc = "", "", "", "", ""

        listmode = False

        for line in config:
            comment = line.rfind("#")
            if line.find(":", comment) < 0 > line.find("=", comment) and comment > 0 and line[comment - 1].isspace():
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
                    section, none, desc = line[:-1].partition('-')
                    section = section.strip()
                    desc = desc.replace('"', "").strip()
                    conf[section] = {"desc": desc}
                else:
                    if listmode:
                        if line.endswith("]"):
                            listmode = False
                            line = line.replace("]", "")

                        value += [self.cast(typ, x.strip()) for x in line.split(",") if x]

                        if not listmode:
                            conf[section][option] = {"desc": desc,
                                                     "type": typ,
                                                     "value": value}


                    else:
                        m = self.CONFLINE.search(line)

                        typ = m.group('T')
                        option = m.group('N')
                        desc = m.group('D').strip()
                        value = m.group('V').strip()

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
                            conf[section][option] = {"desc": desc,
                                                     "type": typ,
                                                     "value": value}

            except Exception, e:
                print "Config Warning:"
                print line
                print_exc()

        f.close()
        return conf


    def updateValues(self, config, dest):
        """sets the config values from a parsed config file to values in destination"""

        for section in config.iterkeys():
            if section in dest:
                for option in config[section].iterkeys():
                    if option in ("desc", "outline"): continue

                    if option in dest[section]:
                        dest[section][option]["value"] = config[section][option]["value"]

                        #else:
                        #    dest[section][option] = config[section][option]


                        #else:
                        #    dest[section] = config[section]

    def saveConfig(self, config, filename):
        """saves config to filename"""
        with open(filename, "wb") as f:
            chmod(filename, 0600)
            f.write("version: %i \n" % CONF_VERSION)
            for section in sorted(config.iterkeys()):
                f.write('\n%s - "%s":\n' % (section, config[section]["desc"]))

                for option, data in sorted(config[section].items(), key=lambda _x: _x[0]):
                    if option in ("desc", "outline"):
                        continue

                    if isinstance(data["value"], list):
                        value = "[ \n"
                        for x in data["value"]:
                            value += "\t\t" + str(x) + ",\n"
                        value += "\t\t]\n"
                    else:
                        if type(data["value"]) in (str, unicode):
                            value = data["value"] + "\n"
                        else:
                            value = str(data["value"]) + "\n"
                    try:
                        f.write('\t%s %s : "%s" = %s' % (data["type"], option, data["desc"], value))
                    except UnicodeEncodeError:
                        f.write('\t%s %s : "%s" = %s' % (data["type"], option, data["desc"], value.encode("utf8")))

    def cast(self, typ, value):
        """cast value to given format"""
        if type(value) not in (str, unicode):
            return value

        elif typ == "int":
            return int(value)
        elif typ == "bool":
            return True if value.lower() in ("1", "true", "on", "an", "yes") else False
        elif typ == "time":
            if not value: value = "0:00"
            if not ":" in value: value += ":00"
            return value
        elif typ in ("str", "file", "folder"):
            try:
                return value.encode("utf8")
            except:
                return value
        else:
            return value


    def save(self):
        """saves the configs to disk"""

        self.saveConfig(self.config, "pyload.conf")
        self.saveConfig(self.plugin, "plugin.conf")


    def __getitem__(self, section):
        """provides dictonary like access: c['section']['option']"""
        return Section(self, section)


    def get(self, section, option):
        """get value"""
        val = self.config[section][option]["value"]
        try:
            if type(val) in (str, unicode):
                return val.decode("utf8")
            else:
                return val
        except:
            return val

    def set(self, section, option, value):
        """set value"""

        value = self.cast(self.config[section][option]["type"], value)

        self.config[section][option]["value"] = value
        self.save()

    def getPlugin(self, plugin, option):
        """gets a value for a plugin"""
        val = self.plugin[plugin][option]["value"]
        try:
            if type(val) in (str, unicode):
                return val.decode("utf8")
            else:
                return val
        except:
            return val

    def setPlugin(self, plugin, option, value):
        """sets a value for a plugin"""

        value = self.cast(self.plugin[plugin][option]["type"], value)

        if self.pluginCB:
            self.pluginCB(plugin, option, value)

        self.plugin[plugin][option]["value"] = value
        self.save()

    def getMetaData(self, section, option):
        """ get all config data for an option """
        return self.config[section][option]

    def addPluginConfig(self, name, config, outline=""):
        """adds config options with tuples (name, type, desc, default)"""
        if name not in self.plugin:
            conf = {"desc": name,
                    "outline": outline}
            self.plugin[name] = conf
        else:
            conf = self.plugin[name]
            conf["outline"] = outline

        for item in config:
            if item[0] in conf and item[1] == conf[item[0]]["type"]:
                conf[item[0]]["desc"] = item[2]
            else:
                conf[item[0]] = {
                    "desc": item[2],
                    "type": item[1],
                    "value": self.cast(item[1], item[3])
                }

        values = [x[0] for x in config] + ["desc", "outline"]
        #delete old values
        for item in conf.keys():
            if item not in values:
                del conf[item]

    def deleteConfig(self, name):
        """Removes a plugin config"""
        if name in self.plugin:
            del self.plugin[name]


    def deleteOldPlugins(self):
        """ remove old plugins from config """
        for name in IGNORE:
            if name in self.plugin:
                del self.plugin[name]



class Section:
    """provides dictionary like access for configparser"""

    def __init__(self, parser, section):
        """Constructor"""
        self.parser = parser
        self.section = section

    def __getitem__(self, item):
        """getitem"""
        return self.parser.get(self.section, item)

    def __setitem__(self, item, value):
        """setitem"""
        self.parser.set(self.section, item, value)


if __name__ == "__main__":
    pypath = ""

    from time import time

    a = time()

    c = ConfigParser()

    b = time()

    print "sec", b - a

    print c.config

    c.saveConfig(c.config, "user.conf")
