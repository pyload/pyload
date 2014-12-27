# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHook import MultiHook


class ZeveraCom(MultiHook):
    __name__    = "ZeveraCom"
    __type__    = "hook"
    __version__ = "0.04"

    __config__ = [("mode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("pluginlist", "str", "Hoster list (comma separated)", "")]

    __description__ = """Real-Debrid.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    def getHosters(self):
        page = self.getURL("http://www.zevera.com/jDownloader.ashx", get={'cmd': "gethosters"})
        return [x.strip() for x in page.replace("\"", "").split(",")]
