# -*- coding: utf-8 -*-

import re

from module.plugins.Hook import Hook
from module.plugins.Plugin import SkipDownload


class SkipRev(Hook):
    __name__    = "SkipRev"
    __type__    = "hook"
    __version__ = "0.10"

    __config__ = [("auto",   "bool", "Automatically keep all rev files needed by package", True),
                  ("tokeep", "int" , "Min number of rev files to keep for package"       ,    1),
                  ("unskip", "bool", "Restart a skipped rev when download fails"         , True)]

    __description__ = """Skip files ending with extension rev"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    event_map = [("downloadStarts", skipRev)]

    REV = re.compile(r'\.part(\d+)\.rev$')


    def skipRev(self, pyfile, url, filename):
        if REV.search(pyfile.name) is None or pyfile.getStatusName() is "unskipped":
            return

        tokeep = self.getConfig("tokeep")

        if tokeep > 0:
            saved = [True if link.hasStatus("finished") or link.hasStatus("downloading") and REV.search(link.name) \
                     for link in pyfile.package().getChildren()].count(True)

            if saved < tokeep:
                return

        raise SkipDownload("SkipRev")


    def downloadFailed(self, pyfile):
        if self.getConfig("auto") is False:

            if self.getConfig("unskip") is False:
                return

            if REV.search(pyfile.name) is None:
                return

        for link in pyfile.package().getChildren():
            if link.hasStatus("skipped") and REV.search(link.name):
                link.setCustomStatus("unskipped", "queued")
                return
