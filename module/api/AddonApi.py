#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.Api import Api, RequirePerm, Permission

from ApiComponent import ApiComponent

class AddonApi(ApiComponent):
    """ Methods to interact with addons """

    def getAllInfo(self):
        """Returns all information stored by addon plugins. Values are always strings

        :return: {"plugin": {"name": value } }
        """
        return self.core.addonManager.getAllInfo()

    def getInfoByPlugin(self, plugin):
        """Returns information stored by a specific plugin.

        :param plugin: pluginname
        :return: dict of attr names mapped to value {"name": value}
        """
        return self.core.addonManager.getInfo(plugin)

if Api.extend(AddonApi):
    del AddonApi