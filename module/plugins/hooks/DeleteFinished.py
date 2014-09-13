# -*- coding: utf-8 -*-

from module.database import style
from module.plugins.Hook import Hook


class DeleteFinished(Hook):
    __name__ = "DeleteFinished"
    __type__ = "hook"
    __version__ = "1.09"

    __config__ = [('activated', 'bool', 'Activated', 'False'),
                  ('interval', 'int', 'Delete every (hours)', '72'),
                  ('deloffline', 'bool', 'Delete packages with offline links', 'False')]

    __description__ = """Automatically delete all finished packages from queue"""
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"


    ## overwritten methods ##
    def periodical(self):
        if not self.info['sleep']:
            deloffline = self.getConfig('deloffline')
            mode = '0,1,4' if deloffline else '0,4'
            msg = 'delete all finished packages in queue list (%s packages with offline links)'
            self.logInfo(msg % ('including' if deloffline else 'excluding'))
            self.deleteFinished(mode)
            self.info['sleep'] = True
            self.addEvent('packageFinished', self.wakeup)

    def pluginConfigChanged(self, plugin, name, value):
        if name == 'interval' and value != self.interval:
            self.interval = value * 3600
            self.initPeriodical()

    def unload(self):
        self.removeEvent('packageFinished', self.wakeup)

    def coreReady(self):
        self.info = {'sleep': True}
        interval = self.getConfig('interval')
        self.pluginConfigChanged('DeleteFinished', 'interval', interval)
        self.addEvent('packageFinished', self.wakeup)

    ## own methods ##
    @style.queue
    def deleteFinished(self, mode):
        self.c.execute('DELETE FROM packages WHERE NOT EXISTS(SELECT 1 FROM links WHERE package=packages.id AND status NOT IN (%s))' % mode)
        self.c.execute('DELETE FROM links WHERE NOT EXISTS(SELECT 1 FROM packages WHERE id=links.package)')

    def wakeup(self, pypack):
        self.removeEvent('packageFinished', self.wakeup)
        self.info['sleep'] = False

    ## event managing ##
    def addEvent(self, event, func):
        """Adds an event listener for event name"""
        if event in self.m.events:
            if func in self.m.events[event]:
                self.logDebug('Function already registered %s' % func)
            else:
                self.m.events[event].append(func)
        else:
            self.m.events[event] = [func]

    def setup(self):
        self.m = self.manager
        self.removeEvent = self.m.removeEvent
