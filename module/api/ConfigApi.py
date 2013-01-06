#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.Api import Api, UserContext, RequirePerm, Permission, ConfigHolder, ConfigItem, PluginInfo
from module.utils import to_string

from ApiComponent import ApiComponent

class ConfigApi(ApiComponent):
    """ Everything related to configuration """

    @UserContext
    def getConfigValue(self, section, option):
        """Retrieve config value.

        :param section: name of category, or plugin
        :param option: config option
        :rtype: str
        :return: config value as string
        """
        value = self.core.config.get(section, option, self.user)
        return to_string(value)

    @UserContext
    def setConfigValue(self, section, option, value):
        """Set new config value.

        :param section:
        :param option:
        :param value: new config value
        """
        if option in ("limit_speed", "max_speed"): #not so nice to update the limit
            self.core.requestFactory.updateBucket()

        self.core.config.set(section, option, value, self.user)

    def getConfig(self):
        """Retrieves complete config of core.

        :rtype: dict of section -> ConfigHolder
        """
        data = {}
        for section, config, values in self.core.config.iterCoreSections():
            holder = ConfigHolder(section, config.name, config.description, config.long_desc)
            holder.items = [ConfigItem(option, x.name, x.description, x.type, to_string(x.default),
                to_string(values.get(option, x.default))) for option, x in config.config.iteritems()]

            data[section] = holder
        return data

    def getCoreConfig(self):
        """ Retrieves core config sections

        :rtype: list of PluginInfo
        """
        return [PluginInfo(section, config.name, config.description, False, False)
                for section, config, values in self.core.config.iterCoreSections()]

    @UserContext
    @RequirePerm(Permission.Plugins)
    def getPluginConfig(self):
        """All plugins and addons the current user has configured

        :rtype: list of PluginInfo
        """
        # TODO: include addons that are activated by default
        data = []
        for name, config, values in self.core.config.iterSections(self.user):
            if not values: continue
            item = PluginInfo(name, config.name, config.description,
                self.core.pluginManager.isPluginType(name, "addons"),
                self.core.pluginManager.isUserPlugin(name),
                values.get("activated", False))
            data.append(item)

        return data

    @UserContext
    @RequirePerm(Permission.Plugins)
    def getAvailablePlugins(self):
        """List of all available plugins, that are configurable

        :rtype: list of PluginInfo
        """
        # TODO: filter user_context / addons when not allowed
        return [PluginInfo(name, config.name, config.description,
            self.core.pluginManager.isPluginType(name, "addons"),
            self.core.pluginManager.isUserPlugin(name))
                for name, config, values in self.core.config.iterSections(self.user)]

    @UserContext
    @RequirePerm(Permission.Plugins)
    def configurePlugin(self, plugin):
        """Get complete config options for desired section

        :param plugin: Name of plugin or config section
        :rtype: ConfigHolder
        """

        pass

    @UserContext
    @RequirePerm(Permission.Plugins)
    def saveConfig(self, config):
        """Used to save a configuration, core config can only be saved by admins

        :param config: :class:`ConfigHolder`
        """
        pass

    @UserContext
    @RequirePerm(Permission.Plugins)
    def deleteConfig(self, plugin):
        """Deletes modified config

        :param plugin: plugin name
        """
        self.core.config.delete(plugin, self.user)

    @RequirePerm(Permission.Plugins)
    def setConfigHandler(self, plugin, iid, value):
        pass

if Api.extend(ConfigApi):
    del ConfigApi