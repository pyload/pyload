# -*- coding: utf-8 -*-

import sys
import re

from operator import itemgetter
from os import remove, stat
from os.path import join, isfile
from time import time

from module.network.RequestFactory import getURL
from module.plugins.Hook import Expose, Hook, threaded


class UpdateManager(Hook):
    __name__ = "UpdateManager"
    __version__ = "0.31"
    __type__ = "hook"

    __config__ = [("activated", "bool", "Activated", True),
                  ("mode", "pyLoad + plugins;plugins only", "Check updates for", "pyLoad + plugins"),
                  ("interval", "int", "Check interval in hours", 8),
                  ("reloadplugins", "bool", "Monitor plugins for code changes (debug mode only)", True),
                  ("nodebugupdate", "bool", "Don't check for updates in debug mode", True)]

    __description__ = """Check for updates"""
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"

    SERVER_URL = "http://updatemanager.pyload.org"
    MIN_INTERVAL = 3 * 60 * 60  #: 3h minimum check interval (value is in seconds)

    event_list = ["pluginConfigChanged"]


    def pluginConfigChanged(self, plugin, name, value):
        if name == "interval":
            interval = value * 60 * 60
            if self.MIN_INTERVAL <= interval != self.interval:
                self.scheduler.removeJob(self.cb)
                self.interval = interval
                self.initPeriodical()
            else:
                self.logDebug("Invalid interval value, kept current")
        elif name == "reloadplugins":
            if self.cb2:
                self.scheduler.removeJob(self.cb2)
            if value is True and self.core.debug:
                self.periodical2()

    def coreReady(self):
        self.pluginConfigChanged(self.__name__, "interval", self.getConfig("interval"))
        self.pluginConfigChanged(self.__name__, "reloadplugins", self.getConfig("reloadplugins"))

    def setup(self):
        self.scheduler = self.core.scheduler
        self.cb2 = None
        self.interval = self.MIN_INTERVAL
        self.updating = False
        self.info = {"pyload": False, "version": None, "plugins": False}
        self.mtimes = {}  #: store modification time for each plugin


    def periodical2(self):
        if not self.updating:
            self.autoreloadPlugins()
        self.cb2 = self.scheduler.addJob(10, self.periodical2, threaded=True)

    @Expose
    def autoreloadPlugins(self):
        """ reload and reindex all modified plugins """
        modules = filter(
            lambda m: m and (m.__name__.startswith("module.plugins.") or
                             m.__name__.startswith("userplugins.")) and
                             m.__name__.count(".") >= 2, sys.modules.itervalues())

        reloads = []

        for m in modules:
            root, type, name = m.__name__.rsplit(".", 2)
            id = (type, name)
            if type in self.core.pluginManager.plugins:
                f = m.__file__.replace(".pyc", ".py")
                if not isfile(f):
                    continue

                mtime = stat(f).st_mtime

                if id not in self.mtimes:
                    self.mtimes[id] = mtime
                elif self.mtimes[id] < mtime:
                    reloads.append(id)
                    self.mtimes[id] = mtime

        return True if self.core.pluginManager.reloadPlugins(reloads) else False

    def periodical(self):
        if not self.info['pyload'] and not (self.getConfig("nodebugupdate") and self.core.debug):
            self.updating = True
            self.update(onlyplugin=True if self.getConfig("mode") == "plugins only" else False)
            self.updating = False

    def server_response(self):
        try:
            return getURL(self.SERVER_URL, get={'v': self.core.api.getServerVersion()}).splitlines()
        except:
            self.logWarning(_("Unable to contact server to get updates"))

    @Expose
    def updatePlugins(self):
        """ simple wrapper for calling plugin update quickly """
        return self.update(onlyplugin=True)

    @Expose
    def update(self, onlyplugin=False):
        """ check for updates """
        data = self.server_response()
        if not data:
            r = False
        elif data[0] == "None":
            self.logInfo(_("No new pyLoad version available"))
            updates = data[1:]
            r = self._updatePlugins(updates)
        elif onlyplugin:
            r = False
        else:
            newversion = data[0]
            self.logInfo(_("***  New pyLoad Version %s available  ***") % newversion)
            self.logInfo(_("***  Get it here: https://github.com/pyload/pyload/releases  ***"))
            r = self.info['pyload'] = True
            self.info['version'] = newversion
        return r

    @threaded
    def _updatePlugins(self, updates):
        """ check for plugin updates """

        if self.info['plugins']:
            return False  #: plugins were already updated

        updated = []

        vre = re.compile(r'__version__.*=.*("|\')([0-9.]+)')
        url = updates[0]
        schema = updates[1].split('|')
        if "BLACKLIST" in updates:
            blacklist = updates[updates.index('BLACKLIST') + 1:]
            updates = updates[2:updates.index('BLACKLIST')]
        else:
            blacklist = None
            updates = updates[2:]

        data = sorted(map(lambda x: dict(zip(schema, x.split('|'))), updates), key=itemgetter("type", "name"))
        for plugin in data:
            filename = plugin['name']
            prefix = plugin['type']
            version = plugin['version']

            if filename.endswith(".pyc"):
                name = filename[:filename.find("_")]
            else:
                name = filename.replace(".py", "")

            #TODO: obsolete in 0.5.0
            if prefix.endswith("s"):
                type = prefix[:-1]
            else:
                type = prefix

            plugins = getattr(self.core.pluginManager, "%sPlugins" % type)

            oldver = float(plugins[name]['v']) if name in plugins else None
            newver = float(version)

            if not oldver:
                msg = "New version of [%(type)s] %(name)s (v%(newver)s)"
            elif newver > oldver:
                msg = "New version of [%(type)s] %(name)s (v%(oldver)s -> v%(newver)s)"
            else:
                continue

            self.logInfo(_(msg) % {
                "type": type,
                "name": name,
                "oldver": oldver,
                "newver": newver
            })

            try:
                content = getURL(url % plugin)
                m = vre.search(content)
                if m and m.group(2) == version:
                    f = open(join("userplugins", prefix, filename), "wb")
                    f.write(content)
                    f.close()
                    updated.append((prefix, name))
                else:
                    raise Exception(_("Version mismatch"))
            except Exception, e:
                self.logError(_("Error updating plugin %s") % filename, str(e))

        if blacklist:
            removed = self.removePlugins(map(lambda x: x.split('|'), blacklist))
            for t, n in removed:
                self.logInfo(_("Removed blacklisted plugin: [%(type)s] %(name)s") % {
                    "type": t,
                    "name": n
                })

        if updated:
            reloaded = self.core.pluginManager.reloadPlugins(updated)
            if reloaded:
                self.logInfo(_("Plugins updated and reloaded"))
            else:
                self.logInfo(_("*** Plugins have been updated, pyLoad will be restarted now ***"))
                self.info['plugins'] = True
                self.scheduler.addJob(4, self.core.api.restart(), threaded=False)  #: risky, but pyload doesn't let more
            return True
        else:
            self.logInfo(_("No plugin updates available"))
            return False

    @Expose
    def removePlugins(self, type_plugins):
        """ delete plugins under userplugins directory"""
        if not type_plugins:
            return None

        self.logDebug("Request deletion of plugins: %s" % type_plugins)

        removed = []

        for type, name in type_plugins:
            py = join("userplugins", type, name)
            pyc = join("userplugins", type, name.replace('.py', '.pyc'))
            id = (type, name)
            try:
                if isfile(py):
                    remove(py)
                if isfile(pyc):
                    remove(pyc)
            except Exception, e:
                self.logError("Error deleting %s" % id, str(e))
            else:
                removed.append(id)

        return removed  #: return a list of the plugins successfully removed
