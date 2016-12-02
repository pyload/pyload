#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyload.Api import Api, RequirePerm, Permission, ConfigHolder, ConfigItem, ConfigInfo
from pyload.utils import to_string

from ApiComponent import ApiComponent

# helper function to create a ConfigHolder
def toConfigHolder(section, config, values):
    holder = ConfigHolder(section, config.label, config.description, config.explanation)
    holder.items = [ConfigItem(option, x.label, x.description, x.input,
                               to_string(values.get(option, x.input.default_value))) for option, x in
                    config.config.iteritems()]
    return holder


class ConfigApi(ApiComponent):
    """ Everything related to configuration """

    def getConfigValue(self, section, option):
        """Retrieve config value.

        :param section: name of category, or plugin
        :param option: config option
        :rtype: str
        :return: config value as string
        """
        value = self.core.config.get(section, option, self.primaryUID)
        return to_string(value)

    def setConfigValue(self, section, option, value):
        """Set new config value.

        :param section:
        :param option:
        :param value: new config value
        """
        self.core.config.set(section, option, value, self.primaryUID)

    def getConfig(self):
        """Retrieves complete config of core.

        :rtype: dict of section -> ConfigHolder
        """
        data = {}
        for section, config, values in self.core.config.iterCoreSections():
            data[section] = toConfigHolder(section, config, values)
        return data

    def getCoreConfig(self):
        """ Retrieves core config sections

        :rtype: list of PluginInfo
        """
        return [ConfigInfo(section, config.label, config.description, False, False)
                for section, config, values in self.core.config.iterCoreSections()]

    @RequirePerm(Permission.Plugins)
    def getPluginConfig(self):
        """All plugins and addons the current user has configured

        :rtype: list of PluginInfo
        """
        # TODO: include addons that are activated by default
        # TODO: multi user
        # TODO: better plugin / addon activated config
        data = []
        active = [x.getName() for x in self.core.addonManager.activePlugins()]
        for name, config, values in self.core.config.iterSections(self.primaryUID):
            # skip unmodified and inactive addons
            if not values and name not in active: continue

            item = ConfigInfo(name, config.label, config.description,
                              self.core.pluginManager.getCategory(name),
                              self.core.pluginManager.isUserPlugin(name),
                              # TODO: won't work probably
                              values.get("activated", None if "activated" not in config.config else config.config[
                                  "activated"].input.default_value))
            data.append(item)

        return data

    @RequirePerm(Permission.Plugins)
    def getAvailablePlugins(self):
        """List of all available plugins, that are configurable

        :rtype: list of PluginInfo
        """
        # TODO: filter user_context / addons when not allowed
        plugins = [ConfigInfo(name, config.label, config.description,
                              self.core.pluginManager.getCategory(name),
                              self.core.pluginManager.isUserPlugin(name))
                   for name, config, values in self.core.config.iterSections(self.primaryUID)]

        return plugins

    @RequirePerm(Permission.Plugins)
    def loadConfig(self, name):
        """Get complete config options for desired section

        :param name: Name of plugin or config section
        :rtype: ConfigHolder
        """
        # requires at least plugin permissions, but only admin can load core config
        config, values = self.core.config.getSection(name, self.primaryUID)
        return toConfigHolder(name, config, values)


    @RequirePerm(Permission.Plugins)
    def saveConfig(self, config):
        """Used to save a configuration, core config can only be saved by admins

        :param config: :class:`ConfigHolder`
        """
        for item in config.items:
            self.core.config.set(config.name, item.name, item.value, sync=False, user=self.primaryUID)
            # save the changes
        self.core.config.saveValues(self.primaryUID, config.name)

    @RequirePerm(Permission.Plugins)
    def deleteConfig(self, plugin):
        """Deletes modified config

        :param plugin: plugin name
        """
        #TODO: delete should deactivate addons?
        self.core.config.delete(plugin, self.primaryUID)


if Api.extend(ConfigApi):
    del ConfigApi
