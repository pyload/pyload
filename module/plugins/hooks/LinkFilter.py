
from ..internal.Addon import Addon


class LinkFilter(Addon):
    __name__ = "LinkFilter"
    __type__ = "hook"
    __version__ = "0.14"
    __status__ = "testing"

    __config__ = [("activated", "bool", "Activated", False),
                  ("filter", "str", "Filter links containing (seperate by comma)", "ul.to,share-online.biz")]

    __description__ = "Filters all added links"
    __license__ = "GPLv3"
    __authors__ = [("segelkma", None)]

    def activate(self):
        self.manager.addEvent('linksAdded', self.filter_links)

    def deactivate(self):
        self.manager.removeEvent('linksAdded', self.filter_links)

    def filter_links(self, links, pid):
        filter_entries = self.config.get('filter').split(',')

        for filter in filter_entries:
            if filter == "":
                break

            linkcount = len(links)
            links[:] = [link for link in links if link.find(filter) == -1]
            linkcount -= len(links)

            if linkcount > 0:
                linkstring = 'links' if linkcount > 1 else 'link'
                self.log_info(
                    "Removed %s %s containing %s" %
                    (linkcount, linkstring, filter))
