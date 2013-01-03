#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.Api import Api, UserContext, RequirePerm, Permission, ConfigHolder, ConfigItem
from module.utils import to_string

from ApiComponent import ApiComponent

class ConfigApi(ApiComponent):
    """ Everything related to configuration """

    def getConfigValue(self, section, option):
        """Retrieve config value.

        :param section: name of category, or plugin
        :param option: config option
        :rtype: str
        :return: config value as string
        """
        value = self.core.config.get(section, option)
        return to_string(value)

    def setConfigValue(self, section, option, value):
        """Set new config value.

        :param section:
        :param option:
        :param value: new config value
        """
        if option in ("limit_speed", "max_speed"): #not so nice to update the limit
            self.core.requestFactory.updateBucket()

        self.core.config.set(section, option, value)

    def getConfig(self):
        """Retrieves complete config of core.

        :rtype: ConfigHolder
        :return: dict with section mapped to config
        """
        # TODO
        return dict([(section, ConfigHolder(section, data.name, data.description, data.long_desc, [
        ConfigItem(option, d.name, d.description, d.type, to_string(d.default),
            to_string(self.core.config.get(section, option))) for
        option, d in data.config.iteritems()])) for
                     section, data in self.core.config.getBaseSections()])


    def getConfigRef(self):
        """Config instance, not for RPC"""
        return self.core.config

    def getGlobalPlugins(self):
        """All global plugins/addons, only admin can use this

        :return: list of `ConfigInfo`
        """
        pass

    @UserContext
    @RequirePerm(Permission.Plugins)
    def getUserPlugins(self):
        """List of plugins every user can configure for himself

        :return: list of `ConfigInfo`
        """
        pass

    @UserContext
    @RequirePerm(Permission.Plugins)
    def configurePlugin(self, plugin):
        """Get complete config options for an plugin

        :param plugin: Name of the plugin to configure
        :return: :class:`ConfigHolder`
        """

        pass

    @UserContext
    @RequirePerm(Permission.Plugins)
    def saveConfig(self, config):
        """Used to save a configuration, core config can only be saved by admins

        :param config: :class:`ConfigHolder
        """
        pass

    @UserContext
    @RequirePerm(Permission.Plugins)
    def deleteConfig(self, plugin):
        """Deletes modified config

        :param plugin: plugin name
        :return:
        """
        pass

    @RequirePerm(Permission.Plugins)
    def setConfigHandler(self, plugin, iid, value):
        pass

if Api.extend(ConfigApi):
    del ConfigApi