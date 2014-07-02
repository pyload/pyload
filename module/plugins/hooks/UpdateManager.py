# -*- coding: utf-8 -*-

import sys
import re

from os import remove, stat
from os.path import join, isfile
from time import time

from module.ConfigParser import IGNORE
from module.network.RequestFactory import getURL
from module.plugins.Hook import threaded, Expose, Hook


class UpdateManager(Hook):
    __name__ = "UpdateManager"
    __version__ = "0.25"
    __description__ = """Check for updates"""
    __config__ = [("activated", "bool", "Activated", True),
                  ("mode", "pyLoad + plugins;plugins only", "Check updates for", "pyLoad + plugins"),
                  ("interval", "int", "Check interval in hours", 8),
                  ("reloadplugins", "bool", "Monitor plugins for code changes (debug mode only)", True),
                  ("nodebugupdate", "bool", "Don't check for updates in debug mode", True)]
    __author_name__ = ("RaNaN", "stickell", "Walter Purcaro")
    __author_mail__ = ("ranan@pyload.org", "l.stickell@yahoo.it", "vuolter@gmail.com")

    SERVER_URL = "http://updatemanager.pyload.org"
    MIN_TIME = 3 * 60 * 60  #: 3h minimum check interval (seconds)

    event_list = ["pluginConfigChanged"]


    def pluginConfigChanged(self, plugin, name, value):
        if name == "interval":
            interval = value * 60 * 60
            if self.MIN_TIME <= interval != self.interval:
                if self.cb:
                    self.core.scheduler.removeJob(self.cb)
                self.interval = interval
                self.initPeriodical()
            else:
                self.logWarning("Invalid interval value, kept current")
        elif name == "reloadplugins":
            if self.cb2:
                self.core.scheduler.removeJob(self.cb2)
            if value and self.core.debug:
                self.periodical2()

    def coreReady(self):
        self.pluginConfigChanged(self.__name__, "reloadplugins", self.getConfig("reloadplugins"))

    def setup(self):
        self.cb2 = None
        self.interval = self.MIN_TIME
        self.updating = False
        self.info = {"pyload": False, "version": None, "plugins": False}
        self.mtimes = {}  #: store modification time for each plugin


    def periodical2(self):
        if not self.updating:
            self.autoreloadPlugins()
        self.cb2 = self.core.scheduler.addJob(10, self.periodical2, threaded=True)

    @Expose
    def autoreloadPlugins(self):
        """ reload and reindex all modified plugins """
        modules = filter(
            lambda m: m and (m.__name__.startswith("module.plugins.") or m.__name__.startswith(
                "userplugins.")) and m.__name__.count(".") >= 2, sys.modules.itervalues())

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

    @threaded
    def periodical(self):
        if not self.info["pyload"] and not (self.getConfig("nodebugupdate") and self.core.debug):
            self.updating = True
            self.update(onlyplugin=True if self.getConfig("mode") == "plugins only" else False)
            self.updating = False

    def server_response(self):
        try:
            return getURL(self.SERVER_URL, get={'v': self.core.api.getServerVersion()}).splitlines()
        except:
            self.logWarning(_("Not able to connect server to get updates"))

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
            self.logInfo(_("No pyLoad version available"))
            updates = data[1:]
            r = self._updatePlugins(updates)
        elif onlyplugin:
            r = False
        else:
            newversion = data[0]
            self.logInfo(_("***  New pyLoad Version %s available  ***") % newversion)
            self.logInfo(_("***  Get it here: https://github.com/pyload/pyload/releases  ***"))
            r = self.info["pyload"] = True
            self.info["version"] = newversion
        return r

    def _updatePlugins(self, updates):
        """ check for plugin updates """

        if self.info["plugins"]:
            return False  #: plugins were already updated

        updated = []

        vre = re.compile(r'__version__.*=.*("|\')([0-9.]+)')
        url = updates[0]
        schema = updates[1].split("|")
        if 'BLACKLIST' in updates:
            blacklist = updates[updates.index('BLACKLIST') + 1:]
            updates = updates[2:updates.index('BLACKLIST')]
        else:
            blacklist = None
            updates = updates[2:]

        for plugin in updates:
            info = dict(zip(schema, plugin.split("|")))
            filename = info["name"]
            prefix = info["type"]
            version = info["version"]

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

            if name not in plugins or name in IGNORE or (type, name) in IGNORE:
                continue

            oldver = float(plugins[name]["v"])
            newver = float(version)

            if oldver >= newver:
                continue
            else:
                self.logInfo(_("New version of [%(type)s] %(name)s (v%(oldver)s -> v%(newver)s)") % {
                    "type": type,
                    "name": name,
                    "oldver": oldver,
                    "newver": newver
                })

            try:
                content = getURL(url % info)
            except Exception, e:
                self.logError(_("Error when updating plugin %s") % filename, str(e))
                continue

            m = vre.search(content)
            if not m or m.group(2) != version:
                self.logError(_("Error when updating plugin %s") % name, _("Version mismatch"))
                continue

            f = open(join("userplugins", prefix, filename), "wb")
            f.write(content)
            f.close()
            updated.append((prefix, name))

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
                self.info["plugins"] = True
                self.core.scheduler.addJob(4, self.core.api.restart(), threaded=False)  #: risky, but pyload doesn't let more
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
            if isfile(py):
                id = (type, name)
                remove(py)
                removed.append(id)
            if isfile(pyc):
                remove(pyc)

        return removed  #: return a list of the plugins successfully removed
