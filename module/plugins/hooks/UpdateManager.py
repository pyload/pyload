# -*- coding: utf-8 -*-

from __future__ import with_statement

import operator
import os
import re
import sys
import time

from module.plugins.internal.Addon import Expose, Addon, threaded
from module.plugins.internal.Plugin import exists
from module.utils import fs_encode, save_join as fs_join


class UpdateManager(Addon):
    __name__    = "UpdateManager"
    __type__    = "hook"
    __version__ = "1.00"
    __status__  = "testing"

    __config__ = [("activated"    , "bool", "Activated"                                , True ),
                  ("checkinterval", "int" , "Check interval in hours"                  , 8    ),
                  ("autorestart"  , "bool", "Auto-restart pyLoad when required"        , True ),
                  ("checkonstart" , "bool", "Check for updates on startup"             , True ),
                  ("checkperiod"  , "bool", "Check for updates periodically"           , True ),
                  ("reloadplugins", "bool", "Monitor plugin code changes in debug mode", True ),
                  ("nodebugupdate", "bool", "Don't update plugins in debug mode"       , False)]

    __description__ = """Check for updates"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    _VERSION = re.compile(r'__version__.*=.*("|\')([\d.]+)')

    SERVER_URL = "http://updatemanager.pyload.org"

    PERIODICAL_INTERVAL = 3 * 60 * 60  #: 3 hours


    def activate(self):
        if self.checkonstart:
            self.pyload.api.pauseServer()
            self.update()

            if self.do_restart is False:
                self.pyload.api.unpauseServer()

        self.start_periodical(10)


    def init(self):
        self.info      = {'pyload': False, 'plugins': False, 'last_check': time.time()}
        self.mtimes    = {}  #: Store modification time for each plugin
        self.event_map = {'allDownloadsProcessed': "all_downloads_processed"}

        if self.get_config('checkonstart'):
            self.pyload.api.pauseServer()
            self.checkonstart = True
        else:
            self.checkonstart = False

        self.do_restart = False


    def all_downloads_processed(self):
        if self.do_restart is True:
            self.log_warning(_("Downloads are done, restarting pyLoad to reload the updated plugins"))
            self.pyload.api.restart()


    def periodical(self):
        if self.pyload.debug:
            if self.get_config('reloadplugins'):
                self.autoreload_plugins()

            if self.get_config('nodebugupdate'):
                return

        if self.get_config('checkperiod') and \
           time.time() - max(self.PERIODICAL_INTERVAL, self.get_config('checkinterval') * 60 * 60) > self.info['last_check']:
            self.update()


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
            root, type, name = m.__name__.rsplit(".", 2)
            id = (type, name)
            if type in self.pyload.pluginManager.plugins:
                f = m.__file__.replace(".pyc", ".py")
                if not os.path.isfile(f):
                    continue

                mtime = os.path.getmtime(f)

                if id not in self.mtimes:
                    self.mtimes[id] = mtime

                elif self.mtimes[id] < mtime:
                    reloads.append(id)
                    self.mtimes[id] = mtime

        return True if self.pyload.pluginManager.reloadPlugins(reloads) else False


    def server_response(self, line=None):
        try:
            html = self.load(self.SERVER_URL,
                             get={'v': self.pyload.api.getServerVersion()})

        except Exception:
            self.log_warning(_("Unable to retrieve server to get updates"))

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
        if self._update() is not 2 or not self.get_config('autorestart'):
            return

        if not self.pyload.api.statusDownloads():
            self.pyload.api.restart()
        else:
            self.do_restart = True
            self.log_warning(_("Downloads are active, will restart once the download is done"))
            self.pyload.api.pauseServer()


    def _update(self):
        newversion = self.server_response(0)

        self.info['pyload']     = False
        self.info['last_check'] = time.time()

        if not newversion:
            exitcode = 0

        elif newversion == "None":
            self.log_info(_("No new pyLoad version available"))
            exitcode = self.update_plugins()

        else:
            self.log_info(_("***  New pyLoad Version %s available  ***") % newversion)
            self.log_info(_("***  Get it here: https://github.com/pyload/pyload/releases  ***"))
            self.info['pyload'] = True
            exitcode = 3

        #: Exit codes:
        #:  -1 = No plugin updated, new pyLoad version available
        #:   0 = No plugin updated
        #:   1 = Plugins updated
        #:   2 = Plugins updated, but restart required
        return exitcode


    @Expose
    def update_plugins(self):
        updates = self.server_response()

        if not updates or updates[0] != "None":
            return 0

        updated = self._update_plugins(updates)

        if updated:
            self.log_info(_("*** Plugins updated ***"))

            if self.pyload.pluginManager.reloadPlugins(updated):
                exitcode = 1
            else:
                self.log_warning(_("You have to restart pyLoad to reload the updated plugins"))
                self.info['plugins'] = True
                exitcode = 2

            self.manager.dispatchEvent("plugin_updated", updated)
        else:
            self.log_info(_("*** No plugin updates available ***"))
            exitcode = 0

        #: Exit codes:
        #:   0 = No plugin updated
        #:   1 = Plugins updated
        #:   2 = Plugins updated, but restart required
        return exitcode


    def parse_list(self, list):
        schema = list[2].split('|')

        if "BLACKLIST" in list:
            blacklist  = list[list.index('BLACKLIST') + 1:]
            updatelist = list[3:list.index('BLACKLIST')]
        else:
            blacklist  = []
            updatelist = list[3:]

        for l in updatelist, blacklist:
            nl = []
            for line in l:
                d = dict(zip(schema, line.split('|')))
                d['name'] = d['name'].rsplit('.py', 1)[0]
                d['type'] = d['type'].rstrip('s')
                nl.append(d)
            l[:] = nl

        updatelist = sorted(updatelist, key=operator.itemgetter("type", "name"))
        blacklist  = sorted(blacklist, key=operator.itemgetter("type", "name"))

        return updatelist, blacklist


    def _update_plugins(self, updates):
        """
        Check for plugin updates
        """
        updated = []

        updatelist, blacklist = self.parse_list(updates)

        url = updates[1]

        if blacklist:
            #@NOTE: Protect UpdateManager from self-removing
            type_plugins = [(plugin['type'], plugin['name']) for plugin in blacklist \
                            if plugin['name'] is not self.classname and plugin['type'] is not self.__type__]

            c = 1
            l = len(type_plugins)
            for idx, plugin in enumerate(updatelist):
                if c > l:
                    break
                name = plugin['name']
                type = plugin['type']
                for t, n in type_plugins:
                    if n != name or t != type:
                        continue
                    updatelist.pop(idx)
                    c += 1
                    break

            for t, n in self.remove_plugins(type_plugins):
                self.log_info(_("Removed blacklisted plugin: %(type)s %(name)s") % {
                    'type': t.upper(),
                    'name': n,
                })

        for plugin in updatelist:
            name    = plugin['name']
            type    = plugin['type']
            version = plugin['version']

            plugins = getattr(self.pyload.pluginManager, "%sPlugins" % type)

            oldver = float(plugins[name]['v']) if name in plugins else None
            newver = float(version)

            if not oldver:
                msg = "New plugin: %(type)s %(name)s (v%(newver).2f)"
            elif newver > oldver:
                msg = "New version of plugin: %(type)s %(name)s (v%(oldver).2f -> v%(newver).2f)"
            else:
                continue

            self.log_info(_(msg) % {'type'  : type.upper(),
                                    'name'  : name,
                                    'oldver': oldver,
                                    'newver': newver})
            try:
                content = self.load(url % plugin + ".py", decode=False)
                m = self._VERSION.search(content)

                if m and m.group(2) == version:
                    #@TODO: Remove in 0.4.10
                    if type in ("account", "hook"):
                        folder = type + "s"
                    else:
                        folder = type

                    with open(fs_join("userplugins", folder, name + ".py"), "wb") as f:
                        f.write(fs_encode(content))

                    updated.append((type, name))
                else:
                    raise Exception(_("Version mismatch"))

            except Exception, e:
                self.log_error(_("Error updating plugin: %s %s") % (type.upper(), name), e)

        return updated


    #: Deprecated method, use `remove_plugins` instead
    @Expose
    def removePlugins(self, *args, **kwargs):
        """
        See `remove_plugins`
        """
        return self.remove_plugins(*args, **kwargs)


    @Expose
    def remove_plugins(self, type_plugins):
        """
        Delete plugins from disk
        """
        if not type_plugins:
            return

        removed = set()

        self.log_debug("Requested deletion of plugins: %s" % type_plugins)

        for type, name in type_plugins:
            rootplugins = os.path.join(pypath, "module", "plugins")

            #@TODO: Remove in 0.4.10
            if type in ("account", "hook"):
                folder = type + "s"
            else:
                folder = type

            for dir in ("userplugins", rootplugins):
                py_filename  = fs_join(dir, folder, name + ".py")
                pyc_filename = py_filename + "c"

                if type is "hook":
                    try:
                        self.manager.deactivateHook(name)

                    except Exception, e:
                        self.log_debug(e, trace=True)

                for filename in (py_filename, pyc_filename):
                    if not exists(filename):
                        continue

                    try:
                        os.remove(filename)

                    except OSError, e:
                        self.log_warning(_("Error removing: %s") % filename, e)

                    else:
                        id = (type, name)
                        removed.add(id)

        return list(removed)  #: Return a list of the plugins successfully removed
