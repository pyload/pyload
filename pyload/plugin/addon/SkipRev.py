# -*- coding: utf-8 -*-

from types import MethodType
from urllib import unquote
from urlparse import urlparse

from pyload.datatype.File import PyFile
from pyload.plugin.Addon import Addon
from pyload.plugin.Plugin import SkipDownload


def _setup(self):
    self.pyfile.plugin._setup()
    if self.pyfile.hasStatus("skipped"):
        raise SkipDownload(self.pyfile.statusname or self.pyfile.pluginname)


class SkipRev(Addon):
    __name    = "SkipRev"
    __type    = "addon"
    __version = "0.25"

    __config = [("tokeep", "int", "Number of rev files to keep for package (-1 to auto)", -1)]

    __description = """Skip files ending with extension rev"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    def _pyname(self, pyfile):
        if hasattr(pyfile.pluginmodule, "getInfo"):
            return getattr(pyfile.pluginmodule, "getInfo")([pyfile.url]).next()[0]
        else:
            self.logWarning("Unable to grab file name")
            return urlparse(unquote(pyfile.url)).path.split('/')[-1]


    def _pyfile(self, link):
        return PyFile(self.core.files,
                      link.fid,
                      link.url,
                      link.name,
                      link.size,
                      link.status,
                      link.error,
                      link.plugin,
                      link.packageID,
                      link.order)


    def downloadPreparing(self, pyfile):
        if pyfile.statusname is "unskipped" or not self._pyname(pyfile).endswith(".rev"):
            return

        tokeep = self.getConfig("tokeep")

        if tokeep:
            status_list = (1, 4, 8, 9, 14) if tokeep < 0 else (1, 3, 4, 8, 9, 14)

            queued = [True for link in self.core.api.getPackageData(pyfile.package().id).links \
                      if link.name.endswith(".rev") and link.status not in status_list].count(True)

            if not queued or queued < tokeep:  #: keep one rev at least in auto mode
                return

        pyfile.setCustomStatus("SkipRev", "skipped")
        pyfile.plugin._setup = pyfile.plugin.setup
        pyfile.plugin.setup  = MethodType(_setup, pyfile.plugin)  #: work-around: inject status checker inside the preprocessing routine of the plugin


    def downloadFailed(self, pyfile):
        #: Check if pyfile is still "failed",
        #  maybe might has been restarted in meantime
        if pyfile.status != 8:
            return

        tokeep = self.getConfig("tokeep")

        if not tokeep:
            return

        for link in self.core.api.getPackageData(pyfile.package().id).links:
            if link.status is 4 and link.name.endswith(".rev"):
                pylink = self._pyfile(link)

                if tokeep > -1 or pyfile.name.endswith(".rev"):
                    pylink.setStatus("queued")
                else:
                    pylink.setCustomStatus("unskipped", "queued")

                self.core.files.save()
                pylink.release()
                return
