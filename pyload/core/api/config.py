# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from future import standard_library
standard_library.install_aliases()

from pyload.utils.convert import to_str

from ..datatype.init import ConfigHolder, ConfigInfo, ConfigItem, Permission
from .base import BaseApi
from .init import Api, requireperm


# @TODO: Recheck...
# helper function to create a ConfigHolder
def to_config_holder(section, config, values):
    holder = ConfigHolder(section, config.label,
                          config.description, config.explanation)
    holder.items = [ConfigItem(option, x.label, x.description, x.input,
                               to_str(values.get(option, x.input.default_value), values.get(option, x.input.default_value))) for option, x in
                    config.config.items()]
    return holder


class ConfigApi(BaseApi):
    """
    Everything related to configuration.
    """
    __slots__ = []

    def get_config_value(self, section, option):
        """
        Retrieve config value.

        :param section: name of category, or plugin
        :param option: config option
        :rtype: str
        :return: config value as string
        """
        value = self.pyload.config.get(section, option, self.primary_uid)
        return to_str(value, value)

    def set_config_value(self, section, option, value):
        """
        Set new config value.

        :param section:
        :param option:
        :param value: new config value
        """
        self.pyload.config.set(section, option, value, self.primary_uid)

    def get_config(self):
        """
        Retrieves complete config of core.

        :rtype: dict of section -> ConfigHolder
        """
        data = {}
        for section, config, values in self.pyload.config.iter_core_sections():
            data[section] = to_config_holder(section, config, values)
        return data

    def get_core_config(self):
        """
        Retrieves core config sections

        :rtype: list of PluginInfo
        """
        return [ConfigInfo(section, config.label, config.description, False, False)
                for section, config, values in self.pyload.config.iter_core_sections()]

    @requireperm(Permission.Plugins)
    def get_plugin_config(self):
        """
        All plugins and addons the current user has configured

        :rtype: list of PluginInfo
        """

        # TODO: include addons that are activated by default
        # TODO: multi user
        # TODO: better plugin / addon activated config
        data = []
        active = [x.get_name() for x in self.pyload.adm.active_plugins()]
        for name, config, values in self.pyload.config.iter_sections(
                self.primary_uid):
            # skip unmodified and inactive addons
            if not values and name not in active:
                continue

            item = ConfigInfo(name, config.label, config.description,
                              self.pyload.pgm.get_category(name),
                              self.pyload.pgm.is_user_plugin(name),
                              # TODO: won't work probably
                              values.get("activated",
                                         None if "activated" not in config.config else config.config['activated'].input.default_value))
            data.append(item)

        return data

    @requireperm(Permission.Plugins)
    def get_available_plugins(self):
        """
        List of all available plugins, that are configurable

        :rtype: list of PluginInfo
        """

        # TODO: filter user_context / addons when not allowed
        plugins = [ConfigInfo(name, config.label, config.description,
                              self.pyload.pgm.get_category(name),
                              self.pyload.pgm.is_user_plugin(name))
                   for name, config, values in self.pyload.config.iter_sections(self.primary_uid)]

        return plugins

    @requireperm(Permission.Plugins)
    def load_config(self, name):
        """
        Get complete config options for desired section

        :param name: Name of plugin or config section
        :rtype: ConfigHolder
        """

        # requires at least plugin permissions, but only admin can load core
        # config
        config, values = self.pyload.config.get_section(name, self.primary_uid)
        return to_config_holder(name, config, values)

    @requireperm(Permission.Plugins)
    def save_config(self, config):
        """
        Used to save a configuration, core config can only be saved by admins

        :param config: :class:`ConfigHolder`
        """
        for item in config.items:
            self.pyload.config.set(
                config.name, item.name, item.value, sync=False, user=self.primary_uid)
            # save the changes
        self.pyload.config.save_values(self.primary_uid, config.name)

    @requireperm(Permission.Plugins)
    def delete_config(self, plugin):
        """
        Deletes modified config

        :param plugin: plugin name
        """

        # TODO: delete should deactivate addons?
        self.pyload.config.delete(plugin, self.primary_uid)
