# -*- coding: utf-8 -*-

from __future__ import with_statement

import operator
import os
import re
import sys
import time

from ..internal.Addon import Addon
from ..internal.misc import Expose, encode, exists, fsjoin, threaded


class UpdateManager(Addon):
    __name__ = "UpdateManager"
    __type__ = "hook"
    __version__ = "1.21"
    __status__ = "testing"

    __config__ = [("activated", "bool", "Activated", True),
                  ("checkinterval", "int", "Check interval in hours", 6),
                  ("autorestart", "bool", "Auto-restart pyLoad when required", True),
                  ("checkonstart", "bool", "Check for updates on startup", True),
                  ("checkperiod", "bool", "Check for updates periodically", True),
                  ("reloadplugins", "bool", "Monitor plugin code changes in debug mode", True),
                  ("nodebugupdate", "bool", "Don't update plugins in debug mode", False)]

    __description__ = """Check for updates"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    _VERSION = re.compile(r'^\s*__version__\s*=\s*("|\')([\d.]+)\1', re.M)

    # SERVER_URL     = "http://updatemanager.pyload.org"
    # SERVER_URL = "http://updatemanager-spyload.rhcloud.com"
    SERVER_URL = "https://raw.githubusercontent.com/pyload/updates/master/plugins.txt"
    CHECK_INTERVAL = 3 * 60 * 60  #: 3 hours

    def activate(self):
        if self.checkonstart:
            self.pyload.api.pauseServer()
            self.update()

            if self.do_restart is False:
                self.pyload.api.unpauseServer()

        self.periodical.start(10)

    def init(self):
        self.info.update({
            'pyload': False,
            'plugins': False,
            'last_check': time.time()})
        self.mtimes = {}  #: Store modification time for each plugin
        self.event_map = {'allDownloadsProcessed': "all_downloads_processed"}

        if self.config.get('checkonstart'):
            self.pyload.api.pauseServer()
            self.checkonstart = True
        else:
            self.checkonstart = False

        self.do_restart = False

    def all_downloads_processed(self):
        if self.do_restart is True:
            self.pyload.api.restart()

    def periodical_task(self):
        if self.pyload.debug:
            if self.config.get('reloadplugins'):
                self.autoreload_plugins()

            if self.config.get('nodebugupdate'):
                return

        if self.config.get('checkperiod') and \
           time.time() - max(self.CHECK_INTERVAL, self.config.get('checkinterval') * 60 * 60) > self.info['last_check']:
            self.update()

        if self.do_restart is True:
            if self.pyload.threadManager.pause and not self.pyload.api.statusDownloads():
                self.pyload.api.restart()

    #: Deprecated method, use `autoreload_plugins` instead
    @Expose
    def autoreloadPlugins(self, *args, **kwargs):
        """
        See `autoreload_plugins`
        """
        return self.autoreload_plugins(*args, **kwargs)

    @Expose
    def autoreload_plugins(self):
        """
        Reload and reindex all modified plugins
        """
        reloads = []
        modules = filter(
            lambda m: m and (m.__name__.startswith("module.plugins.") or
                             m.__name__.startswith("userplugins.")) and
            m.__name__.count(".") >= 2, sys.modules.values()
        )
        for m in modules:
            root, plugin_type, plugin_name = m.__name__.rsplit(".", 2)
            plugin_id = (plugin_type, plugin_name)
            if plugin_type in self.pyload.pluginManager.plugins:
                f = m.__file__.replace(".pyc", ".py")
                if not os.path.isfile(f):
                    continue

                mtime = os.path.getmtime(f)

                if plugin_id not in self.mtimes:
                    self.mtimes[plugin_id] = mtime

                elif self.mtimes[plugin_id] < mtime:
                    reloads.append(plugin_id)
                    self.mtimes[plugin_id] = mtime

        return True if self.pyload.pluginManager.reloadPlugins(reloads) else False

    def server_response(self, line=None):
        try:
            html = self.load(self.SERVER_URL,
                             get={'v': self.pyload.api.getServerVersion()})

        except Exception:
            self.log_warning(_("Unable to connect to the server to retrieve updates"))

        else:
            res = html.splitlines()

            if line is not None:
                try:
                    res = res[line]
                except IndexError:
                    res = None

            return res

    @Expose
    @threaded
    def update(self):
        """
        Check for updates
        """
        if self._update() != 2 or not self.config.get('autorestart'):
            return

        if not self.pyload.api.statusDownloads():
            self.pyload.api.restart()
        else:
            self.log_warning(_("pyLoad restart scheduled"),
                             _("Downloads are active, pyLoad restart postponed once the download is done"))
            self.pyload.api.pauseServer()
            self.do_restart = True

    def _update(self):
        newversion = self.server_response(0)

        self.info['pyload'] = False
        self.info['last_check'] = time.time()

        if not newversion:
            exitcode = 0

        elif newversion == self.pyload.api.getServerVersion():
            self.log_info(_("pyLoad is up to date!"))
            exitcode = self.update_plugins()

        elif re.search(r'^\d+(?:\.\d+){0,3}[a-z]?$', newversion):
            self.log_info(_("***  New pyLoad %s available  ***") % newversion)
            self.log_info(_("***  Get it here: https://github.com/pyload/pyload/releases  ***"))
            self.info['pyload'] = True
            exitcode = 3

        else:
            exitcode = 0

        #: Exit codes:
        #:  -1 = No plugin updated, new pyLoad version available
        #:   0 = No plugin updated
        #:   1 = Plugins updated
        #:   2 = Plugins updated, but restart required
        return exitcode

    @Expose
    def update_plugins(self):
        server_data = self.server_response()

        if not server_data or server_data[0] != self.pyload.api.getServerVersion():
            return 0

        updated = self._update_plugins(server_data)

        if updated:
            self.log_info(_("*** Plugins updated ***"))

            if self.pyload.pluginManager.reloadPlugins(updated):
                exitcode = 1
            else:
                self.log_warning(_("You have to restart pyLoad to use the updated plugins"))
                self.info['plugins'] = True
                exitcode = 2

            paused = self.pyload.threadManager.pause
            self.pyload.api.pauseServer()
            self.manager.dispatchEvent("plugin_updated", updated)
            if not paused:
                self.pyload.api.unpauseServer()
        else:
            self.log_info(_("All plugins are up to date!"))
            exitcode = 0

        #: Exit codes:
        #:   0 = No plugin updated
        #:   1 = Plugins updated
        #:   2 = Plugins updated, but restart required
        return exitcode

    def parse_updates(self, server_data):
        schema = server_data[2].split('|')

        if "BLACKLIST" in server_data:
            blacklist = server_data[server_data.index('BLACKLIST') + 1:]
            updatelist = server_data[3:server_data.index('BLACKLIST')]
        else:
            blacklist = []
            updatelist = server_data[3:]

        for l in updatelist, blacklist:
            nl = []
            for line in l:
                d = dict(zip(schema, line.split('|')))
                d['name'] = d['name'].rsplit('.py', 1)[0]
                nl.append(d)
            l[:] = nl

        updatelist = sorted(updatelist,
                            key=operator.itemgetter("type", "name"))
        blacklist = sorted(blacklist, key=operator.itemgetter("type", "name"))

        return updatelist, blacklist

    def _update_plugins(self, server_data):
        """
        Check for plugin updates
        """
        updated = []

        updatelist, blacklist = self.parse_updates(server_data)

        url = server_data[1]
        req = self.pyload.requestFactory.getRequest(self.classname)

        if blacklist:
            #@NOTE: Protect UpdateManager from self-removing
            if os.name == "nt":
                #@NOTE: Windows filesystem is case insensitive, make sure we do not delete legitimate plugins
                whitelisted_plugins = [
                    (plugin['type'], plugin['name'].upper()) for plugin in updatelist]
                blacklisted_plugins = [(plugin['type'], plugin['name']) for plugin in blacklist
                                       if not (plugin['name'] == self.classname and plugin['type'] == self.__type__)
                                       and (plugin['type'], plugin['name'].upper()) not in whitelisted_plugins]
            else:
                blacklisted_plugins = [(plugin['type'], plugin['name']) for plugin in blacklist
                                       if not (plugin['name'] == self.classname and plugin['type'] == self.__type__)]

            c = 1
            l = len(blacklisted_plugins)
            for idx, plugin in enumerate(updatelist):
                if c > l:
                    break
                plugin_name = plugin['name']
                plugin_type = plugin['type']
                for t, n in blacklisted_plugins:
                    if n != plugin_name or t != plugin_type:
                        continue
                    updatelist.pop(idx)
                    c += 1
                    break

            for t, n in self.remove_plugins(blacklisted_plugins):
                self.log_info(_("Removed blacklisted plugin: %(type)s %(name)s") %
                              {'type': t.upper(),
                               'name': n,})

        for plugin in updatelist:
            plugin_name = plugin['name']
            plugin_type = plugin['type']
            plugin_version = plugin['version']

            plugins = getattr(self.pyload.pluginManager,
                              "%sPlugins" % plugin_type.rstrip('s'))  # @TODO: Remove rstrip in 0.4.10

            oldver = float(plugins[plugin_name]['v']) if plugin_name in plugins else None
            try:
                newver = float(plugin_version)
            except ValueError:
                self.log_error(_("Error updating plugin: %s %s") % (plugin_type.rstrip('s').upper(), plugin_name),
                               _("Bad version number on the server"))
                continue

            if not oldver:
                msg = "New plugin: %(type)s %(name)s (v%(newver).2f)"
            elif newver > oldver:
                msg = "New version of plugin: %(type)s %(name)s (v%(oldver).2f -> v%(newver).2f)"
            else:
                continue

            self.log_info(_(msg) % {'type': plugin_type.rstrip('s').upper(),  # @TODO: Remove rstrip in 0.4.10
                                    'name': plugin_name,
                                    'oldver': oldver,
                                    'newver': newver})
            try:
                content = self.load(url % plugin + ".py", decode=False, req=req)

                if req.code == 404:
                    raise Exception(_("URL not found"))

                m = self._VERSION.search(content)
                if m and m.group(2) == plugin_version:
                    with open(fsjoin("userplugins", plugin_type, plugin_name + ".py"), "wb") as f:
                        f.write(encode(content))

                    updated.append((plugin_type, plugin_name))
                else:
                    raise Exception(_("Version mismatch"))

            except Exception, e:
                self.log_error(_("Error updating plugin: %s %s") %
                               (plugin_type.rstrip('s').upper(), plugin_name),
                               e)  # @TODO: Remove rstrip in 0.4.10

        return updated

    #: Deprecated method, use `remove_plugins` instead
    @Expose
    def removePlugins(self, *args, **kwargs):
        """
        See `remove_plugins`
        """
        return self.remove_plugins(*args, **kwargs)

    @Expose
    def remove_plugins(self, plugin_ids):
        """
        Delete plugins from disk
        """
        if not plugin_ids:
            return

        removed = set()

        self.log_debug("Requested deletion of plugins: %s" % plugin_ids)

        for plugin_type, plugin_name in plugin_ids:
            rootplugins = os.path.join(pypath, "module", "plugins")

            for basedir in ("userplugins", rootplugins):
                py_filename = fsjoin(basedir, plugin_type, plugin_name + ".py")
                pyc_filename = py_filename + "c"

                if plugin_type == "hook":
                    try:
                        self.manager.deactivateHook(plugin_name)

                    except Exception, e:
                        self.log_debug(e, trace=True)

                for filename in (py_filename, pyc_filename):
                    if not exists(filename):
                        continue

                    try:
                        os.remove(filename)

                    except OSError, e:
                        self.log_warning(_("Error removing `%s`") % filename, e)

                    else:
                        plugin_id = (plugin_type, plugin_name)
                        removed.add(plugin_id)

        #: Return a list of the plugins successfully removed
        return list(removed)
