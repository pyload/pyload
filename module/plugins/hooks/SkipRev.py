# -*- coding: utf-8 -*-

import re
import urllib
import urlparse

from types import MethodType

from module.PyFile import PyFile
from module.plugins.internal.Addon import Addon


class SkipRev(Addon):
    __name__    = "SkipRev"
    __type__    = "hook"
    __version__ = "0.33"
    __status__  = "testing"

    __config__ = [("mode"     , "Auto;Manual", "Choose recovery archives to skip"               , "Auto"),
                  ("revtokeep", "int"        , "Number of recovery archives to keep for package", 0     )]

    __description__ = """Skip recovery archives (.rev)"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    @staticmethod
    def _init(self):
        self.pyfile.plugin._init()
        if self.pyfile.hasStatus("skipped"):
            self.skip(self.pyfile.statusname or self.pyfile.pluginname)


    def _name(self, pyfile):
        return pyfile.pluginclass.get_info(pyfile.url)['name']


    def _pyfile(self, link):
        return PyFile(self.pyload.files,
                      link.fid,
                      link.url,
                      link.name,
                      link.size,
                      link.status,
                      link.error,
                      link.plugin,
                      link.packageID,
                      link.order)


    def download_preparing(self, pyfile):
        name = self._name(pyfile)

        if pyfile.statusname is _("unskipped") or not name.endswith(".rev") or not ".part" in name:
            return

        revtokeep = -1 if self.get_config('mode') == "Auto" else self.get_config('revtokeep')

        if revtokeep:
            status_list = (1, 4, 8, 9, 14) if revtokeep < 0 else (1, 3, 4, 8, 9, 14)
            pyname      = re.compile(r'%s\.part\d+\.rev$' % name.rsplit('.', 2)[0].replace('.', '\.'))

            queued = [True for link in self.pyload.api.getPackageData(pyfile.package().id).links \
                      if link.status not in status_list and pyname.match(link.name)].count(True)

            if not queued or queued < revtokeep:  #: Keep one rev at least in auto mode
                return

        pyfile.setCustomStatus("SkipRev", "skipped")

        if not hasattr(pyfile.plugin, "_init"):
            #: Work-around: inject status checker inside the preprocessing routine of the plugin
            pyfile.plugin._init = pyfile.plugin.init
            pyfile.plugin.init  = MethodType(self._init, pyfile.plugin)


    def download_failed(self, pyfile):
        #: Check if pyfile is still "failed", maybe might has been restarted in meantime
        if pyfile.status != 8 or pyfile.name.rsplit('.', 1)[-1].strip() not in ("rar", "rev"):
            return

        revtokeep = -1 if self.get_config('mode') == "Auto" else self.get_config('revtokeep')

        if not revtokeep:
            return

        pyname = re.compile(r'%s\.part\d+\.rev$' % pyfile.name.rsplit('.', 2)[0].replace('.', '\.'))

        for link in self.pyload.api.getPackageData(pyfile.package().id).links:
            if link.status == 4 and pyname.match(link.name):
                pylink = self._pyfile(link)

                if revtokeep > -1 or pyfile.name.endswith(".rev"):
                    pylink.setStatus("queued")
                else:
                    pylink.setCustomStatus(_("unskipped"), "queued")

                self.pyload.files.save()
                pylink.release()
                return
