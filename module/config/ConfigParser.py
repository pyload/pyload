# -*- coding: utf-8 -*-

from __future__ import with_statement
from time import sleep
from os.path import exists
from gettext import gettext
from new_collections import namedtuple, OrderedDict

from module.utils import from_string
from module.utils.fs import chmod

from default import make_config

CONF_VERSION = 2
SectionTuple = namedtuple("SectionTuple", "name description long_desc config")
ConfigData = namedtuple("ConfigData", "name type description default")

class ConfigParser:
    """
    Holds and manages the configuration + meta data for core and every user.
    """

    CONFIG = "pyload.conf"
    PLUGIN = "plugin.conf"

    def __init__(self):
        """Constructor"""

        # core config sections from pyload
        self.baseSections = []

        # Meta data information
        self.config = OrderedDict()
        # The actual config values
        self.values = {}

        self.changeCB = None # callback when config value was changed

        self.checkVersion()

        self.loadDefault()
        self.parseValues(self.CONFIG)

    def loadDefault(self):
        make_config(self)

    def checkVersion(self):
        """Determines if config needs to be deleted"""
        e = None
        # workaround conflict, with GUI (which also accesses the config) so try read in 3 times
        for i in range(0, 3):
            try:
                for conf in (self.CONFIG, self.PLUGIN):
                    if exists(conf):
                        f = open(conf, "rb")
                        v = f.readline()
                        f.close()
                        v = v[v.find(":") + 1:].strip()

                        if not v or int(v) < CONF_VERSION:
                            f = open(conf, "wb")
                            f.write("version: " + str(CONF_VERSION))
                            f.close()
                            print "Old version of %s deleted" % conf
                    else:
                        f = open(conf, "wb")
                        f.write("version:" + str(CONF_VERSION))
                        f.close()

            except Exception, ex:
                e = ex
                sleep(0.3)
        if e: raise e


    def parseValues(self, filename):
        """read config values from file"""
        f = open(filename, "rb")
        config = f.readlines()[1:]

        # save the current section
        section = ""

        for line in config:
            line = line.strip()

            # comment line, different variants
            if not line or line.startswith("#") or line.startswith("//") or line.startswith(";"): continue

            if line.startswith("["):
                section = line.replace("[", "").replace("]", "")

                if section not in self.config:
                    print "Unrecognized section", section
                    section = ""

            else:
                name, non, value = line.rpartition("=")
                name = name.strip()
                value = value.strip()

                if not section:
                    print "Value without section", name
                    continue

                if name in self.config[section].config:
                    self.set(section, name, value, sync=False)
                else:
                    print "Unrecognized option", section, name


    def save(self):
        """saves config to filename"""

        # separate pyload and plugin conf
        configs = []
        for c in (self.CONFIG, self.PLUGIN):
            f = open(c, "wb")
            configs.append(f)
            chmod(c, 0600)
            f.write("version: %i\n\n" % CONF_VERSION)


        # write on 2 files
        for section, data in self.config.iteritems():
            f = configs[0] if section in self.baseSections else configs[1]

            f.write("[%s]\n" % section)

            for option, data in data.config.iteritems():
                value = self.get(section, option)
                if type(value) == unicode: value = value.encode("utf8")
                else: value = str(value)

                f.write('%s = %s\n' % (option, value))

            f.write("\n")

        [f.close() for f in configs]

    def __getitem__(self, section):
        """provides dictionary like access: c['section']['option']"""
        return Section(self, section)

    def get(self, section, option):
        """get value"""
        if option in self.values[section]:
            return self.values[section][option]
        else:
            return self.config[section].config[option].default

    def set(self, section, option, value, sync=True):
        """set value"""

        data = self.config[section].config[option]
        value = from_string(value, data.type)

        # only save when different to default values
        if value != data.default or (option in self.values[section] and value != self.values[section][option]):
            self.values[section][option] = value
            if sync:
                if self.changeCB: self.changeCB(section, option, value)
                self.save()

    def getPlugin(self, *args):
        """gets a value for a plugin"""
        ret = self.get(*args)
        print "Deprecated method getPlugin%s -> %s" % (str(args), ret)
        return ret

    def setPlugin(self, *args):
        """sets a value for a plugin"""
        print "Deprecated method setPlugin%s" % str(args)
        self.set(*args)

    def getMetaData(self, section, option):
        """ get all config data for an option """
        return self.config[section].config[option]

    def getBaseSections(self):
        for section, data in self.config.iteritems():
            if section in self.baseSections:
                yield section, data
        return

    def getPluginSections(self):
        for section, data in self.config.iteritems():
            if section not in self.baseSections:
                yield section, data
        return

    def addConfigSection(self, section, name, desc, long_desc, config, base=False):
        """Adds a section to the config. `config` is a list of config tuples as used in plugin api defined as:
        Either (name, type, verbose_name, default_value) or
                (name, type, verbose_name, short_description, default_value)
        The order of the config elements is preserved with OrderedDict
        """
        d = OrderedDict()

        for entry in config:
            if len(entry) == 5:
                conf_name, type, conf_desc, conf_verbose, default = entry
            else: # config options without tooltip / description
                conf_name, type, conf_desc, default = entry
                conf_verbose = ""

            d[conf_name] = ConfigData(gettext(conf_desc), type, gettext(conf_verbose), from_string(default, type))

        if base:
            if section not in self.baseSections: self.baseSections.append(section)
        elif section in self.baseSections:
            return # would overwrite base section

        data = SectionTuple(gettext(name), gettext(desc), gettext(long_desc), d)
        self.config[section] = data

        if section not in self.values:
            self.values[section] = {}

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
