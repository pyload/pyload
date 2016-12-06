# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import object
import builtins

from gettext import gettext
from _thread import start_new_thread
from threading import RLock

from collections import defaultdict
from new_collections import namedtuple

from types import MethodType

from pyload.Api import AddonService, AddonInfo, ServiceException, ServiceDoesNotExist
from pyload.threads.AddonThread import AddonThread
from .utils import lock, to_string

AddonTuple = namedtuple('AddonTuple', 'instances events handler')


class AddonManager(object):
    """ Manages addons, loading, unloading.  """

    def __init__(self, core):
        self.core = core
        self.config = self.core.config

        builtins.addonManager = self #needed to let addons register themselves

        self.log = self.core.log

        # TODO: multiuser addons

        # maps plugin names to info tuple
        self.plugins = defaultdict(lambda: AddonTuple([], [], {}))
        # Property hash mapped to meta data
        self.info_props = {}

        self.lock = RLock()
        self.createIndex()

        # manage addons on config change
        self.listenTo("config:changed", self.manageAddon)

    def iterAddons(self):
        """ Yields (name, meta_data) of all addons """
        return iter(self.plugins.items())

    @lock
    def callInHooks(self, event, eventName, *args):
        """  Calls a method in all addons and catch / log errors"""
        for plugin in self.plugins.values():
            for inst in plugin.instances:
                self.call(inst, event, *args)
        self.dispatchEvent(eventName, *args)

    def call(self, plugin, f, *args):
        try:
            func = getattr(plugin, f)
            return func(*args)
        except Exception as e:
            plugin.logError(_("Error when executing %s" % f), e)
            self.core.print_exc()

    def invoke(self, plugin, func_name, args):
        """ Invokes a registered method """

        if plugin not in self.plugins and func_name not in self.plugins[plugin].handler:
            raise ServiceDoesNotExist(plugin, func_name)

        # TODO: choose correct instance
        try:
            func = getattr(self.plugins[plugin].instances[0], func_name)
            return func(*args)
        except Exception as e:
            raise ServiceException(e.message)

    @lock
    def createIndex(self):
        active = []
        deactive = []

        for pluginname in self.core.pluginManager.getPlugins("addons"):
            try:
                # check first for builtin plugin
                attrs = self.core.pluginManager.loadAttributes("addons", pluginname)
                internal = attrs.get("internal", False)

                if internal or self.core.config.get(pluginname, "activated"):
                    pluginClass = self.core.pluginManager.loadClass("addons", pluginname)

                    if not pluginClass: continue

                    plugin = pluginClass(self.core, self)
                    self.plugins[pluginClass.__name__].instances.append(plugin)

                    # hide internals from printing
                    if not internal and plugin.isActivated():
                        active.append(pluginClass.__name__)
                    else:
                        self.log.debug("Loaded internal plugin: %s" % pluginClass.__name__)
                else:
                    deactive.append(pluginname)

            except Exception:
                self.log.warning(_("Failed activating %(name)s") % {"name": pluginname})
                self.core.print_exc()

        self.log.info(_("Activated addons: %s") % ", ".join(sorted(active)))
        self.log.info(_("Deactivated addons: %s") % ", ".join(sorted(deactive)))

    def manageAddon(self, plugin, name, value):
        # TODO: multi user

        # check if section was a plugin
        if plugin not in self.core.pluginManager.getPlugins("addons"):
            return

        if name == "activated" and value:
            self.activateAddon(plugin)
        elif name == "activated" and not value:
            self.deactivateAddon(plugin)

    @lock
    def activateAddon(self, plugin):
        #check if already loaded
        if plugin in self.plugins:
            return

        pluginClass = self.core.pluginManager.loadClass("addons", plugin)

        if not pluginClass: return

        self.log.debug("Plugin loaded: %s" % plugin)

        plugin = pluginClass(self.core, self)
        self.plugins[pluginClass.__name__].instances.append(plugin)

        # active the addon in new thread
        start_new_thread(plugin.activate, tuple())
        self.registerEvents()

    @lock
    def deactivateAddon(self, plugin):
        if plugin not in self.plugins:
            return
        else: # todo: multiple instances
            addon = self.plugins[plugin].instances[0]

        if addon.__internal__: return

        self.call(addon, "deactivate")
        self.log.debug("Plugin deactivated: %s" % plugin)

        #remove periodic call
        self.log.debug("Removed callback %s" % self.core.scheduler.removeJob(addon.cb))

        # todo: only delete instances, meta data is lost otherwise
        del self.plugins[addon.__name__].instances[:]

        # TODO: could be improved
        #remove event listener
        for f in dir(addon):
            if f.startswith("__") or not isinstance(getattr(addon, f), MethodType):
                continue
            self.core.eventManager.removeFromEvents(getattr(addon, f))

    def activateAddons(self):
        self.log.info(_("Activating addons..."))
        for plugin in self.plugins.values():
            for inst in plugin.instances:
                if inst.isActivated():
                    self.call(inst, "activate")

        self.registerEvents()

    def deactivateAddons(self):
        """  Called when core is shutting down """
        self.log.info(_("Deactivating addons..."))
        for plugin in self.plugins.values():
            for inst in plugin.instances:
                self.call(inst, "deactivate")

    def downloadPreparing(self, pyfile):
        self.callInHooks("downloadPreparing", "download:preparing", pyfile)

    def downloadFinished(self, pyfile):
        self.callInHooks("downloadFinished", "download:finished", pyfile)

    def downloadFailed(self, pyfile):
        self.callInHooks("downloadFailed", "download:failed", pyfile)

    def packageFinished(self, package):
        self.callInHooks("packageFinished", "package:finished", package)

    @lock
    def startThread(self, function, *args, **kwargs):
        AddonThread(self.core.threadManager, function, args, kwargs)

    def activePlugins(self):
        """ returns all active plugins """
        return [p for x in self.plugins.values() for p in x.instances if p.isActivated()]

    def getInfo(self, plugin):
        """ Retrieves all info data for a plugin """

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

    def addEventListener(self, plugin, func, event):
        """ add the event to the list """
        self.plugins[plugin].events.append((func, event))

    def registerEvents(self):
        """ actually register all saved events """
        for name, plugin in self.plugins.items():
            for func, event in plugin.events:
                for inst in plugin.instances:
                    self.listenTo(event, getattr(inst, func))

    def addAddonHandler(self, plugin, func, label, desc, args, package, media):
        """ Registers addon service description """
        self.plugins[plugin].handler[func] = AddonService(func, gettext(label), gettext(desc), args, package, media)

    def addInfoProperty(self, h, name, desc):
        """  Register property as :class:`AddonInfo` """
        self.info_props[h] = AddonInfo(name, desc)

    def listenTo(self, *args):
        self.core.eventManager.listenTo(*args)

    def dispatchEvent(self, *args):
        self.core.eventManager.dispatchEvent(*args)
