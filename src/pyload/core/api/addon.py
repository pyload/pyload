# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from future import standard_library
standard_library.install_aliases()

from ..datatype.init import Permission
from .base import BaseApi
from .init import Api, requireperm


# TODO: multi user
class AddonApi(BaseApi):
    """
    Methods to interact with addons.
    """
    __slots__ = []

    @requireperm(Permission.Interaction)
    def get_all_info(self):
        """
        Returns all information stored by addon plugins. Values are always strings.
        """
        raise NotImplementedError

    @requireperm(Permission.Interaction)
    def get_info_by_plugin(self, plugin):
        """
        Returns public information associated with specific plugin.

        :param plugin: pluginName
        :return: list of :class:`AddonInfo`
        """
        return self.pyload.adm.get_info(plugin)

    @requireperm(Permission.Interaction)
    def get_addon_handler(self):
        """
        Lists all available addon handler

        :return: dict of plugin name to list of :class:`AddonService`
        """
        handler = {}
        for name, data in self.pyload.adm.iter_addons():
            if data.handler:
                handler[name] = list(data.handler.values())
        return handler

    @requireperm(Permission.Interaction)
    def invoke_addon(self, plugin, func, func_args):
        """
        Calls any function exposed by an addon.
        """
        return self.pyload.adm.invoke(plugin, func, func_args)

    @requireperm(Permission.Interaction)
    def invoke_addon_handler(self, plugin, func, pid_or_fid):
        """
        Calls an addon handler registered to work with packages or files.
        """
        return self.invoke_addon(plugin, func, (pid_or_fid,))
