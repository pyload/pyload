# -*- coding: utf-8 -*-

from __future__ import with_statement

import re
import sys

from operator import itemgetter
from os import path, remove, stat

from pyload.network.RequestFactory import getURL
from pyload.plugin.Addon import Expose, Addon, threaded
from pyload.utils import safe_join


class UpdateManager(Addon):
    __name    = "UpdateManager"
    __type    = "addon"
    __version = "0.42"

    __config = [("activated"    , "bool"                         , "Activated"                                     , True              ),
                ("mode"         , "pyLoad + plugins;plugins only", "Check updates for"                             , "pyLoad + plugins"),
                ("interval"     , "int"                          , "Check interval in hours"                       , 8                 ),
                ("autorestart"  , "bool"                         , "Automatically restart pyLoad when required"    , True              ),
                ("reloadplugins", "bool"                         , "Monitor plugins for code changes in debug mode", True              ),
                ("nodebugupdate", "bool"                         , "Don't check for updates in debug mode"         , True              )]

    __description = """Check for updates"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    # event_list = ["pluginConfigChanged"]

    SERVER_URL   = "http://updatemanager.pyload.org"
    VERSION      = re.compile(r'__version.*=.*("|\')([\d.]+)')
    MIN_INTERVAL = 3 * 60 * 60  #: 3h minimum check interval (value is in seconds)


    def pluginConfigChanged(self, plugin, name, value):
        if name == "interval":
            interval = value * 60 * 60
            if self.MIN_INTERVAL <= interval != self.interval:
                self.core.scheduler.removeJob(self.cb)
                self.interval = interval
                self.initPeriodical()
            else:
                self.logDebug("Invalid interval value, kept current")

        elif name == "reloadplugins":
            if self.cb2:
                self.core.scheduler.removeJob(self.cb2)
            if value is True and self.core.debug:
                self.periodical2()


    def activate(self):
        self.pluginConfigChanged(self.__name, "interval", self.getConfig("interval"))
        x = lambda: self.pluginConfigChanged(self.__name, "reloadplugins", self.getConfig("reloadplugins"))
        self.core.scheduler.addJob(10, x, threaded=False)


    def deactivate(self):
        self.pluginConfigChanged(self.__name, "reloadplugins", False)


    def setup(self):
        self.cb2      = None
        self.interval = 0
        self.updating = False
        self.info     = {'pyload': False, 'version': None, 'plugins': False}
        self.mtimes   = {}  #: store modification time for each plugin


    def periodical2(self):
        if not self.updating:
            self.autoreloadPlugins()

        self.cb2 = self.core.scheduler.addJob(4, self.periodical2, threaded=False)


    @Expose
    def autoreloadPlugins(self):
        """ reload and reindex all modified plugins """
        modules = filter(
            lambda m: m and (m.__name.startswith("pyload.plugin.") or
                             m.__name.startswith("userplugins.")) and
                             m.__name.count(".") >= 2, sys.modules.itervalues()
        )

        reloads = []

        for m in modules:
            root, type, name = m.__name.rsplit(".", 2)
            id = (type, name)
            if type in self.core.pluginManager.plugins:
                f = m.__file__.replace(".pyc", ".py")
                if not path.isfile(f):
                    continue

                mtime = stat(f).st_mtime

                if id not in self.mtimes:
                    self.mtimes[id] = mtime
                elif self.mtimes[id] < mtime:
                    reloads.append(id)
                    self.mtimes[id] = mtime

        return True if self.core.pluginManager.reloadPlugins(reloads) else False


    def periodical(self):
        if self.info['pyload'] or self.getConfig("nodebugupdate") and self.core.debug:
            return

        self.updateThread()


    def server_request(self):
        try:
            return getURL(self.SERVER_URL, get={'v': self.core.api.getServerVersion()}).splitlines()
        except Exception:
            self.logWarning(_("Unable to contact server to get updates"))


    @threaded
    def updateThread(self):
        self.updating = True

        status = self.update(onlyplugin=self.getConfig("mode") == "plugins only")

        if status is 2 and self.getConfig("autorestart"):
            self.core.api.restart()
        else:
            self.updating = False


    @Expose
    def updatePlugins(self):
        """ simple wrapper for calling plugin update quickly """
        return self.update(onlyplugin=True)


    @Expose
    def update(self, onlyplugin=False):
        """ check for updates """
        data = self.server_request()

        if not data:
            exitcode = 0

        elif data[0] == "None":
            self.logInfo(_("No new pyLoad version available"))
            updates = data[1:]
            exitcode = self._updatePlugins(updates)

        elif onlyplugin:
            exitcode = 0

        else:
            newversion = data[0]
            self.logInfo(_("***  New pyLoad Version %s available  ***") % newversion)
            self.logInfo(_("***  Get it here: https://github.com/pyload/pyload/releases  ***"))
            exitcode = 3
            self.info['pyload'] = True
            self.info['version'] = newversion

        return exitcode  #: 0 = No plugins updated; 1 = Plugins updated; 2 = Plugins updated, but restart required; 3 = No plugins updated, new pyLoad version available


    def _updatePlugins(self, updates):
        """ check for plugin updates """

        if self.info['plugins']:
            return False  #: plugins were already updated

        exitcode = 0
        updated  = []

        url    = updates[0]
        schema = updates[1].split('|')

        if "BLACKLIST" in updates:
            blacklist = updates[updates.index('BLACKLIST') + 1:]
            updates   = updates[2:updates.index('BLACKLIST')]
        else:
            blacklist = None
            updates   = updates[2:]

        upgradable  = [dict(zip(schema, x.split('|'))) for x in updates]
        blacklisted = [(x.split('|')[0], x.split('|')[1].rsplit('.', 1)[0]) for x in blacklist] if blacklist else []

        if blacklist:
            # Protect internal plugins against removing
            for i, t, n in enumerate(blacklisted):
				if t == "internal":
                    blacklisted.pop(i)
					continue

                for idx, plugin in enumerate(upgradable):
                    if n == plugin['name'] and t == plugin['type']:
                        upgradable.pop(idx)
                        break

            for t, n in self.removePlugins(sorted(blacklisted)):
                self.logInfo(_("Removed blacklisted plugin [%(type)s] %(name)s") % {
                    'type': t,
                    'name': n,
                })

        for plugin in sorted(upgradable, key=itemgetter("type", "name")):
            filename = plugin['name']
            type     = plugin['type']
            version  = plugin['version']

            if filename.endswith(".pyc"):
                name = filename[:filename.find("_")]
            else:
                name = filename.replace(".py", "")

            plugins = getattr(self.core.pluginManager, "%sPlugins" % type)

            oldver = float(plugins[name]['version']) if name in plugins else None
            newver = float(version)

            if not oldver:
                msg = "New plugin: [%(type)s] %(name)s (v%(newver).2f)"
            elif newver > oldver:
                msg = "New version of plugin: [%(type)s] %(name)s (v%(oldver).2f -> v%(newver).2f)"
            else:
                continue

            self.logInfo(_(msg) % {'type'  : type,
                                   'name'  : name,
                                   'oldver': oldver,
                                   'newver': newver})
            try:
                content = getURL(url % plugin)
                m = self.VERSION.search(content)

                if m and m.group(2) == version:
                    with open(safe_join("userplugins", prefix, filename), "wb") as f:
                        f.write(content)

                    updated.append((prefix, name))
                else:
                    raise Exception, _("Version mismatch")

            except Exception, e:
                self.logError(_("Error updating plugin: %s") % filename, str(e))

        if updated:
            reloaded = self.core.pluginManager.reloadPlugins(updated)
            if reloaded:
                self.logInfo(_("Plugins updated and reloaded"))
                exitcode = 1
            else:
                self.logInfo(_("*** Plugins have been updated, but need a pyLoad restart to be reloaded ***"))
                self.info['plugins'] = True
                exitcode = 2
        else:
            self.logInfo(_("No plugin updates available"))

        return exitcode  #: 0 = No plugins updated; 1 = Plugins updated; 2 = Plugins updated, but restart required


    @Expose
    def removePlugins(self, type_plugins):
        """ delete plugins from disk """

        if not type_plugins:
            return

        self.logDebug("Requested deletion of plugins: %s" % type_plugins)

        removed = []

        for type, name in type_plugins:
            err = False
            file = name + ".py"

            for root in ("userplugins", path.join(pypath, "pyload", "plugins")):

                filename = safe_join(root, type, file)
                try:
                    remove(filename)
                except Exception, e:
                    self.logDebug("Error deleting: %s" % path.basename(filename), e)
                    err = True

                filename += "c"
                if path.isfile(filename):
                    try:
                        if type == "addon":
                            self.manager.deactivateAddon(name)
                        remove(filename)
                    except Exception, e:
                        self.logDebug("Error deleting: %s" % path.basename(filename), e)
                        err = True

            if not err:
                id = (type, name)
                removed.append(id)

        return removed  #: return a list of the plugins successfully removed
