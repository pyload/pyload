# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals
from pyload.Api import Api, require_perm, Permission

from .apicomponent import ApiComponent


# TODO: multi user
class AddonApi(ApiComponent):
    """ Methods to interact with addons """

    @require_perm(Permission.Interaction)
    def get_all_info(self):
        """Returns all information stored by addon plugins. Values are always strings

        :return:
        """
        # TODO

    @require_perm(Permission.Interaction)
    def get_info_by_plugin(self, plugin):
        """Returns public information associated with specific plugin.

        :param plugin: pluginName
        :return: list of :class:`AddonInfo`
        """
        return self.pyload.addonmanager.get_info(plugin)

    @require_perm(Permission.Interaction)
    def get_addon_handler(self):
        """ Lists all available addon handler

        :return: dict of plugin name to list of :class:`AddonService`
        """
        handler = {}
        for name, data in self.pyload.addonmanager.iter_addons():
            if data.handler:
                handler[name] = list(data.handler.values())
        return handler

    @require_perm(Permission.Interaction)
    def invoke_addon(self, plugin, func, func_args):
        """ Calls any function exposed by an addon """
        return self.pyload.addonmanager.invoke(plugin, func, func_args)

    @require_perm(Permission.Interaction)
    def invoke_addon_handler(self, plugin, func, pid_or_fid):
        """ Calls an addon handler registered to work with packages or files  """
        return self.invoke_addon(plugin, func, (pid_or_fid,))


if Api.extend(AddonApi):
    del AddonApi
