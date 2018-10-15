# -*- coding: utf-8 -*-

import os
import re
import shutil
import traceback
from builtins import object, PKGDIR, str, HOMEDIR
import time

from pyload.utils.utils import chmod


# CONFIG_VERSION
__version__ = 1


class ConfigParser(object):
    """
    holds and manage the configuration.

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

    CONFLINE = re.compile(
        r'^\s*(?P<T>.+?)\s+(?P<N>[^ ]+?)\s*:\s*"(?P<D>.+?)"\s*=\s?(?P<V>.*)'
    )
    VERSION = re.compile(r'version\s*:\s*(\d+)')

    def __init__(self):
        """
        Constructor.
        """
        self.config = {}  # the config values
        self.plugin = {}  # the config for plugins

        self.configpath = os.path.join(HOMEDIR, '.pyload', "pyload.conf")
        self.pluginpath = os.path.join(HOMEDIR, '.pyload', "plugins.conf")

        self.oldRemoteData = {}

        self.pluginCB = None  # callback when plugin config value is changed

        self.checkVersion()

        self.readConfig()

    def checkVersion(self, n=0):
        """
        determines if config need to be copied.
        """
        try:
            if not os.path.exists(self.configpath):
                os.makedirs(os.path.dirname(self.configpath), exist_ok=True)                
                shutil.copy(
                    os.path.join(PKGDIR, "config", "default.conf"),
                    self.configpath,
                )
                chmod(self.configpath, 0o600)

            if not os.path.exists(self.pluginpath):
                os.makedirs(os.path.dirname(self.pluginpath), exist_ok=True)  
                with open(self.pluginpath, "wb") as f:
                    f.write("version: " + str(__version__))
                chmod(self.pluginpath, 0o600)

            with open(self.configpath, "rb") as f:
                content = f.read()
                
            version = self.VERSION.findall(content)
            if not version or int(version) < __version__:
                shutil.copy(
                    os.path.join(PKGDIR, "config", "default.conf"),
                    self.configpath,
                )
                print("Old version of config was replaced")

            with open(self.pluginpath, "rb") as f:
                content = f.read()

            version = self.VERSION.findall(content)
            if not version or int(version) < __version__:
                with open(self.pluginpath, "wb") as f:
                    f.write("version: " + str(__version__))

                print("Old version of plugin-config replaced")
                
        except Exception:
            if n < 3:
                time.sleep(1)
                self.checkVersion(n + 1)
            else:
                raise

    def readConfig(self):
        """
        reads the config file.
        """

        self.config = self.parseConfig(
            os.path.join(PKGDIR, "config", "default.conf")
        )
        self.plugin = self.parseConfig(self.pluginpath)

        try:
            homeconf = self.parseConfig(self.configpath)
            if "username" in homeconf["remote"]:
                if "password" in homeconf["remote"]:
                    self.oldRemoteData = {
                        "username": homeconf["remote"]["username"]["value"],
                        "password": homeconf["remote"]["username"]["value"],
                    }
                    del homeconf["remote"]["password"]
                del homeconf["remote"]["username"]
            self.updateValues(homeconf, self.config)

        except Exception as e:
            print("Config Warning")
            traceback.print_exc()

    def parseConfig(self, config):
        """
        parses a given configfile.
        """

        with open(config) as f:

            config = f.read()

            config = config.splitlines()[1:]

            conf = {}

            section, option, value, typ, desc = "", "", "", "", ""

            listmode = False

            for line in config:
                comment = line.rfind("#")
                if (
                    line.find(":", comment) < 0 > line.find("=", comment)
                    and comment > 0
                    and line[comment - 1].isspace()
                ):
                    line = line.rpartition("#")  # removes comments
                    if line[1]:
                        line = line[0]
                    else:
                        line = line[2]

                line = line.strip()

                try:
                    if line == "":
                        continue
                    elif line.endswith(":"):
                        section, none, desc = line[:-1].partition("-")
                        section = section.strip()
                        desc = desc.replace('"', "").strip()
                        conf[section] = {"desc": desc}
                    else:
                        if listmode:
                            if line.endswith("]"):
                                listmode = False
                                line = line.replace("]", "")

                            value += [
                                self.cast(typ, x.strip()) for x in line.split(",") if x
                            ]

                            if not listmode:
                                conf[section][option] = {
                                    "desc": desc,
                                    "type": typ,
                                    "value": value,
                                }

                        else:
                            m = self.CONFLINE.search(line)

                            typ = m.group("T")
                            option = m.group("N")
                            desc = m.group("D").strip()
                            value = m.group("V").strip()

                            if value.startswith("["):
                                if value.endswith("]"):
                                    listmode = False
                                    value = value[:-1]
                                else:
                                    listmode = True

                                value = [
                                    self.cast(typ, x.strip())
                                    for x in value[1:].split(",")
                                    if x
                                ]
                            else:
                                value = self.cast(typ, value)

                            if not listmode:
                                conf[section][option] = {
                                    "desc": desc,
                                    "type": typ,
                                    "value": value,
                                }

                except Exception as e:
                    print("Config Warning:")
                    print(line)
                    traceback.print_exc()

        return conf

    def updateValues(self, config, dest):
        """
        sets the config values from a parsed config file to values in
        destination.
        """

        for section in config.keys():
            if section in dest:
                for option in config[section].keys():
                    if option in ("desc", "outline"):
                        continue

                    if option in dest[section]:
                        dest[section][option]["value"] = config[section][option][
                            "value"
                        ]

                        # else:
                        #    dest[section][option] = config[section][option]

                        # else:
                        #    dest[section] = config[section]

    def saveConfig(self, config, filename):
        """
        saves config to filename.
        """
        with open(filename, "wb") as f:
            chmod(filename, 0o600)
            f.write("version: {} \n".format(__version__))
            for section in sorted(config.keys()):
                f.write('\n{} - "{}":\n'.format(section, config[section]["desc"]))

                for option, data in sorted(
                    list(config[section].items()), key=lambda _x: _x[0]
                ):
                    if option in ("desc", "outline"):
                        continue

                    if isinstance(data["value"], list):
                        value = "[ \n"
                        for x in data["value"]:
                            value += "\t\t" + str(x) + ",\n"
                        value += "\t\t]\n"
                    else:
                        if type(data["value"]) in (str, bytes):
                            value = data["value"] + "\n"
                        else:
                            value = str(data["value"]) + "\n"
                    try:
                        f.write(
                            '\t{} {} : "{}" = {}'.format(
                                data["type"], option, data["desc"], value
                            )
                        )
                    except UnicodeEncodeError:
                        f.write(
                            '\t{} {} : "{}" = {}'.format(
                                data["type"], option, data["desc"], value.encode("utf8")
                            )
                        )

    def cast(self, typ, value):
        """
        cast value to given format.
        """
        if type(value) not in (str, bytes):
            return value

        elif typ == "int":
            return int(value)
        elif typ == "bool":
            return value.lower() in ("1", "true", "on", "yes", "y")
        elif typ == "time":
            if not value:
                value = "0:00"
            if ":" not in value:
                value += ":00"
            return value
        elif typ in ("str", "file", "folder"):
            try:
                return value.encode("utf8")
            except Exception:
                return value
        else:
            return value

    def save(self):
        """
        saves the configs to disk.
        """

        self.saveConfig(self.config, self.configpath)
        self.saveConfig(self.plugin, self.pluginpath)

    def __getitem__(self, section):
        """
        provides dictonary like access: c['section']['option']
        """
        return Section(self, section)

    def get(self, section, option):
        """
        get value.
        """
        val = self.config[section][option]["value"]
        try:
            if type(val) in (str, bytes):
                return val.decode("utf8")
            else:
                return val
        except Exception:
            return val

    def set(self, section, option, value):
        """
        set value.
        """

        value = self.cast(self.config[section][option]["type"], value)

        self.config[section][option]["value"] = value
        self.save()

    def toggle(self, section, option):
        self.set(section, option, self.get(section, option) ^ True)

    def getPlugin(self, plugin, option):
        """
        gets a value for a plugin.
        """
        val = self.plugin[plugin][option]["value"]
        try:
            if type(val) in (str, bytes):
                return val.decode("utf8")
            else:
                return val
        except Exception:
            return val

    def setPlugin(self, plugin, option, value):
        """
        sets a value for a plugin.
        """

        value = self.cast(self.plugin[plugin][option]["type"], value)

        if self.pluginCB:
            self.pluginCB(plugin, option, value)

        self.plugin[plugin][option]["value"] = value
        self.save()

    def getMetaData(self, section, option):
        """
        get all config data for an option.
        """
        return self.config[section][option]

    def addPluginConfig(self, name, config, outline=""):
        """
        adds config options with tuples (name, type, desc, default)
        """
        if name not in self.plugin:
            conf = {"desc": name, "outline": outline}
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
                    "value": self.cast(item[1], item[3]),
                }

        values = [x[0] for x in config] + ["desc", "outline"]
        # delete old values
        for item in conf.keys():
            if item not in values:
                del conf[item]

    def deleteConfig(self, name):
        """
        Removes a plugin config.
        """
        if name in self.plugin:
            del self.plugin[name]


class Section(object):
    """
    provides dictionary like access for configparser.
    """

    def __init__(self, parser, section):
        """
        Constructor.
        """
        self.parser = parser
        self.section = section

    def __getitem__(self, item):
        """
        getitem.
        """
        return self.parser.get(self.section, item)

    def __setitem__(self, item, value):
        """
        setitem.
        """
        self.parser.set(self.section, item, value)
