# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, unicode_literals,
                        with_statement)

import io
import os
import re
from builtins import int, object, str
from gettext import gettext

from future import standard_library

from pyload.utils import convert
from pyload.utils.layer.legacy.collections_ import OrderedDict, namedtuple
from pyload.utils.path import bufsize

from .convert import from_string, to_configdata
from .default import make_config

standard_library.install_aliases()


__all__ = ['ConfigParser', 'ConfigSection']


SectionTuple = namedtuple(
    "SectionTuple", "label description explanation config")


class ConfigParser(object):
    """
    Holds and manages the configuration + meta data for config read from file.
    """
    __slots__ = ['_RE_VERSION', 'config', 'filename', 'values', 'version']

    _RE_VERSION = re.compile(r'\s*version\s*:\s*(\d+\.\d+\.\d+)', flags=re.I)

    def __init__(self, file, version):
        self.filename = file
        self.version = convert.to_version(version, version)

        # Meta data information
        self.config = OrderedDict()
        # The actual config values
        self.values = {}

        self.check_version()

        self.load_default()
        self.parse(self.filename)

    def load_default(self):
        make_config(self)

    def check_version(self):
        """
        Determines if config needs to be deleted.
        """
        if not os.path.exists(self.filename):
            with io.open(self.filename, mode='wb') as fp:
                fp.write(
                    "version: {}".format(
                        convert.from_version(
                            self.version)))
            return None

        version = None
        try:
            with io.open(self.filename, mode='rb') as fp:
                m = self._RE_VERSION.match(fp.readline())
                version = convert.to_version(m.group(1))
        except (AttributeError, TypeError):
            pass

        if not self.version or version[:-1] != self.version[:-1]:
            os.rename(self.filename, "{}.old".format(self.filename))

        with io.open(self.filename, mode='wb') as fp:
            fp.write("version: {}".format(convert.from_version(self.version)))

    def parse(self, filename):
        """
        Read config values from file.
        """
        with io.open(filename, mode='rb') as fp:
            # save the current section
            section = ""
            fp.readline()
            for line in iter(fp.readline, ""):
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
        with io.open(self.filename, mode='wb') as fp:
            configs.append(fp)
            os.chmod(self.filename, 0o600)
            fp.write(
                "version: {}\n\n".format(
                    convert.from_version(
                        self.version)))

            for section, data in self.config.items():
                fp.write("[{}]\n".format(section))

                for option, data in data.config.items():
                    value = self.get(section, option)
                    fp.write('{} = {}\n'.format(option, value))

                fp.write("\n")

    def __getitem__(self, section):
        """
        Provides dictionary like access: c['section']['option'].
        """
        return ConfigSection(self, section)

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


class ConfigSection(object):
    """
    Provides dictionary like access for configparser.
    """
    __slots__ = ['parser', 'section']

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
