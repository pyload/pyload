# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: hgg, Walter Purcaro
"""

from module.plugins.Hook import Hook


class UnSkipOnFail(Hook):
    __name__ = "UnSkipOnFail"
    __version__ = "0.02"
    __description__ = "When a download fails restart skipped duplicates"
    __config__ = [("activated", "bool", "Activated", False)]
    __author_name__ = ("hagg", "Walter Purcaro")
    __author_mail__ = ("", "vuolter@gmail.com")

    event_map = {"downloadFailed": "unSkipOnFail"}

    def unSkipOnFail(self, pyfile):
        #: Check if pyfile is still "failed",
        #: maybe might has been restarted in meantime
        if pyfile.status != 8:
            return
        pid = pyfile.package().id
        msg = "look for skipped duplicates for file \"%s\" (pid:%s)"
        self.logInfo(msg % (pyfile.name, pid))
        dups = self.findSkipDups(pyfile)
        for fid in dups:
            dupfile = self.api.getFileData(fid)
            msg = "restarting file \"%s\" (pid: %s)"
            self.logInfo(msg % (dupfile.name, dupfile.id))
            dupfile.setStatus("queued")

    def findSkipDups(self, pyfile):
        """ Search all packages for duplicate links to "pyfile".
            Duplicates are links that would overwrite "pyfile".
            To test on duplicity the package-folder and link-name
            of twolinks are compared (basename(link.name)).
            So this method returns a list of all links with equal
            package-folders and filenames as "pyfile", but except
            the data for "pyfile" itself.
            It does NOT check the link's status.
        """
        dups = []
        #: get packages (w/o files, as most file data is useless here)
        queue = self.api.getQueue()
        for package in queue:
            #: check if package-folder equals pyfile's package folder
            if package.folder != pyfile.package().folder:
                return
            #: now get packaged data w/ files/links
            pdata = self.api.getPackageData(package.pid)
            for link in pdata.links:
                #: check if link is "skipped"
                if link.status != 4:
                    return
                #: check if link name collides with pdata's name
                #: AND at last check if it is not pyfile itself
                if link.name == pyfile.name and link.fid != pyfile.id:
                    dups.append(link.fid)
        return dups

    def setup(self):
        self.api = self.core.api
