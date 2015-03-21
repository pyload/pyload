# -*- coding: utf-8 -*-

from module.database import style
from module.plugins.Hook import Hook


class DeleteFinished(Hook):
    __name__    = "DeleteFinished"
    __type__    = "hook"
    __version__ = "1.12"

    __config__ = [("activated" , "bool", "Activated"                         , "False"),
                  ("interval"  , "int" , "Delete every (hours)"              , "72"   ),
                  ("deloffline", "bool", "Delete packages with offline links", "False")]

    __description__ = """Automatically delete all finished packages from queue"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    # event_list = ["pluginConfigChanged"]

    MIN_CHECK_INTERVAL = 1 * 60 * 60  #: 1 hour


    ## overwritten methods ##
    def setup(self):
        self.info     = {}  #@TODO: Remove in 0.4.10
        self.interval = self.MIN_CHECK_INTERVAL


    def periodical(self):
        if not self.info['sleep']:
            deloffline = self.getConfig('deloffline')
            mode = '0,1,4' if deloffline else '0,4'
            msg = _('delete all finished packages in queue list (%s packages with offline links)')
            self.logInfo(msg % (_('including') if deloffline else _('excluding')))
            self.deleteFinished(mode)
            self.info['sleep'] = True
            self.addEvent('packageFinished', self.wakeup)


    # def pluginConfigChanged(self, plugin, name, value):
        # if name == "interval" and value != self.interval:
            # self.interval = value * 3600
            # self.initPeriodical()


    def unload(self):
        self.manager.removeEvent('packageFinished', self.wakeup)


    def coreReady(self):
        self.info['sleep'] = True
        # interval = self.getConfig('interval')
        # self.pluginConfigChanged(self.__name__, 'interval', interval)
        self.interval = max(self.MIN_CHECK_INTERVAL, self.getConfig('interval') * 60 * 60)
        self.addEvent('packageFinished', self.wakeup)


    ## own methods ##
    @style.queue
    def deleteFinished(self, mode):
        self.c.execute('DELETE FROM packages WHERE NOT EXISTS(SELECT 1 FROM links WHERE package=packages.id AND status NOT IN (%s))' % mode)
        self.c.execute('DELETE FROM links WHERE NOT EXISTS(SELECT 1 FROM packages WHERE id=links.package)')


    def wakeup(self, pypack):
        self.manager.removeEvent('packageFinished', self.wakeup)
        self.info['sleep'] = False


    ## event managing ##
    def addEvent(self, event, func):
        """Adds an event listener for event name"""
        if event in self.manager.events:
            if func in self.manager.events[event]:
                self.logDebug("Function already registered", func)
            else:
                self.manager.events[event].append(func)
        else:
            self.manager.events[event] = [func]
