
from ..internal.Addon import Addon

class LinkFilter(Addon):
    __name__ = "LinkFilter"
    __type__ = "hook"
    __version__ = "0.16"
    __status__ = "testing"

    __config__ = [("activated", "bool", "Activated", False),
                  ("filter", "str", "Filter links containing (comma separated)", ""),
                  ("list_type", "listed;unlisted", "Allow only links that are", "unlisted"),
                  ("filter_all", "bool", "Filter all link plugin types (also crypters, containers...)", False)]

    __description__ = "Filters all added hoster links"
    __license__ = "GPLv3"
    __authors__ = [("segelkma", None)]

    def activate(self):
        self.manager.addEvent('linksAdded', self.filter_links)

    def deactivate(self):
        self.manager.removeEvent('linksAdded', self.filter_links)

    def filter_links(self, links, pid):
        filters = self.config.get('filter').replace(' ', '')
        if filters == "":
            return
        filters = filters.split(',')
        if self.config.get('list_type', "unlisted") == "listed":
            self.whitelist(links, filters)
        else:
            self.blacklist(links, filters)

    def whitelist(self, links, filters):
        plugindict = dict(self.pyload.pluginManager.parseUrls(links))
        linkcount = len(links)
        links[:] = [link for link in links if
                    any(link.find(_filter) != -1 for _filter in filters) or
                    not self.is_hoster_link(link) and plugindict[link] != "BasePlugin"]
        linkcount -= len(links)

        if linkcount > 0:
            linkstring = '' if self.config.get('filter_all') else 'hoster '
            linkstring += 'link' if linkcount == 1 else 'links'
            self.log_warning(
                _('Whitelist filter removed %s %s not containing (%s)') %
                (linkcount, linkstring, ', '.join(filters)))

    def blacklist(self, links, filters):
        for _filter in filters:
            linkcount = len(links)
            links[:] = [link for link in links if
                        link.find(_filter) == -1 or
                        not self.is_hoster_link(link)]
            linkcount -= len(links)

            if linkcount > 0:
                linkstring = '' if self.config.get('filter_all') else 'hoster '
                linkstring += 'link' if linkcount == 1 else 'links'
                self.log_warning(
                    'Blacklist filter removed %s %s containing %s' %
                    (linkcount, linkstring, _filter))

    def is_hoster_link(self, link):
        #declare all links as hoster links so the filter will work on all links
        if self.config.get('filter_all'):
            return True
        for item in self.pyload.pluginManager.hosterPlugins.items():
            if item[1]['re'].match(link):
                return True
        return False
