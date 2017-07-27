# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import os
from builtins import str

from future import standard_library

from pyload.utils.fs import lopen

from ..datatype.init import Permission
from ..datatype.user import Role
from .base import BaseApi
from .init import requireperm

standard_library.install_aliases()


class DownloadApi(BaseApi):
    """
    Component to create, add, delete or modify downloads.
    """
    # TODO: workaround for link adding without owner
    def true_primary(self):
        if self.user:
            return self.user.true_primary
        else:
            return self.pyload_core.db.get_user_data(role=Role.Admin).uid

    @requireperm(Permission.Add)
    def create_package(self, name, folder, root, password="",
                       site="", comment="", paused=False):
        """
        Create a new package.

        :param name: display name of the package
        :param folder: folder name or relative path, abs path are not allowed
        :param root: package id of root package, -1 for top level package
        :param password: single pw or list of passwords separated with new line
        :param site: arbitrary url to site for more information
        :param comment: arbitrary comment
        :param paused: No downloads will be started when True
        :return: pid of newly created package
        """
        if os.path.isabs(folder):
            folder = folder.replace("/", "_")

        folder = folder.replace("http://", "").replace(":", "")
        folder = folder.replace("\\", "_").replace("..", "")

        self.pyload_core.log.info(
            self._("Added package {0} as folder {1}").format(name, folder))
        pid = self.pyload_core.files.add_package(
            name, folder, root, password, site, comment, paused,
            self.true_primary())

        return pid

    @requireperm(Permission.Add)
    def add_package(self, name, links, password="", paused=False):
        """
        Convenient method to add a package to the top-level
        and for adding links.

        :return: package id
        """
        return self.add_package_child(name, links, password, -1, paused)

    @requireperm(Permission.Add)
    def addPackageP(self, name, links, password, paused):
        """
        Same as above with additional paused attribute.
        """
        return self.add_package_child(name, links, password, -1, paused)

    @requireperm(Permission.Add)
    def add_package_child(self, name, links, password, root, paused):
        """
        Adds a package, with links to desired package.

        :param root: parents package id
        :return: package id of the new package
        """
        if self.pyload_core.config.get('general', 'folder_pack'):
            folder = name
        else:
            folder = ""

        pid = self.create_package(name, folder, root, password, paused=paused)
        self.add_links(pid, links)

        return pid

    @requireperm(Permission.Add)
    def add_links(self, pid, links):
        """
        Adds links to specific package.
        Initiates online status fetching.

        :param pid: package id
        :param links: list of urls
        """
        hoster, crypter = self.pyload_core.pgm.parse_urls(links)

        self.pyload_core.files.add_links(
            hoster + crypter, pid, self.true_primary())
        if hoster:
            self.pyload_core.iom.create_info_thread(hoster, pid)

        self.pyload_core.log.info((self._(
            "Added {0:d} links to package "
            "#{0:d}").format(pid)).format(len(hoster + crypter)))
        self.pyload_core.files.save()

    @requireperm(Permission.Add)
    def upload_container(self, filename, data):
        """
        Uploads and adds a container file to pyLoad.

        :param filename: name of the file
        :param data: file content
        """
        storagedir = self.pyload_core.config.get('general', 'storage_folder')
        filename = 'tmp_{0}'.format(filename)
        filepath = os.path.join(storagedir, filename)
        with lopen(filepath, mode='wb') as fp:
            fp.write(str(data))
            return self.add_package(fp.name, [fp.name])

    @requireperm(Permission.Delete)
    def remove_files(self, fids):
        """
        Removes several file entries from core.

        :param fids: list of file ids
        """
        for fid in fids:
            self.pyload_core.files.remove_file(fid)

        self.pyload_core.files.save()

    @requireperm(Permission.Delete)
    def remove_packages(self, pids):
        """
        Remove packages and containing links.

        :param pids: list of package ids
        """
        for pid in pids:
            self.pyload_core.files.remove_package(pid)

        self.pyload_core.files.save()

    @requireperm(Permission.Modify)
    def restart_package(self, pid):
        """
        Restarts a package, resets every containing files.

        :param pid: package id
        """
        self.pyload_core.files.restart_package(pid)

    @requireperm(Permission.Modify)
    def restart_file(self, fid):
        """
        Resets file status, so it will be downloaded again.

        :param fid: file id
        """
        self.pyload_core.files.restart_file(fid)

    @requireperm(Permission.Modify)
    def recheck_package(self, pid):
        """
        Check online status of all files in a package,
        also a default action when package is added.
        """
        self.pyload_core.files.re_check_package(pid)

    @requireperm(Permission.Modify)
    def restart_failed(self):
        """
        Restarts all failed failes.
        """
        self.pyload_core.files.restart_failed()

    @requireperm(Permission.Modify)
    def stop_all_downloads(self):
        """
        Aborts all running downloads.
        """
        for file in self.pyload_core.files.cached_files():
            if self.has_access(file):
                file.abort_download()

    @requireperm(Permission.Modify)
    def stop_downloads(self, fids):
        """
        Aborts specific downloads.

        :param fids: list of file ids
        :return:
        """
        files = self.pyload_core.files.cached_files()
        for file in files:
            if file.fid in fids and self.has_access(file):
                file.abort_download()
