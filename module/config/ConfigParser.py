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
    Holds and manages the configuration + meta data for config read from file.
    """

    CONFIG = "pyload.conf"

    def __init__(self, config=None):

        if config: self.CONFIG = config

        # Meta data information
        self.config = OrderedDict()
        # The actual config values
        self.values = {}

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
                if exists(self.CONFIG):
                    f = open(self.CONFIG, "rb")
                    v = f.readline()
                    f.close()
                    v = v[v.find(":") + 1:].strip()

                    if not v or int(v) < CONF_VERSION:
                        f = open(self.CONFIG, "wb")
                        f.write("version: " + str(CONF_VERSION))
                        f.close()
                        print "Old version of %s deleted" % self.CONFIG
                else:
                    f = open(self.CONFIG, "wb")
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

        configs = []
        f = open(self.CONFIG, "wb")
        configs.append(f)
        chmod(self.CONFIG, 0600)
        f.write("version: %i\n\n" % CONF_VERSION)

        for section, data in self.config.iteritems():
            f.write("[%s]\n" % section)

            for option, data in data.config.iteritems():
                value = self.get(section, option)
                if type(value) == unicode: value = value.encode("utf8")
                else: value = str(value)

                f.write('%s = %s\n' % (option, value))

            f.write("\n")

        f.close()

    def __getitem__(self, section):
        """provides dictionary like access: c['section']['option']"""
        return Section(self, section)

    def __contains__(self, section):
        """ checks if parser contains section """
        return section in self.config

    def get(self, section, option):
        """get value or default"""
        try:
            return self.values[section][option]
        except KeyError:
            return self.config[section].config[option].default

    def set(self, section, option, value, sync=True):
        """set value"""

        data = self.config[section].config[option]
        value = from_string(value, data.type)
        old_value = self.get(section, option)

        # only save when different values
        if value != old_value:
            if section not in self.values: self.values[section] = {}
            self.values[section][option] = value
            if sync:
                self.save()
            return True

        return False

    def getMetaData(self, section, option):
        """ get all config data for an option """
        return self.config[section].config[option]

    def iterSections(self):
        """ Yields section, config info, values, for all sections """

        for name, config in self.config.iteritems():
            yield name, config, self.values[name] if name in self.values else {}

    def addConfigSection(self, section, name, desc, long_desc, config):
        """Adds a section to the config. `config` is a list of config tuples as used in plugin api defined as:
        The order of the config elements is preserved with OrderedDict
        """
        d = OrderedDict()

        for entry in config:
            if len(entry) == 5:
                conf_name, type, conf_desc, conf_verbose, default = entry
            else: # config options without description
                conf_name, type, conf_desc, default = entry
                conf_verbose = ""

            d[conf_name] = ConfigData(gettext(conf_desc), type, gettext(conf_verbose), from_string(default, type))

        data = SectionTuple(gettext(name), gettext(desc), gettext(long_desc), d)
        self.config[section] = data

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
