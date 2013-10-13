# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: Walter Purcaro
"""

from module.database import style
from module.plugins.Hook import Hook


class DeleteFinished(Hook):
    __name__ = 'DeleteFinished'
    __version__ = '1.50'
    __description__ = 'Automatically delete finished packages from queue'
    __config__ = [('activated', 'bool', 'Activated', 'False'),
                  ('mode', 'immediately;periodically', 'Delete package mode', 'periodically'),
                  ('interval', 'int', 'Interval in hours', '72'),
                  ('del_offline', 'bool', 'Delete packages with offline links', 'False'),
                  ('del_password', 'bool', 'Delete packages with password', 'False'),
                  ('del_statusmsg', 'bool', 'Delete packages with custom link status messages', 'False'),
                  ('keep_latest', 'bool', 'Never delete lastest packages', 'False'),
                  ('pack_number', 'int', 'Number of latest packages to keep', '5')]
    __author_name__ = ('Walter Purcaro')
    __author_mail__ = ('vuolter@gmail.com')

    def setup(self):
        self.info = {}
        self.packageFinished_orig = self.packageFinished

    def initPeriodical(self):
        pass

    def coreReady(self):
        self.pluginConfigChanged(self.__name__, "mode", self.getConfig("mode"))

    def schedule(self):
        self.deleteFinished()
        self.packageFinished = self.wakeup
        self.info.schedule_cb = None

    def startTimer(self):
        self.info.schedule_cb = self.core.scheduler.addJob(self.getConfig("interval"), self.deleteFinished, threaded=False)

    def stopTimer(self):
        self.core.scheduler.removeJob(self.info.schedule_cb)
        self.info.schedule_cb = None

    def wakeup(self, arg1=None):
        self.packageFinished = self.packageFinished_orig
        self.startTimer()

    def pluginConfigChanged(self, plugin, name, value):
        if name == "mode":
            if value == "immediately":
                if self.info.schedule_cb:
                    self.stopTimer()
                self.packageFinished = self.deleteFinished
            else:
                self.wakeup()
        elif name == "interval" and self.info.schedule_cb:
            self.stopTimer()
            self.startTimer()

    @style.queue
    def delete(self, password, packageorder, status, statusmsg):
        self.c.execute('DELETE FROM packages WHERE queue ? ? AND NOT EXISTS(SELECT 1 FROM links WHERE package = packages.id AND status NOT IN (?)) ?',
                       (password, packageorder, status, statusmsg))
        self.c.execute('DELETE FROM links WHERE NOT EXISTS(SELECT 1 FROM packages WHERE id = links.package)')

    def deleteFinished(self, arg1=None):
        deloffline = self.getConfig('del_offline')
        delpassword = self.getConfig('del_password')
        delstatusmsg = self.getConfig('del_statusmsg')
        keeplatest = max(self.getConfig('keep_latest'), 1)
        packnumber = self.getConfig('pack_number')

        password = "AND NOT password" if not delpassword else ""
        packageorder = "AND packageorder < %s" % self.core.db._nextPackageOrder(1) - packnumber if keeplatest else ""
        statuscode = "0,4" if not deloffline else "0,1,4"
        statusmsg = "OR statusmsg" if not delstatusmsg else ""

        self.logInfo("delete packages from queue")
        self.delete(password=password, packageorder=packageorder, status=statuscode, statusmsg=statusmsg)
