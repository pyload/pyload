# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, division, unicode_literals

import io
import os
import re
import sys
from builtins import dict, zip
from time import time

from future import standard_library

from pyload.config.parser import IGNORE
from pyload.core.network import get_url

from . import Expose, Hook, threaded

standard_library.install_aliases()


class UpdateManager(Hook):
    __name__ = "UpdateManager"
    __version__ = "0.15"
    __description__ = """Checks for updates"""
    __config__ = [("activated", "bool", "Activated", True),
                  ("interval", "int", "Check interval in minutes", 480),
                  ("debug", "bool", "Check for plugin changes when in debug mode", False)]
    __author_name__ = "RaNaN"
    __author_mail__ = "ranan@pyload.net"

    URL = "http://get.pyload.net/check2/{}/"
    MIN_TIME = 3 * 60 * 60  #: 3h minimum check interval

    @property
    def debug(self):
        return self.pyload.debug and self.get_config("debug")

    def setup(self):
        if self.debug:
            self.log_debug("Monitoring file changes")
            self.interval = 4
            self.last_check = 0  #: timestamp of updatecheck
            self.old_periodical = self.periodical
            self.periodical = self.check_changes
            self.mtimes = {}  #: recordes times
        else:
            self.interval = max(self.get_config(
                "interval") * 60, self.MIN_TIME)

        self.updated = False
        self.reloaded = True
        self.version = "None"

        self.info = {'pyload': False, 'plugins': False}

    @threaded
    def periodical(self):

        updates = self.check_for_update()
        if updates:
            self.check_plugins(updates)

        if self.updated and not self.reloaded:
            self.info['plugins'] = True
            self.log_info(
                _("*** Plugins have been updated, please restart pyLoad ***"))
        elif self.updated and self.reloaded:
            self.log_info(_("Plugins updated and reloaded"))
            self.updated = False
        elif self.version == "None":
            self.log_info(_("No plugin updates available"))

    @Expose
    def recheck_for_updates(self):
        """
        Recheck if updates are available.
        """
        self.periodical()

    def check_for_update(self):
        """
        Checks if an update is available, return result.
        """
        try:
            if self.version == "None":  #: No updated known
                version_check = get_url(self.URL.format(
                    self.pyload.api.get_server_version()).splitlines())
                self.version = version_check[0]

                # Still no updates, plugins will be checked
                if self.version == "None":
                    self.log_info(_("No Updates for pyLoad"))
                    return version_check[1:]

            self.info['pyload'] = True
            self.log_info(
                _("***  New pyLoad Version {0} available  ***").format(self.version))
            self.log_info(
                _("***  Get it here: https://github.com/pyload/pyload/releases  ***"))

        except Exception:
            self.log_warning(_("Not able to connect server for updates"))

        return None  #: Nothing will be done

    def check_plugins(self, updates):
        """
        Checks for plugins updates.
        """

        # plugins were already updated
        if self.info['plugins']:
            return None

        reloads = []

        vre = re.compile(r'__version__.*=.*("|\')([0-9.]+)')
        url = updates[0]
        schema = updates[1].split("|")
        updates = updates[2:]

        for plugin in updates:
            info = dict(list(zip(schema, plugin.split("|"))))
            filename = info['name']
            prefix = info['type']
            version = info['version']

            if filename.endswith(".pyc"):
                name = filename[:filename.find("_")]
            else:
                name = filename.replace(".py", "")

            # TODO: obsolete in 0.5.0
            if prefix.endswith("s"):
                _type = prefix[:-1]
            else:
                _type = prefix

            plugins = getattr(self.pyload.pgm, "{0}Plugins".format(_type))

            if name in plugins:
                if float(plugins[name]['v']) >= float(version):
                    continue

            if name in IGNORE or (_type, name) in IGNORE:
                continue

            self.log_info(_("New version of {0}|{1} : {2:.2f}").format(
                _type, name, version))

            try:
                content = get_url(url.format(info))
            except Exception as e:
                self.log_warning(
                    _("Error when updating {0}").format(filename), e.message)
                continue

            m = vre.search(content)
            if not m or m.group(2) != version:
                self.log_warning(_("Error when updating {0}").format(
                    name), _("Version mismatch"))
                continue

            with io.open(os.path.join("userplugins", prefix, filename), mode='wb') as fp:
                fp.write(content)

            self.updated = True

            reloads.append((prefix, name))

        self.reloaded = self.pyload.pgm.reload_plugins(reloads)

    def check_changes(self):

        if self.last_check + \
                max(self.get_config("interval") * 60, self.MIN_TIME) < time():
            self.old_periodical()
            self.last_check = time()

        modules = [m for m in sys.modules.values() if m and (m.__name__.startswith("pyload.plugin.") or m.__name__.startswith(
            "userplugins.")) and m.__name__.count(".") >= 2]

        reloads = []

        for m in modules:
            root, _type, name = m.__name__.rsplit(".", 2)
            id = (_type, name)
            if _type in self.pyload.pgm.plugins:
                f = m.__file__.replace(".pyc", ".py")
                if not os.path.exists(f):
                    continue

                mtime = os.stat(f).st_mtime

                if id not in self.mtimes:
                    self.mtimes[id] = mtime
                elif self.mtimes[id] < mtime:
                    reloads.append(id)
                    self.mtimes[id] = mtime

        self.pyload.pgm.reload_plugins(reloads)
