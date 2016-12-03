# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals
from pyload.Api import Api, RequirePerm, Permission

from .ApiComponent import ApiComponent

# TODO: multi user
class AddonApi(ApiComponent):
    """ Methods to interact with addons """

    @RequirePerm(Permission.Interaction)
    def getAllInfo(self):
        """Returns all information stored by addon plugins. Values are always strings

        :return:
        """
        # TODO

    @RequirePerm(Permission.Interaction)
    def getInfoByPlugin(self, plugin):
        """Returns public information associated with specific plugin.

        :param plugin: pluginName
        :return: list of :class:`AddonInfo`
        """
        return self.core.addonManager.getInfo(plugin)

    @RequirePerm(Permission.Interaction)
    def getAddonHandler(self):
        """ Lists all available addon handler

        :return: dict of plugin name to list of :class:`AddonService`
        """
        handler = {}
        for name, data in self.core.addonManager.iterAddons():
            if data.handler:
                handler[name] = data.handler.values()
        return handler

    @RequirePerm(Permission.Interaction)
    def invokeAddon(self, plugin, func, func_args):
        """ Calls any function exposed by an addon """
        return self.core.addonManager.invoke(plugin, func, func_args)

    @RequirePerm(Permission.Interaction)
    def invokeAddonHandler(self, plugin, func, pid_or_fid):
        """ Calls an addon handler registered to work with packages or files  """
        return self.invokeAddon(plugin, func, (pid_or_fid, ))


if Api.extend(AddonApi):
    del AddonApi
