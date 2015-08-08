# -*- coding: utf-8 -*-

from module.PyFile import PyFile
from module.plugins.internal.Addon import Addon


class UnSkipOnFail(Addon):
    __name__    = "UnSkipOnFail"
    __type__    = "hook"
    __version__ = "0.09"
    __status__  = "testing"

    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Restart skipped duplicates when download fails"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def download_failed(self, pyfile):
        #: Check if pyfile is still "failed", maybe might has been restarted in meantime
        if pyfile.status != 8:
            return

        msg = _("Looking for skipped duplicates of: %s (pid:%s)")
        self.log_info(msg % (pyfile.name, pyfile.package().id))

        link = self.find_duplicate(pyfile)
        if link:
            self.log_info(_("Queue found duplicate: %s (pid:%s)") % (link.name, link.packageID))

            #: Change status of "link" to "new_status".
            #: "link" has to be a valid FileData object,
            #: "new_status" has to be a valid status name
            #: (i.e. "queued" for this Plugin)
            #: It creates a temporary PyFile object using
            #: "link" data, changes its status, and tells
            #: The pyload.files-manager to save its data.
            pylink = self._pyfile(link)

            pylink.setCustomStatus(_("unskipped"), "queued")

            self.pyload.files.save()
            pylink.release()

        else:
            self.log_info(_("No duplicates found"))


    def find_duplicate(self, pyfile):
        """Search all packages for duplicate links to "pyfile".
            Duplicates are links that would overwrite "pyfile".
            To test on duplicity the package-folder and link-name
            of twolinks are compared (link.name).
            So this method returns a list of all links with equal
            package-folders and filenames as "pyfile", but except
            the data for "pyfile" iotselöf.
            It does MOT check the link's status.
        """
        queue = self.pyload.api.getQueue()  #: Get packages (w/o files, as most file data is useless here)

        for package in queue:
            #: Check if package-folder equals pyfile's package folder
            if package.folder is not pyfile.package().folder:
                continue

            #: Now get packaged data w/ files/links
            pdata = self.pyload.api.getPackageData(package.pid)
            for link in pdata.links:
                #: Check if link == "skipped"
                if link.status != 4:
                    continue

                #: Check if link name collides with pdata's name
                #: and at last check if it is not pyfile itself
                if link.name is pyfile.name and link.fid is not pyfile.id:
                    return link


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
