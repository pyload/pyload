# -*- coding: utf-8 -*-

from module.database import style
from module.plugins.internal.Hook import Hook


class DeleteFinished(Hook):
    __name__    = "DeleteFinished"
    __type__    = "hook"
    __version__ = "1.13"

    __config__ = [("interval"  , "int" , "Check interval in hours"          , 72   ),
                  ("deloffline", "bool", "Delete package with offline links", False)]

    __description__ = """Automatically delete all finished packages from queue"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    MIN_CHECK_INTERVAL = 1 * 60 * 60  #: 1 hour


    ## overwritten methods ##
    def setup(self):
        self.info = {}  #@TODO: Remove in 0.4.10
        # self.event_list = ["pluginConfigChanged"]
        self.interval = self.MIN_CHECK_INTERVAL


    def periodical(self):
        if not self.info['sleep']:
            deloffline = self.getConfig('deloffline')
            mode = '0,1,4' if deloffline else '0,4'
            msg = _('delete all finished packages in queue list (%s packages with offline links)')
            self.logInfo(msg % (_('including') if deloffline else _('excluding')))
            self.deleteFinished(mode)
            self.info['sleep'] = True
            self.addEvent('package_finished', self.wakeup)


    # def pluginConfigChanged(self, plugin, name, value):
        # if name == "interval" and value != self.interval:
            # self.interval = value * 3600
            # self.init_periodical()


    def deactivate(self):
        self.manager.removeEvent('package_finished', self.wakeup)


    def activate(self):
        self.info['sleep'] = True
        # interval = self.getConfig('interval')
        # self.pluginConfigChanged(self.__name__, 'interval', interval)
        self.interval = max(self.MIN_CHECK_INTERVAL, self.getConfig('interval') * 60 * 60)
        self.addEvent('package_finished', self.wakeup)


    ## own methods ##
    @style.queue
    def deleteFinished(self, mode):
        self.c.execute('DELETE FROM packages WHERE NOT EXISTS(SELECT 1 FROM links WHERE package=packages.id AND status NOT IN (%s))' % mode)
        self.c.execute('DELETE FROM links WHERE NOT EXISTS(SELECT 1 FROM packages WHERE id=links.package)')


    def wakeup(self, pypack):
        self.manager.removeEvent('package_finished', self.wakeup)
        self.info['sleep'] = False


    ## event managing ##
    def addEvent(self, event, func):
        """
        Adds an event listener for event name
        """
        if event in self.manager.events:
            if func in self.manager.events[event]:
                self.logDebug("Function already registered", func)
            else:
                self.manager.events[event].append(func)
        else:
            self.manager.events[event] = [func]
