#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#  @author: Walter Purcaro
###############################################################################

from module.database import style
from module.plugins.Hook import Hook
from module.utils import save_join


class DeleteFinished(Hook):
    __name__ = "DeleteFinished"
    __version__ = "2.00"
    __description__ = """Automatically delete finished packages from queue"""
    __config__ = [("activated", "bool", "Activated", False),
                  ("interval", "int", "Smart check interval in hours (0 to run immediately)", 72),
                  ("del_offline", "bool", "Delete package with offline links", False),
                  ("del_password", "bool", "Delete package with password", True),
                  ("del_error", "bool", "Delete package with errors", True),
                  ("keep_latest", "int", "Number of latest packages to keep", 0),
                  ("log", "bool", "Log the list of packages deleted", True)]
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"

    def setup(self):
        self.scheduler = self.core.scheduler
        self.api = self.core.api

    def initPeriodical(self):
        pass

    def coreReady(self):
        self.packageFinished(None)

    def packageFinished(self, pypack):
        interval = max(self.getConfig("interval") * 60 * 60, 0)
        if not self.cb:
            self.interval = interval
            self.logDebug("Schedule a delete package task in %s seconds" % interval)
            self.cb = self.scheduler.addJob(interval, self.deleteFinished, threaded=False)
        elif self.interval != interval:
            self.scheduler.removeJob(self.cb)
            self.packageFinished(pypack)

    @style.queue
    def _deleteFinished(self, keep_latest, del_offline, del_password, del_error):
        self.c.execute('DELETE FROM packages WHERE queue %(password)s %(packageorder)s \
                        AND NOT EXISTS(SELECT 1 FROM links WHERE package = packages.id AND status NOT IN %(status)s %(error)s)' %
                       {"password": "" if del_password else "AND password = ''",
                        "packageorder": "AND packageorder < %s" % (len(self.api.getQueue()) - keep_latest) if keep_latest else "",
                        "status": "(0,1,4)" if del_offline else "(0,4)",
                        "error": "" if del_error else "AND error != ''"})
        self.c.execute('DELETE FROM links WHERE NOT EXISTS(SELECT 1 FROM packages WHERE id = links.package)')

    def deleteFinished(self):
        keep_latest = self.getConfig("keep_latest")
        del_offline = self.getConfig("del_offline")
        del_password = self.getConfig("del_password")
        del_error = self.getConfig("del_error")
        log = self.getConfig("log")

        if log:
            oldpacks = self.api.getQueue()

        self.logDebug("Run delete package task")
        self._deleteFinished(keep_latest, del_offline, del_password, del_error)
        self.cb = None

        if log:
            newqueue = self.core.db.getAllPackages(1)
            for p in oldpacks:
                if p.pid in newqueue:
                    continue
                folder = save_join("./", self.config["general"]["download_folder"], p.folder)
                self.logInfo("Deleted package \"%s\" (%s) containing %s link\s" % (p.name, folder, p.linkstotal))
        self.logInfo("Deleted finished packages from queue")
