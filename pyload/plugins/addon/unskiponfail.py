# -*- coding: utf-8 -*-
#@author: hgg

from __future__ import unicode_literals
from os.path import basename

from pyload.utils import fs_encode
from pyload.plugins.hook import Hook
from pyload.PyFile import PyFile


class UnSkipOnFail(Hook):
    __name__ = 'UnSkipOnFail'
    __version__ = '0.01'
    __description__ = """When a download fails, restart skipped duplicates"""
    __config__ = [("activated", "bool", "Activated", True)]
    __author_name__ = "hagg"
    __author_mail__ = ""

    def download_failed(self, pyfile):
        pyfile_name = basename(pyfile.name)
        pid = pyfile.package().id
        msg = 'look for skipped duplicates for %s (pid:%s)...'
        self.logInfo(msg % (pyfile_name, pid))
        dups = self.findDuplicates(pyfile)
        for link in dups:
            # check if link is "skipped"(=4)
            if link.status == 4:
                lpid = link.packageID
                self.logInfo('restart "%s" (pid:%s)...' % (pyfile_name, lpid))
                self.setLinkStatus(link, "queued")

    def find_duplicates(self, pyfile):
        """ Search all packages for duplicate links to "pyfile".
            Duplicates are links that would overwrite "pyfile".
            To test on duplicity the package-folder and link-name
            of twolinks are compared (basename(link.name)).
            So this method returns a list of all links with equal
            package-folders and filenames as "pyfile", but except
            the data for "pyfile" iotselöf.
            It does MOT check the link's status.
        """
        dups = []
        pyfile_name = fs_encode(basename(pyfile.name))
        # get packages (w/o files, as most file data is useless here)
        queue = self.pyload.api.get_queue()
        for package in queue:
            # check if package-folder equals pyfile's package folder
            if fs_encode(package.folder) == fs_encode(pyfile.package().folder):
                # now get packaged data w/ files/links
                pdata = self.pyload.api.get_package_data(package.pid)
                if pdata.links:
                    for link in pdata.links:
                        link_name = fs_encode(basename(link.name))
                        # check if link name collides with pdata's name
                        if link_name == pyfile_name:
                            # at last check if it is not pyfile itself
                            if link.fid != pyfile.id:
                                dups.append(link)
        return dups

    def set_link_status(self, link, new_status):
        """ Change status of "link" to "new_status".
            "link" has to be a valid FileData object,
            "new_status" has to be a valid status name
              (i.e. "queued" for this Plugin)
            It creates a temporary PyFile object using
            "link" data, changes its status, and tells
            the core.files-manager to save its data.
        """
        pyfile = PyFile(self.pyload.files,
                        link.fid,
                        link.url,
                        link.name,
                        link.size,
                        link.status,
                        link.error,
                        link.plugin,
                        link.packageID,
                        link.order)
        pyfile.set_status(new_status)
        self.pyload.files.save()
        pyfile.release()
