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
    __version__ = "0.16"
    __description__ = """Checks for updates"""
    __config__ = [("activated", "bool", "Activated", True),
                  ("interval", "int", "Check interval in minutes", 480),
                  ("debug", "bool", "Check for plugin changes when in debug mode", False)]
    __author_name__ = ("RaNaN", "stickell")
    __author_mail__ = ("ranan@pyload.org", "l.stickell@yahoo.it")

    URL = "http://updatemanager-spyload.rhcloud.com"
    MIN_TIME = 3 * 60 * 60  # 3h minimum check interval

    @property
    def debug(self):
        return self.core.debug and self.getConfig("debug")

    def setup(self):
        if self.debug:
            self.logDebug("Monitoring file changes")
            self.interval = 4
            self.last_check = 0  # timestamp of updatecheck
            self.old_periodical = self.periodical
            self.periodical = self.checkChanges
            self.mtimes = {}  # recordes times
        else:
            self.interval = max(self.getConfig("interval") * 60, self.MIN_TIME)

        self.updated = False
        self.reloaded = True
        self.version = "None"

        self.info = {"pyload": False, "plugins": False}

    @threaded
    def periodical(self):
        updates = self.checkForUpdate()
        if updates:
            self.checkPlugins(updates)

        if self.updated and not self.reloaded:
            self.info["plugins"] = True
            self.logInfo(_("*** Plugins have been updated, please restart pyLoad ***"))
        elif self.updated and self.reloaded:
            self.logInfo(_("Plugins updated and reloaded"))
            self.updated = False
        elif self.version == "None":
            self.logInfo(_("No plugin updates available"))

    @Expose
    def recheckForUpdates(self):
        """recheck if updates are available"""
        self.periodical()

    def checkForUpdate(self):
        """checks if an update is available, return result"""
        try:
            if self.version == "None":  # No updated known
                version_check = getURL(self.URL, get={'v': self.core.api.getServerVersion()}).splitlines()
                self.version = version_check[0]

                # Still no updates, plugins will be checked
                if self.version == "None":
                    self.logInfo(_("No Updates for pyLoad"))
                    return version_check[1:]

            self.info["pyload"] = True
            self.logInfo(_("***  New pyLoad Version %s available  ***") % self.version)
            self.logInfo(_("***  Get it here: http://pyload.org/download  ***"))
        except:
            self.logWarning(_("Not able to connect server for updates"))

        return None  # Nothing will be done

    def checkPlugins(self, updates):
        """ checks for plugins updates"""

        # plugins were already updated
        if self.info["plugins"]:
            return

        reloads = []

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

            if name in plugins:
                if float(plugins[name]["v"]) >= float(version):
                    continue

            if name in IGNORE or (type, name) in IGNORE:
                continue

            self.logInfo(_("New version of %(type)s|%(name)s : %(version).2f") % {
                "type": type,
                "name": name,
                "version": float(version)
            })

            try:
                content = getURL(url % info)
            except Exception, e:
                self.logWarning(_("Error when updating %s") % filename, str(e))
                continue

            m = vre.search(content)
            if not m or m.group(2) != version:
                self.logWarning(_("Error when updating %s") % name, _("Version mismatch"))
                continue

            f = open(join("userplugins", prefix, filename), "wb")
            f.write(content)
            f.close()
            self.updated = True

            reloads.append((prefix, name))

        self.executeBlacklist(blacklist)

        self.reloaded = self.core.pluginManager.reloadPlugins(reloads)

    def executeBlacklist(self, blacklist):
        for b in blacklist:
            type, name = b.split('|')
            if isfile(join("userplugins", type, name)):
                self.logInfo(_("Removing blacklisted plugin %(type)s|%(name)s") % {
                    "type": type,
                    "name": name
                })
                remove(join("userplugins", type, name))
            if isfile(join("userplugins", type, name.replace('.py', '.pyc'))):
                remove(join("userplugins", type, name.replace('.py', '.pyc')))

    def checkChanges(self):
        if self.last_check + max(self.getConfig("interval") * 60, self.MIN_TIME) < time():
            self.old_periodical()
            self.last_check = time()

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

        self.core.pluginManager.reloadPlugins(reloads)
