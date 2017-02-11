# -*- coding: utf-8 -*-
#@author: RaNaN

from __future__ import absolute_import, unicode_literals

import builtins
from builtins import object
from collections import defaultdict
from gettext import gettext

from _thread import start_new_thread
from future import standard_library

from pyload.api import (AddonInfo, AddonService, ServiceDoesNotExist,
                        ServiceException)
from pyload.thread import AddonThread
from pyload.utils.decorator import lock
from pyload.utils.lib.collections import namedtuple
from pyload.utils.lib.threading import RLock
from types import MethodType

standard_library.install_aliases()


AddonTuple = namedtuple('AddonTuple', 'instances events handler')


class AddonManager(object):
    """
    Manages addons, loading, unloading.
    """

    def __init__(self, core):
        self.pyload = core

        builtins.ADDONMANAGER = self  # needed to let addons register themselves

        # TODO: multiuser addons

        # maps plugin names to info tuple
        self.plugins = defaultdict(lambda: AddonTuple([], [], {}))
        # Property hash mapped to meta data
        self.info_props = {}

        self.lock = RLock()
        self.create_index()

        # manage addons on config change
        self.listen_to("config:changed", self.manage_addon)

    def iter_addons(self):
        """
        Yields (name, meta_data) of all addons.
        """
        return iter(self.plugins.items())

    @lock
    def call_in_hooks(self, event, event_name, *args):
        """
        Calls a method in all addons and catch / log errors.
        """
        for plugin in self.plugins.values():
            for inst in plugin.instances:
                self.call(inst, event, *args)
        self.fire(event_name, *args)

    def call(self, plugin, f, *args):
        try:
            func = getattr(plugin, f)
            return func(*args)
        except Exception as e:
            plugin.log_error(_("Error when executing {}".format(f)), e.message)
            # self.pyload.print_exc()

    def invoke(self, plugin, func_name, args):
        """
        Invokes a registered method.
        """
        if plugin not in self.plugins and func_name not in self.plugins[
                plugin].handler:
            raise ServiceDoesNotExist(plugin, func_name)

        # TODO: choose correct instance
        try:
            func = getattr(self.plugins[plugin].instances[0], func_name)
            return func(*args)
        except Exception as e:
            raise ServiceException(e.message)

    @lock
    def create_index(self):
        active = []
        deactive = []

        for pluginname in self.pyload.pgm.get_plugins("addon"):
            try:
                # check first for builtin plugin
                attrs = self.pyload.pgm.load_attributes("addon", pluginname)
                internal = attrs.get("internal", False)

                if internal or self.pyload.config.get(pluginname, "activated"):
                    pluginclass = self.pyload.pgm.load_class(
                        "addon", pluginname)

                    if not pluginclass:
                        continue

                    plugin = pluginclass(self.pyload, self)
                    self.plugins[pluginclass.__name__].instances.append(plugin)

                    # hide internals from printing
                    if not internal and plugin.is_activated():
                        active.append(pluginclass.__name__)
                    else:
                        self.pyload.log.debug(
                            "Loaded internal plugin: {}".format(pluginclass.__name__))
                else:
                    deactive.append(pluginname)

            except Exception:
                self.pyload.log.warning(
                    _("Failed activating {}").format(pluginname))
                # self.pyload.print_exc()

        self.pyload.log.info(
            _("Activated addons: {}").format(", ".join(sorted(active))))
        self.pyload.log.info(_("Deactivated addons: {}").format(
            ", ".join(sorted(deactive))))

    def manage_addon(self, plugin, name, value):
        # TODO: multi user

        # check if section was a plugin
        if plugin not in self.pyload.pgm.get_plugins("addon"):
            return

        if name == "activated" and value:
            self.activate_addon(plugin)
        elif name == "activated" and not value:
            self.deactivate_addon(plugin)

    @lock
    def activate_addon(self, plugin):
        # check if already loaded
        if plugin in self.plugins:
            return

        pluginclass = self.pyload.pgm.load_class("addon", plugin)

        if not pluginclass:
            return

        self.pyload.log.debug("Plugin loaded: {}".format(plugin))

        plugin = pluginclass(self.pyload, self)
        self.plugins[pluginclass.__name__].instances.append(plugin)

        # active the addon in new thread
        start_new_thread(plugin.activate, tuple())
        self.register_events()

    @lock
    def deactivate_addon(self, plugin):
        if plugin not in self.plugins:
            return
        else:  # TODO: multiple instances
            addon = self.plugins[plugin].instances[0]

        if addon.__internal__:
            return

        self.call(addon, "deactivate")
        self.pyload.log.debug("Plugin deactivated: {}".format(plugin))

        # remove periodic call
        self.pyload.log.debug("Removed callback {}".format(
            self.pyload.scheduler.cancel(addon.cb)))

        # TODO: only delete instances, meta data is lost otherwise
        del self.plugins[addon.__name__].instances[:]

        # TODO: could be improved
        # remove event listener
        for f in dir(addon):
            if f.startswith("__") or not isinstance(
                    getattr(addon, f), MethodType):
                continue
            self.pyload.evm.remove_from_events(getattr(addon, f))

    def activate_addons(self):
        self.pyload.log.info(_("Activating addons ..."))
        for plugin in self.plugins.values():
            for inst in plugin.instances:
                if inst.is_activated():
                    self.call(inst, "activate")

        self.register_events()

    def deactivate_addons(self):
        """
        Called when core is shutting down.
        """
        self.pyload.log.info(_("Deactivating addons ..."))
        for plugin in self.plugins.values():
            for inst in plugin.instances:
                self.call(inst, "deactivate")

    def download_preparing(self, pyfile):
        self.call_in_hooks("pre_download", "download:preparing", pyfile)

    def download_finished(self, pyfile):
        self.call_in_hooks("download_finished", "download:finished", pyfile)

    def download_failed(self, pyfile):
        self.call_in_hooks("download_failed", "download:failed", pyfile)

    def package_finished(self, package):
        self.call_in_hooks("package_finished", "package:finished", package)

    @lock
    def start_thread(self, function, *args, **kwargs):
        AddonThread(self.pyload.thm, function, args, kwargs)

    def active_plugins(self):
        """
        Returns all active plugins.
        """
        return [p for x in self.plugins.values()
                for p in x.instances if p.is_activated()]

    def get_info(self, plugin):
        """
        Retrieves all info data for a plugin.
        """
        data = []
        # TODO
        if plugin in self.plugins:
            if plugin.instances:
                for attr in dir(plugin.instances[0]):
                    if attr.startswith("__Property"):
                        info = self.info_props[attr]
                        info.value = getattr(plugin.instances[0], attr)
                        data.append(info)
        return data

    def add_event_listener(self, plugin, func, event):
        """
        Add the event to the list.
        """
        self.plugins[plugin].events.append((func, event))

    def register_events(self):
        """
        Actually register all saved events.
        """
        for name, plugin in self.plugins.items():
            for func, event in plugin.events:
                for inst in plugin.instances:
                    self.listen_to(event, getattr(inst, func))

    def add_addon_handler(self, plugin, func, label,
                          desc, args, package, media):
        """
        Registers addon service description.
        """
        self.plugins[plugin].handler[func] = AddonService(
            func, gettext(label), gettext(desc), args, package, media)

    def add_info_property(self, h, name, desc):
        """
        Register property as :class:`AddonInfo`.
        """
        self.info_props[h] = AddonInfo(name, desc)

    def listen_to(self, *args):
        self.pyload.evm.listen_to(*args)

    def fire(self, *args):
        self.pyload.evm.fire(*args)
