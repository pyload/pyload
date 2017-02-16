# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import int
from future import standard_library
standard_library.install_aliases()
from __future__ import (absolute_import, print_function, unicode_literals,
                        with_statement)

import io
import os
from builtins import object, str
from gettext import gettext

from pyload.config.convert import from_string, to_configdata
from pyload.config.default import make_config
from pyload.utils.lib.collections import OrderedDict, namedtuple

SectionTuple = namedtuple(
    "SectionTuple", "label description explanation config")


class Config(object):
    """
    Holds and manages the configuration + meta data for config read from file.
    """

    def __init__(self, file, version):

        self.filename = file
        self.version = version

        # Meta data information
        self.config = OrderedDict()
        # The actual config values
        self.values = {}

        self.check_version()

        self.load_default()
        self.parse_values(self.filename)

    def load_default(self):
        make_config(self)

    def check_version(self):
        """
        Determines if config needs to be deleted.
        """
        if os.path.exists(self.filename):
            with io.open(self.filename, "rb") as f:
                v = f.readline()
            v = v[v.find(":") + 1:].strip()

            if not v or int(v) < self.version:
                with io.open(self.filename, "wb") as f:
                    f.write("version: {}".format(self.version))
                print("Old version of {} deleted".format(self.filename))
        else:
            with io.open(self.filename, "wb") as f:
                f.write("version: {}".format(self.version))

    def parse_values(self, filename):
        """
        Read config values from file.
        """
        with io.open(filename, "rb") as f:
            config = f.readlines()[1:]

        # save the current section
        section = ""

        for line in config:
            line = line.strip()

            # comment line, different variants
            if not line or line.startswith("#") or line.startswith(
                    "//") or line.startswith("|"):
                continue

            if line.startswith("["):
                section = line.replace("[", "").replace("]", "")

                if section not in self.config:
                    print("Unrecognized section", section)
                    section = ""

            else:
                name, non, value = line.rpartition("=")
                name = name.strip()
                value = value.strip()

                if not section:
                    print("Value without section", name)
                    continue

                if name in self.config[section].config:
                    self.set(section, name, value, sync=False)
                else:
                    print("Unrecognized option", section, name)

    def save(self):
        """
        Saves config to filename.
        """
        configs = []
        with io.open(self.filename, "wb") as f:
            configs.append(f)
            os.chmod(self.filename, 0o600)
            f.write("version: {:d}\n\n".format(self.version))

            for section, data in self.config.items():
                f.write("[{}]\n".format(section))

                for option, data in data.config.items():
                    value = self.get(section, option)
                    if isinstance(value, str):
                        value = value.encode("utf8")
                    else:
                        value = str(value)

                    f.write('{} = {}\n'.format(option, value))

                f.write("\n")

    def __getitem__(self, section):
        """
        Provides dictionary like access: c['section']['option'].
        """
        return Section(self, section)

    def __contains__(self, section):
        """
        Checks if parser contains section.
        """
        return section in self.config

    def get(self, section, option):
        """
        Get value or default.
        """
        try:
            return self.values[section][option]
        except KeyError:
            return self.config[section].config[option].input.default_value

    def set(self, section, option, value, sync=True):
        """
        Set value.
        """
        data = self.config[section].config[option]
        value = from_string(value, data.input.type)
        old_value = self.get(section, option)

        # only save when different values
        if value != old_value:
            if section not in self.values:
                self.values[section] = {}
            self.values[section][option] = value
            if sync:
                self.save()
            return True

        return False

    def get_meta_data(self, section, option):
        """
        Get all config data for an option.
        """
        return self.config[section].config[option]

    def iter_sections(self):
        """
        Yields section, config info, values, for all sections.
        """
        for name, config in self.config.items():
            yield name, config, self.values[name] if name in self.values else {}

    def get_section(self, section):
        """
        Retrieves single config as tuple (section, values).
        """
        return self.config[section], self.values[
            section] if section in self.values else {}

    def add_config_section(self, section, label, desc, expl, config):
        """
        Adds a section to the config.
        `config` is a list of config tuple as used in plugin api defined as
        the order of the config elements is preserved with OrderedDict
        """
        d = OrderedDict()

        for entry in config:
            name, data = to_configdata(entry)
            d[name] = data

        data = SectionTuple(gettext(label), gettext(desc), gettext(expl), d)
        self.config[section] = data


class Section(object):
    """
    Provides dictionary like access for configparser.
    """

    def __init__(self, parser, section):
        """
        Constructor.
        """
        self.parser = parser
        self.section = section

    def __getitem__(self, item):
        """
        Getitem.
        """
        return self.parser.get(self.section, item)

    def __setitem__(self, item, value):
        """
        Setitem.
        """
        self.parser.set(self.section, item, value)
