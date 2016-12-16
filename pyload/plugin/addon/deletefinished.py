# -*- coding: utf-8 -*-
#@author: Walter Purcaro

from __future__ import unicode_literals

from pyload.database import style
from pyload.plugins.hook import Hook


class DeleteFinished(Hook):
    __name__ = 'DeleteFinished'
    __version__ = '1.09'
    __description__ = 'Automatically delete all finished packages from queue'
    __config__ = [
        ('activated', 'bool', 'Activated', 'False'),
        ('interval', 'int', 'Delete every (hours)', '72'),
        ('deloffline', 'bool', 'Delete packages with offline links', 'False')
    ]
    __author_name__ = ('Walter Purcaro')
    __author_mail__ = ('vuolter@gmail.com')

    ## overwritten methods ##
    def periodical(self):
        if not self.info['sleep']:
            deloffline = self.get_config('deloffline')
            mode = '0,1,4' if deloffline else '0,4'
            msg = 'delete all finished packages in queue list (%s packages with offline links)'
            self.log_info(msg % ('including' if deloffline else 'excluding'))
            self.delete_finished(mode)
            self.info['sleep'] = True
            self.add_event('packageFinished', self.wakeup)

    def plugin_config_changed(self, plugin, name, value):
        if name == 'interval' and value != self.interval:
            self.interval = value * 3600
            self.init_periodical()

    def unload(self):
        self.remove_event('packageFinished', self.wakeup)

    def core_ready(self):
        self.info = {'sleep': True}
        interval = self.get_config('interval')
        self.plugin_config_changed('DeleteFinished', 'interval', interval)
        self.add_event('packageFinished', self.wakeup)

    ## own methods ##
    @style.queue
    def delete_finished(self, mode):
        self.c.execute('DELETE FROM packages WHERE NOT EXISTS(SELECT 1 FROM links WHERE package=packages.id AND status NOT IN (%s))' % mode)
        self.c.execute('DELETE FROM links WHERE NOT EXISTS(SELECT 1 FROM packages WHERE id=links.package)')

    def wakeup(self, pypack):
        self.remove_event('packageFinished', self.wakeup)
        self.info['sleep'] = False

    ## event managing ##
    def add_event(self, event, func):
        """Adds an event listener for event name"""
        if event in self.manager.events:
            if func in self.manager.events[event]:
                self.log_debug('Function already registered %s' % func)
            else:
                self.manager.events[event].append(func)
        else:
            self.manager.events[event] = [func]

    def setup(self):
        self.manager = self.manager
        self.remove_event = self.manager.remove_event
