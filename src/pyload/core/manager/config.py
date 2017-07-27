# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import json

from future import standard_library

from pyload.config import ConfigParser
# from pyload.config.convert import from_string
from pyload.utils.layer.legacy.collections_ import OrderedDict

from pyload.core.datatype.init import InvalidConfigSection

standard_library.install_aliases()


def convertkeyerror(func):
    """
    Converts KeyError into InvalidConfigSection.
    """
    def conv(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            raise InvalidConfigSection(args[1])

    return conv


class ConfigManager(ConfigParser):
    """
    Manages the core config and configs for addons and single user.
    Has similar interface to ConfigParser.
    """
    def __init__(self, core, parser):
        # No __init__ call to super class is needed!

        self.__pyload = core

        # The config parser, holding the core config
        self.__parser = parser

        # similar to parser, separated meta data and values
        self.config = OrderedDict()

        # Value cache for multiple user configs
        # Values are populated from db on first access
        # Entries are saved as (user, section) keys
        self.values = {}
        # TODO: similar to a cache, could be deleted periodically

    def save(self):
        self.__parser.store()

    @property
    def pyload_core(self):
        return self.__pyload

    @convertkeyerror
    def get(self, section, option, user=None):
        """
        Get config value, core config only available for admins.
        if user is not valid default value will be returned.
        """
        # Core config loaded from parser, when no user is given or he is admin
        if section in self.__parser and user is None:
            return self.__parser.get(section, option)
        else:
            # We need the id and not the instance
            # Will be None for admin user and so the same as internal access
            try:
                # Check if this config exists
                # Configs without meta data can not be loaded!
                assert self.config[section].config[option]
                return self.load_values(user, section)[option]
            except KeyError:
                pass  # Returns default value later

        return self.config[section].config[option].input.default

    def load_values(self, user, section):
        if (user, section) not in self.values:
            conf = self.pyload_core.db.load_config(section, user)
            try:
                self.values[user, section] = json.loads(conf) if conf else {}
            except ValueError:  # Something did go wrong when parsing
                self.values[user, section] = {}
                # self.pyload_core.print_exc()

        return self.values[user, section]

    @convertkeyerror
    def set(self, section, option, value, sync=True, user=None):
        """
        Set config value.
        """
        changed = False
        if section in self.__parser and user is None:
            changed = self.__parser.set(section, option, value, sync)
        else:
            data = self.config[section].config[option]
            value = from_string(value, data.input.type)
            old_value = self.get(section, option)

            # Values will always be saved to db, sync is ignored
            if value != old_value:
                changed = True
                self.values[user, section][option] = value
                if sync:
                    self.save_values(user, section)

        if changed:
            self.pyload_core.evm.fire("config:changed", section, option, value)
        return changed

    def save_values(self, user, section):
        if section in self.__parser and user is None:
            self.save()
        elif (user, section) in self.values:
            self.pyload_core.db.save_config(section, json.dumps(
                self.values[user, section]), user)

    def delete(self, section, user=None):
        """
        Deletes values saved in db and cached values for given user,
        NOT meta data.
        Does not trigger an error when nothing was deleted.
        """
        if (user, section) in self.values:
            del self.values[user, section]

        self.pyload_core.db.delete_config(section, user)
        self.pyload_core.evm.fire("config:deleted", section, user)

    # def iter_core_sections(self):
        # return self.__parser.iter_sections()

    def iter_sections(self, user=None):
        """
        Yields: section, metadata, values.
        """
        values = self.pyload_core.db.load_configs_for_user(user)

        # Every section needs to be json decoded
        for section, data in values.items():
            try:
                values[section] = json.loads(data) if data else {}
            except ValueError:
                values[section] = {}
                # self.pyload_core.print_exc()

        for name, config in self.config.items():
            yield name, config, values[name] if name in values else {}

    def get_section(self, section, user=None):
        if section in self.__parser and user is None:
            return self.__parser.get_section(section)

        values = self.load_values(user, section)
        return self.config.get(section), values
