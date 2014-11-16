# -*- coding: utf-8 -*-

import re
import sys

from operator import itemgetter
from os import path, remove, stat

from module.network.RequestFactory import getURL
from module.plugins.Hook import Expose, Hook, threaded
from module.utils import save_join


class UpdateManager(Hook):
    __name__    = "UpdateManager"
    __type__    = "hook"
    __version__ = "0.39"

    __config__ = [("activated", "bool", "Activated", True),
                  ("mode", "pyLoad + plugins;plugins only", "Check updates for", "pyLoad + plugins"),
                  ("interval", "int", "Check interval in hours", 8),
                  ("reloadplugins", "bool", "Monitor plugins for code changes (debug mode only)", True),
                  ("nodebugupdate", "bool", "Don't check for updates in debug mode", True)]

    __description__ = """ Check for updates """
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    # event_list = ["pluginConfigChanged"]

    SERVER_URL = "http://updatemanager.pyload.org"
    MIN_INTERVAL = 6 * 60 * 60  #: 6h minimum check interval (value is in seconds)


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


    def coreReady(self):
        self.pluginConfigChanged(self.__name__, "interval", self.getConfig("interval"))
        x = lambda: self.pluginConfigChanged(self.__name__, "reloadplugins", self.getConfig("reloadplugins"))
        self.core.scheduler.addJob(10, x, threaded=False)


    def unload(self):
        self.pluginConfigChanged(self.__name__, "reloadplugins", False)


    def setup(self):
        self.cb2      = None
        self.interval = self.MIN_INTERVAL
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
            lambda m: m and (m.__name__.startswith("module.plugins.") or
                             m.__name__.startswith("userplugins.")) and
                             m.__name__.count(".") >= 2, sys.modules.itervalues()
        )

        reloads = []

        for m in modules:
            root, type, name = m.__name__.rsplit(".", 2)
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
        if not self.info['pyload'] and not (self.getConfig("nodebugupdate") and self.core.debug):
            self.updateThread()


    def server_request(self):
        try:
            return getURL(self.SERVER_URL, get={'version': self.core.api.getServerVersion()}).splitlines()
        except:
            self.logWarning(_("Unable to contact server to get updates"))


    @threaded
    def updateThread(self):
        self.updating = True

        status = self.update(onlyplugin=self.getConfig("mode") == "plugins only")

        if status == 2:
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

        vre = re.compile(r'__version__.*=.*("|\')([\d.]+)')
        url = updates[0]
        schema = updates[1].split('|')

        if "BLACKLIST" in updates:
            blacklist = updates[updates.index('BLACKLIST') + 1:]
            updates = updates[2:updates.index('BLACKLIST')]
        else:
            blacklist = None
            updates = updates[2:]

        upgradable = sorted(map(lambda x: dict(zip(schema, x.split('|'))), updates),
                            key=itemgetter("type", "name"))

        for plugin in upgradable:
            filename = plugin['name']
            prefix   = plugin['type']
            version  = plugin['version']

            if filename.endswith(".pyc"):
                name = filename[:filename.find("_")]
            else:
                name = filename.replace(".py", "")

            #@TODO: obsolete after 0.4.10
            if prefix.endswith("s"):
                type = prefix[:-1]
            else:
                type = prefix

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
                m = vre.search(content)

                if m and m.group(2) == version:
                    f = open(save_join("userplugins", prefix, filename), "wb")
                    f.write(content)
                    f.close()
                    updated.append((prefix, name))
                else:
                    raise Exception, _("Version mismatch")

            except Exception, e:
                self.logError(_("Error updating plugin %s") % filename, str(e))

        if blacklist:
            blacklisted = sorted(map(lambda x: (x.split('|')[0], x.split('|')[1].rsplit('.', 1)[0]), blacklist))

            # Always protect UpdateManager from self-removing
            try:
                blacklisted.remove(("hook", "UpdateManager"))
            except:
                pass

            removed = self.removePlugins(blacklisted)
            for t, n in removed:
                self.logInfo(_("Removed blacklisted plugin [%(type)s] %(name)s") % {
                    'type': t,
                    'name': n,
                })

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

            for root in ("userplugins", path.join(pypath, "module", "plugins")):

                filename = save_join(root, type, file)
                try:
                    remove(filename)
                except Exception, e:
                    self.logDebug("Error removing: %s" % path.basename(filename), str(e))
                    err = True

                filename += "c"
                if path.isfile(filename):
                    try:
                        if type == "hook":
                            self.manager.deactivateHook(name)
                        remove(filename)
                    except Exception, e:
                        self.logDebug("Error removing: %s" % path.basename(filename), str(e))
                        err = True

            if not err:
                id = (type, name)
                removed.append(id)

        return removed  #: return a list of the plugins successfully removed
