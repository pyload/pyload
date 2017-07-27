# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from future import standard_library

from .base import BaseApi

standard_library.install_aliases()


class ConfigApi(BaseApi):
    """
    Everything related to configuration.
    """
    def get_config_value(self, section, option):
        """
        Retrieve config value.

        :param section: name of category, or plugin
        :param option: config option
        :rtype: str
        :return: config value as string
        """
        return self.pyload_core.config.get(section, option)

    def set_config_value(self, section, option, value):
        """
        Set new config value.

        :param section:
        :param option:
        :param value: new config value
        """
        self.pyload_core.config.set(section, option, value)

    # def get_config(self):
        # """
        # Retrieves complete config of core.

        # :rtype: dict of section -> ConfigHolder
        # """
        # data = {}
        # for section, config, values in self.pyload_core.config.iter_core_sections():
        # data[section] = to_config_holder(section, config, values)
        # return data

    # def get_core_config(self):
        # """
        # Retrieves core config sections

        # :rtype: list of PluginInfo
        # """
        # return [ConfigInfo(section, config.label, config.description, False, False)
        # for section, config, values in
        # self.pyload_core.config.iter_core_sections()]

    # @requireperm(Permission.Plugins)
    # def get_plugin_config(self):
        # """
        # All plugins and addons the current user has configured

        # :rtype: list of PluginInfo
        # """
        # # TODO: include addons that are activated by default
        # # TODO: multi user
        # # TODO: better plugin / addon activated config
        # data = []
        # active = [x.get_name() for x in self.pyload_core.adm.active_plugins()]
        # for name, config, values in self.pyload_core.config.iter_sections():
        # # skip unmodified and inactive addons
        # if not values and name not in active:
        # continue

        # item = ConfigInfo(name, config.label, config.description,
        # self.pyload_core.pgm.get_category(name),
        # self.pyload_core.pgm.is_user_plugin(name),
        # # TODO: won't work probably
        # values.get("activated",
        # None if "activated" not in config.config else config.config['activated'].input.default))
        # data.append(item)

        # return data

    # @requireperm(Permission.Plugins)
    # def get_available_plugins(self):
        # """
        # List of all available plugins, that are configurable

        # :rtype: list of PluginInfo
        # """
        # # TODO: filter user_context / addons when not allowed
        # plugins = [ConfigInfo(name, config.label, config.description,
        # self.pyload_core.pgm.get_category(name),
        # self.pyload_core.pgm.is_user_plugin(name))
        # for name, config, values in self.pyload_core.config.iter_sections()]

        # return plugins

    # @requireperm(Permission.Plugins)
    # def load_config(self, name):
        # """
        # Get complete config options for desired section

        # :param name: Name of plugin or config section
        # :rtype: ConfigHolder
        # """
        # # requires at least plugin permissions, but only admin can load core
        # # config
        # config, values = self.pyload_core.config.get_section(name)
        # return to_config_holder(name, config, values)

    # @requireperm(Permission.Plugins)
    # def save_config(self, config):
        # """
        # Used to save a configuration, core config can only be saved by admins

        # :param config: :class:`ConfigHolder`
        # """
        # for item in config.items:
        # self.pyload_core.config.set(config.name, item.name, item.value, store=False)
        # # save the changes
        # self.pyload_core.config.store()

    # # NOTE: No delete method in ConfigParser, maybe in ConfigManager...
    # @requireperm(Permission.Plugins)
    # def delete_config(self, plugin):
        # """
        # Deletes modified config

        # :param plugin: plugin name
        # """
        # TODO: delete should deactivate addons?
        # self.pyload_core.config.delete(plugin)
