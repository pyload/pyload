# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from builtins import str
from os.path import isabs

from pyload.api import Api, Permission, Role, require_perm
from pyload.api.base import BaseApi
from pyload.utils.fs import join


class DownloadApi(BaseApi):
    """
    Component to create, add, delete or modify downloads.
    """

    # TODO: workaround for link adding without owner
    def true_primary(self):
        if self.user:
            return self.user.true_primary
        else:
            return self.pyload.db.get_user_data(role=Role.Admin).uid

    @require_perm(Permission.Add)
    def create_package(self, name, folder, root, password="", site="", comment="", paused=False):
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
        if isabs(folder):
            folder = folder.replace("/", "_")

        folder = folder.replace(
            "http://", "").replace(":", "").replace("\\", "_").replace("..", "")

        self.pyload.log.info(
            _("Added package {} as folder {}").format(name, folder))
        pid = self.pyload.files.add_package(
            name, folder, root, password, site, comment, paused, self.true_primary())

        return pid

    @require_perm(Permission.Add)
    def add_package(self, name, links, password="", paused=False):
        """
        Convenient method to add a package to the top-level and for adding links.

        :return: package id
        """
        return self.add_package_child(name, links, password, -1, paused)

    @require_perm(Permission.Add)
    def addPackageP(self, name, links, password, paused):
        """
        Same as above with additional paused attribute.
        """
        return self.add_package_child(name, links, password, -1, paused)

    @require_perm(Permission.Add)
    def add_package_child(self, name, links, password, root, paused):
        """
        Adds a package, with links to desired package.

        :param root: parents package id
        :return: package id of the new package
        """
        if self.pyload.config.get('general', 'folder_pack'):
            folder = name
        else:
            folder = ""

        pid = self.create_package(name, folder, root, password, paused=paused)
        self.add_links(pid, links)

        return pid

    @require_perm(Permission.Add)
    def add_links(self, pid, links):
        """
        Adds links to specific package.
        Initiates online status fetching.

        :param pid: package id
        :param links: list of urls
        """
        hoster, crypter = self.pyload.pgm.parse_urls(links)

        self.pyload.files.add_links(hoster + crypter, pid, self.true_primary())
        if hoster:
            self.pyload.thm.create_info_thread(hoster, pid)

        self.pyload.log.info(
            (_("Added {:d} links to package") + " #{:d}".format(pid)).format(len(hoster + crypter)))
        self.pyload.files.save()

    @require_perm(Permission.Add)
    def upload_container(self, filename, data):
        """
        Uploads and adds a container file to pyLoad.

        :param filename: filename, extension is important so it can correctly decrypted
        :param data: file content
        """
        file = join(self.pyload.config.get(
            'general', 'storage_folder'), "tmp_{}".format(filename))
        with open(file, "wb") as f:
            f.write(str(data))

        return self.add_package(th.name, [th.name])

    @require_perm(Permission.Delete)
    def remove_files(self, fids):
        """
        Removes several file entries from pyload.

        :param fids: list of file ids
        """
        for fid in fids:
            self.pyload.files.remove_file(fid)

        self.pyload.files.save()

    @require_perm(Permission.Delete)
    def remove_packages(self, pids):
        """
        Remove packages and containing links.

        :param pids: list of package ids
        """
        for pid in pids:
            self.pyload.files.remove_package(pid)

        self.pyload.files.save()

    @require_perm(Permission.Modify)
    def restart_package(self, pid):
        """
        Restarts a package, resets every containing files.

        :param pid: package id
        """
        self.pyload.files.restart_package(pid)

    @require_perm(Permission.Modify)
    def restart_file(self, fid):
        """
        Resets file status, so it will be downloaded again.

        :param fid: file id
        """
        self.pyload.files.restart_file(fid)

    @require_perm(Permission.Modify)
    def recheck_package(self, pid):
        """
        Check online status of all files in a package, also a default action when package is added.
        """
        self.pyload.files.re_check_package(pid)

    @require_perm(Permission.Modify)
    def restart_failed(self):
        """
        Restarts all failed failes.
        """
        self.pyload.files.restart_failed()

    @require_perm(Permission.Modify)
    def stop_all_downloads(self):
        """
        Aborts all running downloads.
        """
        for pyfile in self.pyload.files.cached_files():
            if self.has_access(pyfile):
                pyfile.abort_download()

    @require_perm(Permission.Modify)
    def stop_downloads(self, fids):
        """
        Aborts specific downloads.

        :param fids: list of file ids
        :return:
        """
        pyfiles = self.pyload.files.cached_files()
        for pyfile in pyfiles:
            if pyfile.fid in fids and self.has_access(pyfile):
                pyfile.abort_download()


if Api.extend(DownloadApi):
    del DownloadApi
