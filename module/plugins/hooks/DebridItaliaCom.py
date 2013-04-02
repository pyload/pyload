# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHoster import MultiHoster


class DebridItaliaCom(MultiHoster):
    __name__ = "DebridItaliaCom"
    __version__ = "0.03"
    __type__ = "hook"
    __config__ = [("activated", "bool", "Activated", "False"),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", ""),
                  ("unloadFailing", "bool", "Revert to standard download if download fails", "False"),
                  ("interval", "int", "Reload interval in hours (0 to disable)", "24")]

    __description__ = """Debriditalia.com hook plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    def getHoster(self):
        return ["netload.in", "hotfile.com", "rapidshare.com", "multiupload.com",
                "uploading.com", "megashares.com", "crocko.com", "filepost.com",
                "bitshare.com", "share-links.biz", "putlocker.com", "uploaded.to",
                "speedload.org", "rapidgator.net", "likeupload.net", "cyberlocker.ch",
                "depositfiles.com", "extabit.com", "filefactory.com", "sharefiles.co",
                "ryushare.com", "tusfiles.net", "nowvideo.co"]
