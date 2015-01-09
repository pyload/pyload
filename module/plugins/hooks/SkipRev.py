# -*- coding: utf-8 -*-

from types import MethodType
from urllib import unquote
from urlparse import urlparse

from module.PyFile import PyFile
from module.plugins.Hook import Hook
from module.plugins.Plugin import SkipDownload


def _setup(self):
    self.pyfile.plugin._setup()
    if self.pyfile.hasStatus("skipped"):
        raise SkipDownload(self.pyfile.statusname or self.pyfile.pluginname)


class SkipRev(Hook):
    __name__    = "SkipRev"
    __type__    = "hook"
    __version__ = "0.22"

    __config__ = [("tokeep", "int", "Number of rev files to keep for package (-1 to auto)", -1)]

    __description__ = """Skip files ending with extension rev"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    #@TODO: Remove in 0.4.10
    def initPeriodical(self):
        pass


    def _pyname(self, pyfile):
        if hasattr(pyfile.pluginmodule, "getInfo"):
            return getattr(pyfile.pluginmodule, "getInfo")([pyfile.url])[0][0]
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
            saved = [True for link in self.core.api.getPackageData(pyfile.package().id).links \
                     if link.name.endswith(".rev") and link.status in (0, 12)].count(True)

            if not saved or saved < tokeep:  #: keep one rev at least in auto mode
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
