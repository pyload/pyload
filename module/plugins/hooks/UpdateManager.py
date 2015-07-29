# -*- coding: utf-8 -*-

from __future__ import with_statement

import operator
import os
import re
import sys
import time
import traceback

from module.plugins.internal.Addon import Expose, Addon, threaded
from module.plugins.internal.Plugin import exists
from module.utils import fs_encode, save_join as fs_join


class UpdateManager(Addon):
    __name__    = "UpdateManager"
    __type__    = "hook"
    __version__ = "0.55"
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


    interval = 0

    SERVER_URL         = "http://updatemanager.pyload.org"
    MIN_CHECK_INTERVAL = 3 * 60 * 60  #: 3 hours


    def activate(self):
        if self.checkonstart:
            self.pyload.api.pauseServer()
            self.update()
            if self.do_restart is False:
                self.pyload.api.unpauseServer()

        self.init_periodical()


    def init(self):
        self.info     = {'pyload': False, 'version': None, 'plugins': False, 'last_check': time.time()}
        self.mtimes   = {}  #: Store modification time for each plugin

        self.event_map = {'allDownloadsProcessed': "all_downloads_processed"}

        self.interval = 10

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

        if self.get_config('checkperiod') \
           and time.time() - max(self.MIN_CHECK_INTERVAL, self.get_config('checkinterval') * 60 * 60) > self.info['last_check']:
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
        modules = filter(
            lambda m: m and (m.__name__.startswith("module.plugins.") or
                             m.__name__.startswith("userplugins.")) and
                             m.__name__.count(".") >= 2, sys.modules.values()
        )

        reloads = []

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


    def server_response(self):
        try:
            return self.load(self.SERVER_URL,
                             get={'v': self.pyload.api.getServerVersion()}).splitlines()

        except Exception:
            self.log_warning(_("Unable to retrieve server to get updates"))


    @Expose
    @threaded
    def update(self):
        """
        Check for updates
        """
        if self._update() == 2 and self.get_config('autorestart'):
            if not self.pyload.api.statusDownloads():
                self.pyload.api.restart()
            else:
                self.do_restart = True
                self.log_warning(_("Downloads are active, will restart once the download is done"))
                self.pyload.api.pauseServer()


    def _update(self):
        data = self.server_response()

        self.info['last_check'] = time.time()

        if not data:
            exitcode = 0

        elif data[0] == "None":
            self.log_info(_("No new pyLoad version available"))
            exitcode = self._update_plugins(data[1:])

        elif onlyplugin:
            exitcode = 0

        else:
            self.log_info(_("***  New pyLoad Version %s available  ***") % data[0])
            self.log_info(_("***  Get it here: https://github.com/pyload/pyload/releases  ***"))
            self.info['pyload']  = True
            self.info['version'] = data[0]
            exitcode = 3

        #: Exit codes:
        #:  -1 = No plugin updated, new pyLoad version available
        #:   0 = No plugin updated
        #:   1 = Plugins updated
        #:   2 = Plugins updated, but restart required
        return exitcode


    def _update_plugins(self, data):
        """
        Check for plugin updates
        """
        exitcode = 0
        updated  = []

        url    = data[0]
        schema = data[1].split('|')

        VERSION = re.compile(r'__version__.*=.*("|\')([\d.]+)')

        if "BLACKLIST" in data:
            blacklist  = data[data.index('BLACKLIST') + 1:]
            updatelist = data[2:data.index('BLACKLIST')]
        else:
            blacklist  = []
            updatelist = data[2:]

        updatelist = [dict(zip(schema, x.split('|'))) for x in updatelist]
        blacklist  = [dict(zip(schema, x.split('|'))) for x in blacklist]

        if blacklist:
            type_plugins = [(plugin['type'], plugin['name'].rsplit('.', 1)[0]) for plugin in blacklist]

            #: Protect UpdateManager from self-removing
            try:
                type_plugins.remove(("hook", "UpdateManager"))
            except ValueError:
                pass

            for t, n in type_plugins:
                for idx, plugin in enumerate(updatelist):
                    if n is plugin['name'] and t is plugin['type']:
                        updatelist.pop(idx)
                        break

            for t, n in self.remove_plugins(sorted(type_plugins)):
                self.log_info(_("Removed blacklisted plugin: [%(type)s] %(name)s") % {
                    'type': t,
                    'name': n,
                })

        for plugin in sorted(updatelist, key=operator.itemgetter("type", "name")):
            filename = plugin['name']
            prefix   = plugin['type']
            version  = plugin['version']

            if filename.endswith(".pyc"):
                name = filename[:filename.find("_")]
            else:
                name = filename.replace(".py", "")

            #@TODO: Remove in 0.4.10
            if prefix.endswith("s"):
                type = prefix[:-1]
            else:
                type = prefix

            plugins = getattr(self.pyload.pluginManager, "%sPlugins" % type)

            oldver = float(plugins[name]['v']) if name in plugins else None
            newver = float(version)

            if not oldver:
                msg = "New plugin: [%(type)s] %(name)s (v%(newver).2f)"
            elif newver > oldver:
                msg = "New version of plugin: [%(type)s] %(name)s (v%(oldver).2f -> v%(newver).2f)"
            else:
                continue

            self.log_info(_(msg) % {'type'  : type,
                                   'name'  : name,
                                   'oldver': oldver,
                                   'newver': newver})
            try:
                content = self.load(url % plugin, decode=False)
                m = VERSION.search(content)

                if m and m.group(2) == version:
                    with open(fs_join("userplugins", prefix, filename), "wb") as f:
                        f.write(fs_encode(content))

                    updated.append((prefix, name))
                else:
                    raise Exception(_("Version mismatch"))

            except Exception, e:
                self.log_error(_("Error updating plugin: %s") % filename, e)
                if self.pyload.debug:
                    traceback.print_exc()

        if updated:
            self.log_info(_("*** Plugins updated ***"))

            if self.pyload.pluginManager.reloadPlugins(updated):
                exitcode = 1
            else:
                self.log_warning(_("pyLoad restart required to reload the updated plugins"))
                self.info['plugins'] = True
                exitcode = 2

            self.manager.dispatchEvent("plugin_updated", updated)
        else:
            self.log_info(_("No plugin updates available"))

        #: Exit codes:
        #:   0 = No plugin updated
        #:   1 = Plugins updated
        #:   2 = Plugins updated, but restart required
        return exitcode


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

            for dir in ("userplugins", rootplugins):
                py_filename  = fs_join(dir, type, name + ".py")
                pyc_filename = py_filename + "c"

                if type == "hook":
                    try:
                        self.manager.deactivateHook(name)

                    except Exception, e:
                        self.log_debug(e)

                for filename in (py_filename, pyc_filename):
                    if not exists(filename):
                        continue

                    try:
                        os.remove(filename)

                    except OSError, e:
                        self.log_warning(_("Error removing: %s") % filename, e)
                        if self.pyload.debug:
                            traceback.print_exc()

                    else:
                        id = (type, name)
                        removed.add(id)

        return list(removed)  #: Return a list of the plugins successfully removed
