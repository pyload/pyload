# -*- coding: utf-8 -*-

import re

from module.PyFile import PyFile

from ..internal.Addon import Addon


class SkipRev(Addon):
    __name__ = "SkipRev"
    __type__ = "hook"
    __version__ = "0.38"
    __status__ = "testing"

    __config__ = [("activated", "bool", "Activated", False),
                  ("mode", "Auto;Manual", "Choose recovery archives to skip", "Auto"),
                  ("revtokeep", "int", "Number of recovery archives to keep for package", 0)]

    __description__ = """Skip recovery archives (.rev)"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    def _name(self, pyfile):
        return pyfile.pluginclass.get_info(pyfile.url)['name']

    def _create_pyFile(self, data):
        pylink = self.pyload.api._convertPyFile(data)
        return PyFile(self.pyload.files,
                      pylink.fid,
                      pylink.url,
                      pylink.name,
                      pylink.size,
                      pylink.status,
                      pylink.error,
                      pylink.plugin,
                      pylink.packageID,
                      pylink.order)

    def download_preparing(self, pyfile):
        name = self._name(pyfile)

        if pyfile.statusname == "unskipped" or not name.endswith(
                ".rev") or not ".part" in name:
            return

        revtokeep = - \
            1 if self.config.get(
                'mode') == "Auto" else self.config.get('revtokeep')

        if revtokeep:
            status_list = (
                1, 4, 8, 9, 14) if revtokeep < 0 else (
                1, 3, 4, 8, 9, 14)
            pyname = re.compile(
                r'%s\.part\d+\.rev$' %
                name.rsplit(
                    '.',
                    2)[0].replace(
                    '.',
                    '\.'))

            queued = [True for fid, fdata in pyfile.package().getChildren().items()
                      if fdata['status'] not in status_list and pyname.match(fdata['name'])].count(True)

            if not queued or queued < revtokeep:  #: Keep one rev at least in auto mode
                return

        pyfile.setCustomStatus("SkipRev", "skipped")

    def download_failed(self, pyfile):
        if pyfile.name.rsplit('.', 1)[-1].strip() not in ("rar", "rev"):
            return

        revtokeep = - \
            1 if self.config.get(
                'mode') == "Auto" else self.config.get('revtokeep')

        if not revtokeep:
            return

        pyname = re.compile(
            r'%s\.part\d+\.rev$' %
            pyfile.name.rsplit(
                '.',
                2)[0].replace(
                '.',
                '\.'))

        for fid, fdata in pyfile.package().getChildren().items():
            if fdata['status'] == 4 and pyname.match(fdata['name']):
                pyfile_new = self._create_pyFile(fdata)

                if revtokeep > -1 or pyfile.name.endswith(".rev"):
                    pyfile_new.setStatus("queued")
                else:
                    pyfile_new.setCustomStatus(_("unskipped"), "queued")

                self.pyload.files.save()
                pyfile_new.release()
                return
