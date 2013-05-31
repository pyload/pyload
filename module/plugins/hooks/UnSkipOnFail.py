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

    @author: hgg
"""

from module.plugins.Hook import Hook
from module.utils import fs_encode
from os.path import basename


class UnSkipOnFail(Hook):
    __name__ = 'UnSkipOnFail'
    __version__ = '0.02'
    __description__ = 'When a download fails, restart a "skipped" duplicate'
    __config__ = [('activated', 'bool', 'Activated', False)]
    __author_name__ = ('hagg', 'Walter Purcaro')
    __author_mail__ = ('', 'vuolter@gmail.com')

    def downloadFailed(self, pyfile):
        #: Check if pyfile is still "failed", maybe might have been restarted in meantime
        if pyfile.status != 8:
            return
        pyfile_name = basename(pyfile.name)
        pid = pyfile.package().id
        self.logInfo('look for skipped duplicates for %s (pid:%s)...' % (pyfile_name, pid))
        dups = self.findDuplicates(pyfile)
        for link in dups:
            #: check if link is "skipped"
            if link.status == 4:
                lpid = link.packageID
                self.logInfo('restart "%s" (pid:%s)...' % (pyfile_name, lpid))
                link.setStatus("queued")
                return

    def findDuplicates(self, pyfile):
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
        pyfile_name = fs_encode(basename(pyfile.name))
        #: get packages (w/o files, as most file data is useless here)
        queue = self.core.api.getQueue()
        for package in queue:
            #: check if package-folder equals pyfile's package folder
            if fs_encode(package.folder) == fs_encode(pyfile.package().folder):
                #: now get packaged data w/ files/links
                pdata = self.core.api.getPackageData(package.pid)
                for link in pdata.links:
                    link_name = fs_encode(basename(link.name))
                    #: check if link name collides with pdata's name AND at last check if it is not pyfile itself
                    if link_name == pyfile_name and link.fid != pyfile.id:
                        dups.append(link)
        return dups
