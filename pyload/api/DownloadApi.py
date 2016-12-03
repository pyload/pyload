#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from os.path import isabs

from pyload.Api import Api, RequirePerm, Permission, Role
from pyload.utils.fs import join

from .ApiComponent import ApiComponent

class DownloadApi(ApiComponent):
    """ Component to create, add, delete or modify downloads."""

    # TODO: workaround for link adding without owner
    def truePrimary(self):
        if self.user:
            return self.user.true_primary
        else:
            return self.core.db.getUserData(role=Role.Admin).uid

    @RequirePerm(Permission.Add)
    def createPackage(self, name, folder, root, password="", site="", comment="", paused=False):
        """Create a new package.

        :param name: display name of the package
        :param folder: folder name or relative path, abs path are not allowed
        :param root: package id of root package, -1 for top level package
        :param password: single pw or list of passwords separated with new line
        :param site: arbitrary url to site for more information
        :param comment: arbitrary comment
        :param paused: No downloads will be started when True
        :return: pid of newly created package
        """

        if isabs(folder):
            folder = folder.replace("/", "_")

        folder = folder.replace("http://", "").replace(":", "").replace("\\", "_").replace("..", "")

        self.core.log.info(_("Added package %(name)s as folder %(folder)s") % {"name": name, "folder": folder})
        pid = self.core.files.addPackage(name, folder, root, password, site, comment, paused, self.truePrimary())

        return pid


    @RequirePerm(Permission.Add)
    def addPackage(self, name, links, password="", paused=False):
        """Convenient method to add a package to the top-level and for adding links.

        :return: package id
        """
        return self.addPackageChild(name, links, password, -1, paused)

    @RequirePerm(Permission.Add)
    def addPackageP(self, name, links, password, paused):
        """ Same as above with additional paused attribute. """
        return self.addPackageChild(name, links, password, -1, paused)

    @RequirePerm(Permission.Add)
    def addPackageChild(self, name, links, password, root, paused):
        """Adds a package, with links to desired package.

        :param root: parents package id
        :return: package id of the new package
        """
        if self.core.config['general']['folder_per_package']:
            folder = name
        else:
            folder = ""

        pid = self.createPackage(name, folder, root, password, paused=paused)
        self.addLinks(pid, links)

        return pid

    @RequirePerm(Permission.Add)
    def addLinks(self, pid, links):
        """Adds links to specific package. Initiates online status fetching.

        :param pid: package id
        :param links: list of urls
        """
        hoster, crypter = self.core.pluginManager.parseUrls(links)

        self.core.files.addLinks(hoster + crypter, pid, self.truePrimary())
        if hoster:
            self.core.threadManager.createInfoThread(hoster, pid)

        self.core.log.info((_("Added %d links to package") + " #%d" % pid) % len(hoster+crypter))
        self.core.files.save()

    @RequirePerm(Permission.Add)
    def uploadContainer(self, filename, data):
        """Uploads and adds a container file to pyLoad.

        :param filename: filename, extension is important so it can correctly decrypted
        :param data: file content
        """
        th = open(join(self.core.config["general"]["download_folder"], "tmp_" + filename), "wb")
        th.write(str(data))
        th.close()

        return self.addPackage(th.name, [th.name])

    @RequirePerm(Permission.Delete)
    def removeFiles(self, fids):
        """Removes several file entries from pyload.

        :param fids: list of file ids
        """
        for fid in fids:
            self.core.files.removeFile(fid)

        self.core.files.save()

    @RequirePerm(Permission.Delete)
    def removePackages(self, pids):
        """Rempve packages and containing links.

        :param pids: list of package ids
        """
        for pid in pids:
            self.core.files.removePackage(pid)

        self.core.files.save()


    @RequirePerm(Permission.Modify)
    def restartPackage(self, pid):
        """Restarts a package, resets every containing files.

        :param pid: package id
        """
        self.core.files.restartPackage(pid)

    @RequirePerm(Permission.Modify)
    def restartFile(self, fid):
        """Resets file status, so it will be downloaded again.

        :param fid: file id
        """
        self.core.files.restartFile(fid)

    @RequirePerm(Permission.Modify)
    def recheckPackage(self, pid):
        """Check online status of all files in a package, also a default action when package is added. """
        self.core.files.reCheckPackage(pid)

    @RequirePerm(Permission.Modify)
    def restartFailed(self):
        """Restarts all failed failes."""
        self.core.files.restartFailed()

    @RequirePerm(Permission.Modify)
    def stopAllDownloads(self):
        """Aborts all running downloads."""
        for pyfile in self.core.files.cachedFiles():
            if self.hasAccess(pyfile):
                pyfile.abortDownload()

    @RequirePerm(Permission.Modify)
    def stopDownloads(self, fids):
        """Aborts specific downloads.

        :param fids: list of file ids
        :return:
        """
        pyfiles = self.core.files.cachedFiles()
        for pyfile in pyfiles:
            if pyfile.id in fids and self.hasAccess(pyfile):
                pyfile.abortDownload()


if Api.extend(DownloadApi):
    del DownloadApi
