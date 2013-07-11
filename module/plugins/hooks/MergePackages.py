  # -*- coding: utf-8 -*-

'''
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
'''

from module.plugins.Hook import Hook
from re import sub


class MergePackages(Hook):
    __name__ = 'MergePackages'
    __version__ = '0.07'
    __description__ = 'Merges added package to an existing one with same name'
    __config__ = [
        ('activated', 'bool', 'Activated', 'False'),
        ('exactmatch', 'bool', 'Exact match', 'False'),
        ('listorder', 'queue;collector', 'List to check first', 'queue'),
        ('samelist', 'bool', 'Don\'t merge package if destination list is different', 'True'),
        ('doublecheck', 'bool', 'Don\'t merge link if already exists', 'True')
    ]
    __author_name__ = ('Walter Purcaro')
    __author_mail__ = ('vuolter@gmail.com')

    event_map = {'linksAdded': 'mergePackages'}

    def doubleCheck(self, links, pid):
        self.logDebug('starting pre-merge duplicate links check')
        pypack = self.api.getPackageData(pid)
        for url in links:
            for link in pypack.links:
                if url == link.url:
                    links.remove(url)
                    break

    def mergePackages(self, links, pid):
        exactmatch = self.getConfig('exactmatch')
        listorder = self.getConfig('listorder')
        samelist = self.getConfig('samelist')
        doublecheck = self.getConfig('doublecheck')
        pypack = self.api.getPackageInfo(pid)
        queue = self.api.getQueue()
        collector = self.api.getCollector()
        pname = pypack.name if exactmatch else sub('[^A-Za-z0-9]+', '', pypack.name).lower()
        if samelist:
            lists = [queue] if pypack.dest else [collector]
        elif listorder == 'queue':
            lists = [queue, collector]
        else:
            lists = [collector, queue]
        for list in lists:
            for lpypack in list:
                lpname = lpypack.name if exactmatch else sub('[^A-Za-z0-9]+', '', lpypack.name).lower()
                if lpname == pname:
                    msg = 'merging "%s" package to "%s" package found on "%s" list'
                    self.logInfo(msg % (pypack.name, lpypack.name, 'queue' if lpypack.dest else 'collector'))
                    if doublecheck:
                        self.doubleCheck(links, lpypack.pid)      
                    self.removeEvent('linksAdded', self.mergePackages)
                    self.api.addFiles(lpypack.pid, links)
                    self.addEvent('linksAdded', self.mergePackages)
                    del links[:]
                    self.logDebug('merge complete')
                    return

    ## event managing ##
    def addEvent(self, event, func):
        """Adds an event listener for event name"""
        if event in self.m.events:
            if func in self.m.events[event]:
                self.logDebug("Function already registered %s" % func)
            else:
                self.m.events[event].append(func)
        else:
            self.m.events[event] = [func]

    def setup(self):
        self.api = self.core.api
        self.m = self.manager
        self.removeEvent = self.m.removeEvent
