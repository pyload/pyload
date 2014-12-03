# -*- coding: utf-8 -*-

import re

from module.plugins.Hook import Hook
from module.plugins.Plugin import SkipDownload


class SkipRev(Hook):
    __name__    = "SkipRev"
    __type__    = "hook"
    __version__ = "0.11"

    __config__ = [("auto",   "bool", "Automatically keep all rev files needed by package", True),
                  ("tokeep", "int" , "Min number of rev files to keep for package"       ,    1),
                  ("unskip", "bool", "Restart a skipped rev when download fails"         , True)]

    __description__ = """Skip files ending with extension rev"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    event_list = ["downloadStarts"]

    REV = re.compile(r'\.part(\d+)\.rev$')


    def downloadStarts(self, pyfile, url, filename):
        if self.REV.search(pyfile.name) is None or pyfile.getStatusName() is "unskipped":
            return

        tokeep = self.getConfig("tokeep")

        if tokeep > 0:
            saved = [True for link in pyfile.package().getChildren() \
                     if link.hasStatus("finished") or link.hasStatus("downloading") and self.REV.search(link.name)].count(True)

            if saved < tokeep:
                return

        raise SkipDownload("SkipRev")


    def downloadFailed(self, pyfile):
        if self.getConfig("auto") is False:

            if self.getConfig("unskip") is False:
                return

            if self.REV.search(pyfile.name) is None:
                return

        for link in pyfile.package().getChildren():
            if link.hasStatus("skipped") and self.REV.search(link.name):
                link.setCustomStatus("unskipped", "queued")
                return
