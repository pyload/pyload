# -*- coding: utf-8 -*-

from module.PyFile import PyFile
from module.plugins.Hook import Hook


class UnSkipOnFail(Hook):
    __name__    = "UnSkipOnFail"
    __type__    = "hook"
    __version__ = "0.07"

    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Restart skipped duplicates when download fails"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    interval = 0  #@TODO: Remove in 0.4.10


    def setup(self):
        self.info = {}  #@TODO: Remove in 0.4.10


    def downloadFailed(self, pyfile):
        #: Check if pyfile is still "failed",
        #  maybe might has been restarted in meantime
        if pyfile.status != 8:
            return

        msg = _("Looking for skipped duplicates of: %s (pid:%s)")
        self.logInfo(msg % (pyfile.name, pyfile.package().id))

        link = self.findDuplicate(pyfile)
        if link:
            self.logInfo(_("Queue found duplicate: %s (pid:%s)") % (link.name, link.packageID))

            #: Change status of "link" to "new_status".
            #  "link" has to be a valid FileData object,
            #  "new_status" has to be a valid status name
            #  (i.e. "queued" for this Plugin)
            #  It creates a temporary PyFile object using
            #  "link" data, changes its status, and tells
            #  the core.files-manager to save its data.
            pylink = self._pyfile(link)

            pylink.setCustomStatus(_("unskipped"), "queued")

            self.core.files.save()
            pylink.release()

        else:
            self.logInfo(_("No duplicates found"))


    def findDuplicate(self, pyfile):
        """ Search all packages for duplicate links to "pyfile".
            Duplicates are links that would overwrite "pyfile".
            To test on duplicity the package-folder and link-name
            of twolinks are compared (link.name).
            So this method returns a list of all links with equal
            package-folders and filenames as "pyfile", but except
            the data for "pyfile" iotselöf.
            It does MOT check the link's status.
        """
        queue = self.core.api.getQueue()  #: get packages (w/o files, as most file data is useless here)

        for package in queue:
            #: check if package-folder equals pyfile's package folder
            if package.folder != pyfile.package().folder:
                continue

            #: now get packaged data w/ files/links
            pdata = self.core.api.getPackageData(package.pid)
            for link in pdata.links:
                #: check if link is "skipped"
                if link.status != 4:
                    continue

                #: check if link name collides with pdata's name
                #: AND at last check if it is not pyfile itself
                if link.name == pyfile.name and link.fid != pyfile.id:
                    return link


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
