# -*- coding: utf-8 -*-
import re

from ..base.addon import BaseAddon


class JustPremium(BaseAddon):
    __name__ = "JustPremium"
    __type__ = "addon"
    __version__ = "0.27"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", False),
        ("excluded", "str", "Exclude hosters (comma separated)", ""),
        ("included", "str", "Include hosters (comma separated)", ""),
    ]

    __description__ = """Remove not-premium links from added urls"""
    __license__ = "GPLv3"
    __authors__ = [
        ("mazleu", "mazleica@gmail.com"),
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("immenz", "immenz@gmx.net"),
    ]

    def init(self):
        self.event_map = {"links_added": "links_added"}

    def links_added(self, links, pid):
        hosterdict = self.pyload.plugin_manager.downloader_plugins
        linkdict = self.pyload.api.check_urls(links)

        premiumplugins = set(
            account.type
            for account in self.pyload.api.get_accounts(False)
            if account.valid and account.premium
        )
        multihosters = set(
            hoster
            for hoster in self.pyload.plugin_manager.downloader_plugins
            if "new_name" in hosterdict[hoster]
            and hosterdict[hoster]["new_name"] in premiumplugins
        )

        excluded = [
            "".join(
                part.capitalize()
                for part in re.split(r"(\.|\d+)", domain)
                if part != "."
            )
            for domain in self.config.get("excluded")
            .replace(" ", "")
            .replace(",", "|")
            .replace(";", "|")
            .split("|")
        ]
        included = [
            "".join(
                part.capitalize()
                for part in re.split(r"(\.|\d+)", domain)
                if part != "."
            )
            for domain in self.config.get("included")
            .replace(" ", "")
            .replace(",", "|")
            .replace(";", "|")
            .split("|")
        ]

        hosterlist = (
            (premiumplugins | multihosters).union(excluded).difference(included)
        )

        #: Found at least one hoster with account or multihoster
        if not any(True for pluginname in linkdict if pluginname in hosterlist):
            return

        for pluginname in set(linkdict.keys()) - hosterlist:
            self.log_info(self._("Remove links of plugin: {}").format(pluginname))
            for link in linkdict[pluginname]:
                self.log_debug(f"Remove link: {link}")
                links.remove(link)
