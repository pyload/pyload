# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals
from pyload.Api import Api, RequirePerm, Permission, DownloadState, PackageStatus as PS, PackageDoesNotExist, FileDoesNotExist
from pyload.utils import uniqify

from .apicomponent import ApiComponent


# TODO: user context
class FileApi(ApiComponent):
    """Everything related to available packages or files. Deleting, Modifying and so on."""

    def checkResult(self, info):
        """ Internal method to verify result and owner """
        #TODO: shared?
        return info and (not self.primaryUID or info.owner == self.primaryUID)

    @RequirePerm(Permission.All)
    def getAllFiles(self):
        """ same as `getFileTree` for toplevel root and full tree"""
        return self.getFileTree(-1, True)

    @RequirePerm(Permission.All)
    def getFilteredFiles(self, state):
        """ same as `getFilteredFileTree` for toplevel root and full tree"""
        return self.getFilteredFileTree(-1, state, True)

    @RequirePerm(Permission.All)
    def getFileTree(self, pid, full):
        """ Retrieve data for specific package. full=True will retrieve all data available
            and can result in greater delays.

        :param pid: package id
        :param full: go down the complete tree or only the first layer
        :return: :class:`TreeCollection`
        """
        return self.core.files.getTree(pid, full, DownloadState.All, self.primaryUID)

    @RequirePerm(Permission.All)
    def getFilteredFileTree(self, pid, full, state):
        """ Same as `getFileTree` but only contains files with specific download state.

        :param pid: package id
        :param full: go down the complete tree or only the first layer
        :param state: :class:`DownloadState`, the attributes used for filtering
        :return: :class:`TreeCollection`
        """
        return self.core.files.getTree(pid, full, state, self.primaryUID)

    @RequirePerm(Permission.All)
    def getPackageContent(self, pid):
        """  Only retrieve content of a specific package. see `getFileTree`"""
        return self.getFileTree(pid, False)

    @RequirePerm(Permission.All)
    def getPackageInfo(self, pid):
        """Returns information about package, without detailed information about containing files

        :param pid: package id
        :raises PackageDoesNotExist:
        :return: :class:`PackageInfo`
        """
        info = self.core.files.getPackageInfo(pid)
        if not self.checkResult(info):
            raise PackageDoesNotExist(pid)
        return info

    @RequirePerm(Permission.All)
    def getFileInfo(self, fid):
        """ Info for specific file

        :param fid: file id
        :raises FileDoesNotExist:
        :return: :class:`FileInfo`

        """
        info = self.core.files.getFileInfo(fid)
        if not self.checkResult(info):
            raise FileDoesNotExist(fid)
        return info

    def getFilePath(self, fid):
        """ Internal method to get the filepath"""
        info = self.getFileInfo(fid)
        pack = self.core.files.getPackage(info.package)
        return pack.getPath(), info.name

    @RequirePerm(Permission.All)
    def findFiles(self, pattern):
        return self.core.files.getTree(-1, True, DownloadState.All, self.primaryUID, pattern)

    @RequirePerm(Permission.All)
    def searchSuggestions(self, pattern):
        names = self.core.db.getMatchingFilenames(pattern, self.primaryUID)
        # TODO: stemming and reducing the names to provide better suggestions
        return uniqify(names)

    @RequirePerm(Permission.All)
    def findPackages(self, tags):
        pass

    @RequirePerm(Permission.Modify)
    def updatePackage(self, pack):
        """Allows to modify several package attributes.

        :param pack: :class:`PackageInfo`
        :return updated package info
        """
        pid = pack.pid
        p = self.core.files.getPackage(pid)
        if not self.checkResult(p):
            raise PackageDoesNotExist(pid)
        p.updateFromInfoData(pack)
        p.sync()
        self.core.files.save()

    @RequirePerm(Permission.Modify)
    def setPackagePaused(self, pid, paused):
        """ Sets the paused state of a package if possible.

        :param pid:  package id
        :param paused: desired paused state of the package
        :return the new package status
        """
        p = self.core.files.getPackage(pid)
        if not self.checkResult(p):
            raise PackageDoesNotExist(pid)

        if p.status == PS.Ok and paused:
            p.status = PS.Paused
        elif p.status == PS.Paused and not paused:
            p.status = PS.Ok

        p.sync()

        return p.status

    # TODO: multiuser etc..
    @RequirePerm(Permission.Modify)
    def movePackage(self, pid, root):
        """ Set a new root for specific package. This will also moves the files on disk\
           and will only work when no file is currently downloading.

        :param pid: package id
        :param root: package id of new root
        :raises PackageDoesNotExist: When pid or root is missing
        :return: False if package can't be moved
        """
        return self.core.files.movePackage(pid, root)

    @RequirePerm(Permission.Modify)
    def moveFiles(self, fids, pid):
        """Move multiple files to another package. This will move the files on disk and\
        only work when files are not downloading. All files needs to be continuous ordered
        in the current package.

        :param fids: list of file ids
        :param pid: destination package
        :return: False if files can't be moved
        """
        return self.core.files.moveFiles(fids, pid)

    def deleteFiles(self, fids):
        """ Deletes files from disk
        :param fids: list of file ids
        :return: False if any file can't be deleted currently
        """
        # TODO


    def deletePackages(self, pids):
        """ Delete package and all content from disk recursively
        :param pids: list of package ids
        :return: False if any package can't be deleted currently
        """
        # TODO

    @RequirePerm(Permission.Modify)
    def orderPackage(self, pid, position):
        """Set new position for a package.

        :param pid: package id
        :param position: new position, 0 for very beginning
        """
        self.core.files.orderPackage(pid, position)

    @RequirePerm(Permission.Modify)
    def orderFiles(self, fids, pid, position):
        """ Set a new position for a bunch of files within a package.
        All files have to be in the same package and must be **continuous**\
        in the package. That means no gaps between them.

        :param fids: list of file ids
        :param pid: package id of parent package
        :param position:  new position: 0 for very beginning
        """
        self.core.files.orderFiles(fids, pid, position)


if Api.extend(FileApi):
    del FileApi
