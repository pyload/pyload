# -*- coding: utf-8 -*-


from ..base.addon import BaseAddon


class LinkFilter(BaseAddon):
    __name__ = "LinkFilter"
    __type__ = "addon"
    __version__ = "0.16"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", False),
        ("filter", "str", "Filter links containing (comma separated)", ""),
        ("list_type", "listed;unlisted", "Allow only links that are", "unlisted"),
        (
            "filter_all",
            "bool",
            "Filter all link plugin types (also crypters, containers...)",
            False,
        ),
    ]

    __description__ = "Filters all added downloader links"
    __license__ = "GPLv3"
    __authors__ = [("segelkma", None)]

    def activate(self):
        self.m.add_event("links_added", self.filter_links)

    def deactivate(self):
        self.m.remove_event("links_added", self.filter_links)

    def filter_links(self, links, pid):
        filters = self.config.get("filter").replace(" ", "")
        if filters == "":
            return
        filters = filters.split(",")
        if self.config.get("list_type", "unlisted") == "listed":
            self.whitelist(links, filters)
        else:
            self.blacklist(links, filters)

    def whitelist(self, links, filters):
        plugin_dict = dict(self.pyload.plugin_manager.parse_urls(links))
        link_count = len(links)
        links[:] = [
            link
            for link in links
            if any(link.find(fltr) != -1 for fltr in filters)
            or not self.is_downloader_link(link)
            and plugin_dict[link] != "DefaultPlugin"
        ]
        link_count -= len(links)

        if link_count > 0:
            link_type = "" if self.config.get("filter_all") else "downloader "
            link_type += "link" if link_count == 1 else "links"
            self.log_warning(
                self._("Whitelist filter removed {} {} not containing ({})").format(
                    link_count, link_type, ", ".join(filters)
                )
            )

    def blacklist(self, links, filters):
        for fltr in filters:
            link_count = len(links)
            links[:] = [
                link
                for link in links
                if link.find(fltr) == -1 or not self.is_downloader_link(link)
            ]
            link_count -= len(links)

            if link_count > 0:
                link_type = "" if self.config.get("filter_all") else "hoster "
                link_type += "link" if link_count == 1 else "links"
                self.log_warning(
                    "Blacklist filter removed {} {} containing {}".format(
                        link_count, link_type, fltr
                    )
                )

    def is_downloader_link(self, link):
        if self.config.get("filter_all"):
            # declare all links as downloader links so the filter will work on all links
            return True
        for item in self.pyload.plugin_manager.downloader_plugins.items():
            if item[1]["re"].match(link):
                return True
        return False
