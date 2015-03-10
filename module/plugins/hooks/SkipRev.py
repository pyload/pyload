# -*- coding: utf-8 -*-

import re

from types import MethodType
from urllib import unquote
from urlparse import urlparse

from module.PyFile import PyFile
from module.plugins.Hook import Hook
from module.plugins.Plugin import SkipDownload


class SkipRev(Hook):
    __name__    = "SkipRev"
    __type__    = "hook"
    __version__ = "0.29"

    __config__ = [("mode"     , "Auto;Manual", "Choose rev files to skip for package", "Auto"),
                  ("revtokeep", "int"        , "Number of rev files to keep"         , 0     )]

    __description__ = """Skip files ending with extension rev"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    #@TODO: Remove in 0.4.10
    def initPeriodical(self):
        pass


    @staticmethod
    def _setup(self):
        self.pyfile.plugin._setup()
        if self.pyfile.hasStatus("skipped"):
            raise SkipDownload(self.pyfile.statusname or self.pyfile.pluginname)


    def _name(self, pyfile):
        if hasattr(pyfile.pluginmodule, "getInfo"):  #@NOTE: getInfo is deprecated in 0.4.10
            return pyfile.pluginmodule.getInfo([pyfile.url]).next()[0]
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
        name = self._name(pyfile)

        if pyfile.statusname is _("unskipped") or not name.endswith(".rev") or not ".part" in name:
            return

        revtokeep = -1 if self.getConfig('mode') == "Auto" else self.getConfig('revtokeep')

        if revtokeep:
            status_list = (1, 4, 8, 9, 14) if revtokeep < 0 else (1, 3, 4, 8, 9, 14)
            pyname      = re.compile(r'%s\.part\d+\.rev$' % name.rsplit('.', 2)[0].replace('.', '\.'))

            queued = [True for link in self.core.api.getPackageData(pyfile.package().id).links \
                      if link.status not in status_list and pyname.match(link.name)].count(True)

            if not queued or queued < revtokeep:  #: keep one rev at least in auto mode
                return

        pyfile.setCustomStatus("SkipRev", "skipped")

        if not hasattr(pyfile.plugin, "_setup"):
            # Work-around: inject status checker inside the preprocessing routine of the plugin
            pyfile.plugin._setup = pyfile.plugin.setup
            pyfile.plugin.setup  = MethodType(self._setup, pyfile.plugin)


    def downloadFailed(self, pyfile):
        #: Check if pyfile is still "failed",
        #  maybe might has been restarted in meantime
        if pyfile.status != 8 or pyfile.name.rsplit('.', 1)[-1].strip() not in ("rar", "rev"):
            return

        revtokeep = -1 if self.getConfig('mode') == "Auto" else self.getConfig('revtokeep')

        if not revtokeep:
            return

        pyname = re.compile(r'%s\.part\d+\.rev$' % pyfile.name.rsplit('.', 2)[0].replace('.', '\.'))

        for link in self.core.api.getPackageData(pyfile.package().id).links:
            if link.status is 4 and pyname.match(link.name):
                pylink = self._pyfile(link)

                if revtokeep > -1 or pyfile.name.endswith(".rev"):
                    pylink.setStatus("queued")
                else:
                    pylink.setCustomStatus(_("unskipped"), "queued")

                self.core.files.save()
                pylink.release()
                return
