
from ..internal.Addon import Addon

from itertools import chain

class LinkFilter(Addon):
    __name__ = "LinkFilter"
    __type__ = "hook"
    __version__ = "0.14"
    __status__ = "testing"

    __config__ = [("activated", "bool", "Activated", False),
                  ("filter", "str", "Filter links containing (seperate by comma)", "ul.to,uploaded.net,share-online.biz"),
                  ("whitelist", "bool", "Execute filter as whitelist", False),
                  ("forceExecute", "bool", "Force execution on all links (also crypters, containers...)", False)]

    __description__ = "Filters all added hoster links"
    __license__ = "GPLv3"
    __authors__ = [("segelkma", None)]

    def activate(self):
        self.manager.addEvent('linksAdded', self.filter_links)

    def deactivate(self):
        self.manager.removeEvent('linksAdded', self.filter_links)

    def filter_links(self, links, pid):
        filters = self.config.get('filter').replace(' ', '').split(',')
        if self.config.get('whitelist'):
            self.whitelist(links, filters)
        else:
            self.blacklist(links, filters)

    def whitelist(self, links, filters):
        linkcount = len(links)
        links[:] = [link for link in links if
            not self.isHosterLink(link) or
            [True for filter in filters if link.find(filter) != -1]]
        linkcount -= len(links)

        if linkcount > 0:
                linkstring = '' if self.config.get('forceExecute') else 'hoster '
                linkstring += 'links' if linkcount > 1 else 'link'
                self.log_info(
                    'Whitelist filter removed %s %s not containing (%s)' %
                    (linkcount, linkstring, ', '.join(filters)))

    def blacklist(self, links, filters):
        for filter in filters:
            linkcount = len(links)
            links[:] = [link for link in links if
                not self.isHosterLink(link) or
                link.find(filter) == -1]
            linkcount -= len(links)

            if linkcount > 0:
                linkstring = '' if self.config.get('forceExecute') else 'hoster '
                linkstring += 'links' if linkcount > 1 else 'link'
                self.log_info(
                    'Blacklist filter removed %s %s containing %s' %
                    (linkcount, linkstring, filter))

    def isHosterLink(self, link):
        #declare all links as hoster links so the filter will work on all links
        if self.config.get('forceExecute'):
            return True
        for name, value in chain(self.pyload.pluginManager.hosterPlugins.iteritems()):
            if value['re'].match(link):
                return True
        return False