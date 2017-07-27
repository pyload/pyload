# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from future import standard_library

from pyload.utils.purge import uniqify

from ..datatype.file import FileDoesNotExist
from ..datatype.init import DownloadState, Permission
from ..datatype.package import PackageDoesNotExist, PackageStatus
from .base import BaseApi
from .init import requireperm

standard_library.install_aliases()


# TODO: user context
class FileApi(BaseApi):
    """
    Everything related to available packages or files. Deleting,
    Modifying and so on.
    """
    # def check_result(self, info):
    # """
    # Internal method to verify result and owner.
    # """
    # TODO: shared?
    # return info and (not self.primary_uid or info.owner ==
    # self.primary_uid)

    @requireperm(Permission.All)
    def get_all_files(self):
        """
        Same as `getFileTree` for toplevel root and full tree.
        """
        return self.get_file_tree(-1, True)

    @requireperm(Permission.All)
    def get_filtered_files(self, state):
        """
        Same as `getFilteredFileTree` for toplevel root and full tree.
        """
        return self.get_filtered_file_tree(-1, state, True)

    @requireperm(Permission.All)
    def get_file_tree(self, pid, full):
        """
        Retrieve data for specific package.
        full=True will retrieve all data available
        and can result in greater delays.

        :param pid: package id
        :param full: go down the complete tree or only the first layer
        :return: :class:`TreeCollection`
        """
        return self.pyload_core.files.get_tree(pid, full, DownloadState.All)

    @requireperm(Permission.All)
    def get_filtered_file_tree(self, pid, full, state):
        """
        Same as `getFileTree` but only contains files
        with specific download state.

        :param pid: package id
        :param full: go down the complete tree or only the first layer
        :param state: :class:`DownloadState`, the attributes used for filtering
        :return: :class:`TreeCollection`
        """
        return self.pyload_core.files.get_tree(pid, full, state)

    @requireperm(Permission.All)
    def get_package_content(self, pid):
        """
        Only retrieve content of a specific package. see `getFileTree`.
        """
        return self.get_file_tree(pid, False)

    @requireperm(Permission.All)
    def get_package_info(self, pid):
        """
        Returns information about package,
        without detailed information about containing files

        :param pid: package id
        :raises PackageDoesNotExist:
        :return: :class:`PackageInfo`
        """
        info = self.pyload_core.files.get_package_info(pid)
        if not info:
            raise PackageDoesNotExist(pid)
        return info

    @requireperm(Permission.All)
    def get_file_info(self, fid):
        """
        Info for specific file

        :param fid: file id
        :raises FileDoesNotExist:
        :return: :class:`FileInfo`

        """
        info = self.pyload_core.files.get_file_info(fid)
        if not info:
            raise FileDoesNotExist(fid)
        return info

    def get_file_path(self, fid):
        """
        Internal method to get the filepath.
        """
        info = self.get_file_info(fid)
        pack = self.pyload_core.files.get_package(info.package)
        return pack.get_path(), info.name

    @requireperm(Permission.All)
    def find_files(self, pattern):
        return self.pyload_core.files.get_tree(
            -1, True, DownloadState.All, pattern)

    @requireperm(Permission.All)
    def search_suggestions(self, pattern):
        names = self.pyload_core.db.get_matching_filenames(pattern)
        # TODO: stemming and reducing the names to provide better suggestions
        return uniqify(names)

    @requireperm(Permission.All)
    def find_packages(self, tags):
        raise NotImplementedError

    @requireperm(Permission.Modify)
    def update_package(self, pack):
        """
        Allows to modify several package attributes.

        :param pack: :class:`PackageInfo`
        :return updated package info
        """
        pid = pack.pid
        pack_ = self.pyload_core.files.get_package(pid)
        if not pack_:
            raise PackageDoesNotExist(pid)
        pack_.update_from_info_data(pack)
        pack_.sync()
        self.pyload_core.files.save()

    @requireperm(Permission.Modify)
    def set_package_paused(self, pid, paused):
        """
        Sets the paused state of a package if possible.

        :param pid:  package id
        :param paused: desired paused state of the package
        :return the new package status
        """
        pack = self.pyload_core.files.get_package(pid)
        if not pack:
            raise PackageDoesNotExist(pid)

        if pack.status == PackageStatus.Ok and paused:
            pack.status = PackageStatus.Paused
        elif pack.status == PackageStatus.Paused and not paused:
            pack.status = PackageStatus.Ok

        pack.sync()

        return pack.status

    # TODO: multiuser etc..
    @requireperm(Permission.Modify)
    def move_package(self, pid, root):
        """
        Set a new root for specific package.
        This will also moves the files on disk
        and will only work when no file is currently downloading.

        :param pid: package id
        :param root: package id of new root
        :raises PackageDoesNotExist: When pid or root is missing
        :return: False if package can't be moved
        """
        return self.pyload_core.files.move_package(pid, root)

    @requireperm(Permission.Modify)
    def move_files(self, fids, pid):
        """
        Move multiple files to another package.
        This will move the files on disk and
        only work when files are not downloading.
        All files needs to be continuous ordered in the current package.

        :param fids: list of file ids
        :param pid: destination package
        :return: False if files can't be moved
        """
        return self.pyload_core.files.move_files(fids, pid)

    def delete_files(self, fids):
        """
        Deletes files from disk
        :param fids: list of file ids
        :return: False if any file can't be deleted currently
        """
        raise NotImplementedError

    def delete_packages(self, pids):
        """
        Delete package and all content from disk recursively
        :param pids: list of package ids
        :return: False if any package can't be deleted currently
        """
        raise NotImplementedError

    @requireperm(Permission.Modify)
    def order_package(self, pid, position):
        """
        Set new position for a package.

        :param pid: package id
        :param position: new position, 0 for very beginning
        """
        self.pyload_core.files.order_package(pid, position)

    @requireperm(Permission.Modify)
    def order_files(self, fids, pid, position):
        """
        Set a new position for a bunch of files within a package.
        All files have to be in the same package and must be **continuous**
        in the package. That means no gaps between them.

        :param fids: list of file ids
        :param pid: package id of parent package
        :param position:  new position: 0 for very beginning
        """
        self.pyload_core.files.order_files(fids, pid, position)
