# -*- coding: utf-8 -*-

import os

from pyload.core.utils.old import safename
from pyload.core.utils.purge import uniquify

from ..base.addon import BaseAddon, expose, threaded
from ..base.extractor import ArchiveError, CRCError, PasswordError
from ..helpers import exists

try:
    import send2trash
except ImportError:
    send2trash = None


class ArchiveQueue:
    def __init__(self, plugin, storage):
        self.plugin = plugin
        self.storage = storage

    def get(self):
        return self.plugin.db.retrieve(self.storage, default=[])

    def set(self, value):
        return self.plugin.db.store(self.storage, value)

    def delete(self):
        return self.plugin.db.delete(self.storage)

    def add(self, item):
        queue = self.get()
        if item not in queue:
            return self.set(queue + [item])
        else:
            return True

    def remove(self, item):
        queue = self.get()
        try:
            queue.remove(item)

        except ValueError:
            pass

        if queue is []:
            return self.delete()

        return self.set(queue)


class ExtractArchive(BaseAddon):
    __name__ = "ExtractArchive"
    __type__ = "addon"
    __version__ = "1.67"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", False),
        ("fullpath", "bool", "Extract with full paths", True),
        ("overwrite", "bool", "Overwrite files", False),
        ("keepbroken", "bool", "Try to extract broken archives", False),
        ("repair", "bool", "Repair broken archives (RAR required)", False),
        ("usepasswordfile", "bool", "Use password file", True),
        ("passwordfile", "file", "Password file", "passwords.txt"),
        ("delete", "bool", "Delete archive after extraction", True),
        ("deltotrash", "bool", "Move to trash instead delete", True),
        ("subfolder", "bool", "Create subfolder for each package", False),
        ("destination", "folder", "Extract files to folder", ""),
        (
            "extensions",
            "str",
            "Extract archives ending with extension",
            "7z,bz2,bzip2,gz,gzip,lha,lzh,lzma,rar,tar,taz,tbz,tbz2,tgz,xar,xz,z,zip",
        ),
        (
            "excludefiles",
            "str",
            "Don't extract the following files",
            "*.nfo,*.DS_Store,index.dat,thumb.db",
        ),
        ("recursive", "bool", "Extract archives in archives", True),
        ("waitall", "bool", "Run after all downloads was processed", False),
        ("priority", "int", "Process priority", 0),
    ]

    __description__ = """Extract different kind of archives"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("Immenz", "immenz@gmx.net"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    def init(self):
        self.event_map = {
            "all_downloads_processed": "all_downloads_processed",
            "package_deleted": "package_deleted",
        }

        self.queue = ArchiveQueue(self, "Queue")
        self.failed = ArchiveQueue(self, "Failed")

        self.extracting = False
        self.last_package = False
        self.extractors = []
        self.passwords = []
        self.repair = False

    def activate(self):
        for p in ("UnRar", "SevenZip", "UnZip", "UnTar"):
            try:
                module = self.pyload.plugin_manager.load_module("base", p)
                klass = getattr(module, p)
                if klass.find():
                    self.extractors.append(klass)
                if klass.REPAIR:
                    self.repair = self.config.get("repair")

            except OSError as exc:
                if exc.errno == 2:
                    self.log_warning(self._("No {} installed").format(p))
                else:
                    self.log_warning(self._("Could not activate: {}").format(p), exc)

            except Exception as exc:
                self.log_warning(self._("Could not activate: {}").format(p), exc)

        if self.extractors:
            self.log_debug(
                *[
                    "Found {} {}".format(Extractor.__name__, Extractor.VERSION)
                    for Extractor in self.extractors
                ]
            )
            self.extract_queued()  #: Resume unfinished extractions
        else:
            self.log_info(self._("No Extract plugins activated"))

    @threaded
    def extract_queued(self, thread):
        # NOTE: doing the check here for safety (called by core_ready)
        if self.extracting:
            return

        self.extracting = True

        packages = self.queue.get()
        while packages:
            if self.last_package:  #: Called from all_downloads_processed
                self.last_package = False
                if self.extract(
                    packages, thread
                ):  # NOTE: check only if all gone fine, no failed reporting for now
                    self.m.dispatch_event("all_archives_extracted")
                self.m.dispatch_event("all_archives_processed")

            else:
                if self.extract(
                    packages, thread
                ):  # NOTE: check only if all gone fine, no failed reporting for now
                    pass

            packages = self.queue.get()  #: Check for packages added during extraction

        self.extracting = False

    #: Deprecated method, use `extract_package` instead
    @expose
    def extract_package(self, *args, **kwargs):
        """
        See `extract_package`
        """
        return self.extract_package(*args, **kwargs)

    @expose
    def extract_package(self, *ids):
        """
        Extract packages with given id.
        """
        for id in ids:
            self.queue.add(id)
        if not self.config.get("waitall") and not self.extracting:
            self.extract_queued()

    def package_deleted(self, pid):
        self.queue.remove(pid)

    def package_finished(self, pypack):
        self.queue.add(pypack.id)
        if not self.config.get("waitall") and not self.extracting:
            self.extract_queued()

    def all_downloads_processed(self):
        self.last_package = True
        if self.config.get("waitall") and not self.extracting:
            self.extract_queued()

    @expose
    def extract(
        self, ids, thread=None
    ):  # TODO: Use pypack, not pid to improve method usability
        if not ids:
            return False

        extracted = []
        failed = []

        def to_list(value):
            return value.replace(" ", "").replace(",", "|").replace(";", "|").split("|")

        destination = self.config.get("destination")
        subfolder = self.config.get("subfolder")
        fullpath = self.config.get("fullpath")
        overwrite = self.config.get("overwrite")
        priority = self.config.get("priority")
        recursive = self.config.get("recursive")
        keepbroken = self.config.get("keepbroken")

        extensions = [
            x.lstrip(".").lower() for x in to_list(self.config.get("extensions"))
        ]
        excludefiles = to_list(self.config.get("excludefiles"))

        if extensions:
            self.log_debug(f"Use for extensions: .{'|.'.join(extensions)}")

        #: Reload from txt file
        self.reload_passwords()

        dl_folder = self.pyload.config.get("general", "storage_folder")

        #: Iterate packages -> extractors -> targets
        for pid in ids:
            pypack = self.pyload.files.get_package(pid)

            if not pypack:
                self.queue.remove(pid)
                continue

            self.log_info(self._("Check package: {}").format(pypack.name))

            pack_dl_folder = os.path.join(
                dl_folder, pypack.folder, ""
            )  #: Force trailing slash

            #: Determine output folder
            extract_folder = os.path.join(
                pack_dl_folder, destination, ""
            )  #: Force trailing slash

            if subfolder:
                extract_folder = os.path.join(
                    extract_folder,
                    pypack.folder or safename(pypack.name.replace("http://", "")),
                )

            os.makedirs(extract_folder, exist_ok=True)
            if subfolder:
                self.set_permissions(extract_folder)

            matched = False
            success = True
            files_ids = list(
                {
                    fdata["name"]: (
                        fdata["id"],
                        (os.path.join(pack_dl_folder, fdata["name"])),
                        extract_folder,
                    )
                    for fdata in pypack.get_children().values()
                }.values()
            )  #: : Remove duplicates

            #: Check as long there are unseen files
            while files_ids:
                new_files_ids = []

                if extensions:  #: Include only specified archive types
                    files_ids = [
                        file_id
                        for file_id in files_ids
                        if any(
                            [
                                Extractor.archivetype(file_id[1]) in extensions
                                for Extractor in self.extractors
                            ]
                        )
                    ]

                #: Sort by filename to ensure (or at least try) that a multivolume archive is targeted by its first part
                #: This is important because, for example, UnRar ignores preceding parts in listing mode
                files_ids.sort(key=lambda file_id: file_id[1])

                for Extractor in self.extractors:
                    targets = Extractor.get_targets(files_ids)
                    if targets:
                        self.log_debug(
                            "Targets for {}: {}".format(Extractor.__name__, targets)
                        )
                        matched = True

                        for fid, fname, fout in targets:
                            name = os.path.basename(fname)

                            if not exists(fname):
                                self.log_debug(name, "File not found")
                                continue

                            self.log_info(name, self._("Extract to: {}").format(fout))
                            try:
                                pyfile = self.pyload.files.get_file(fid)
                                archive = Extractor(
                                    pyfile,
                                    fname,
                                    fout,
                                    fullpath,
                                    overwrite,
                                    excludefiles,
                                    priority,
                                    keepbroken,
                                )

                                thread.add_active(pyfile)
                                archive.init()

                                #: Save for removal from file processing list, which happens after deletion.
                                #: So archive.chunks() would just return an empty list.
                                chunks = archive.chunks()

                                try:
                                    new_files = self._extract(
                                        pyfile, archive, pypack.password
                                    )

                                finally:
                                    pyfile.set_progress(100)
                                    thread.finish_file(pyfile)

                            except Exception as exc:
                                self.log_error(name, exc)
                                success = False
                                continue

                            #: Remove processed file and related multiparts from list
                            files_ids = [
                                (fid, fname, fout)
                                for fid, fname, fout in files_ids
                                if fname not in chunks
                            ]
                            self.log_debug(f"Extracted files: {new_files}")

                            new_folders = uniquify(
                                os.path.dirname(f) for f in new_files
                            )
                            for foldername in new_folders:
                                self.set_permissions(
                                    os.path.join(extract_folder, foldername)
                                )

                            for filename in new_files:
                                self.set_permissions(
                                    os.path.join(extract_folder, filename)
                                )

                            for filename in new_files:
                                file = os.fsdecode(
                                    os.path.join(
                                        os.path.dirname(archive.filename), filename
                                    )
                                )
                                if not exists(file):
                                    self.log_debug(
                                        "New file {} does not exists".format(filename)
                                    )
                                    continue

                                if recursive and os.path.isfile(file):
                                    new_files_ids.append(
                                        (fid, filename, os.path.dirname(filename))
                                    )  #: Append as new target

                            self.m.dispatch_event("archive_extracted", pyfile, archive)

                files_ids = new_files_ids  #: Also check extracted files

            if matched:
                if success:
                    #: Delete empty pack folder if extract_folder resides outside download folder
                    if self.config.get("delete") and self.pyload.config.get(
                        "general", "folder_per_package"
                    ):
                        if not extract_folder.startswith(pack_dl_folder):
                            if len(os.listdir(pack_dl_folder)) == 0:
                                try:
                                    os.rmdir(pack_dl_folder)
                                    self.log_debug(
                                        "Successfully deleted pack folder {}".format(
                                            pack_dl_folder
                                        )
                                    )

                                except OSError:
                                    self.log_warning(
                                        "Unable to delete pack folder {}".format(
                                            pack_dl_folder
                                        )
                                    )

                            else:
                                self.log_warning(
                                    "Not deleting pack folder {}, folder not empty".format(
                                        pack_dl_folder
                                    )
                                )

                    extracted.append(pid)
                    self.m.dispatch_event("package_extracted", pypack)

                else:
                    failed.append(pid)
                    self.m.dispatch_event("package_extract_failed", pypack)

                    self.failed.add(pid)
            else:
                self.log_info(self._("No files found to extract"))

            if not matched or not success and subfolder:
                try:
                    os.rmdir(extract_folder)

                except OSError:
                    pass

            self.queue.remove(pid)

        return True if not failed else False

    def _extract(self, pyfile, archive, password):
        name = os.path.basename(archive.filename)

        pyfile.set_status("processing")

        encrypted = False
        try:
            self.log_debug(f"Password: {password or None}")
            passwords = (
                uniquify([password] + self.get_passwords(False))
                if self.config.get("usepasswordfile")
                else [password]
            )

            for pw in passwords:
                try:
                    pyfile.set_custom_status(self._("archive testing"))
                    pyfile.set_progress(0)
                    archive.verify(pw)
                    pyfile.set_progress(100)

                except PasswordError:
                    if not encrypted:
                        self.log_info(name, self._("Password protected"))
                        encrypted = True

                except CRCError as exc:
                    self.log_debug(name, exc)
                    self.log_info(name, self._("CRC Error"))

                    if not self.repair:
                        raise CRCError("Archive damaged")

                    else:
                        self.log_warning(name, self._("Repairing..."))
                        pyfile.set_custom_status(self._("archive repairing"))
                        pyfile.set_progress(0)
                        repaired = archive.repair()
                        pyfile.set_progress(100)

                        if not repaired and not self.config.get("keepbroken"):
                            raise CRCError("Archive damaged")

                        else:
                            self.add_password(pw)
                            break

                except ArchiveError as exc:
                    raise ArchiveError(exc)

                else:
                    self.add_password(pw)
                    break

            pyfile.set_custom_status(self._("archive extracting"))
            pyfile.set_progress(0)

            if not encrypted or not self.config.get("usepasswordfile"):
                self.log_debug(
                    "Extracting using password: {}".format(password or "None")
                )
                archive.extract(password)
            else:
                for pw in [
                    f for f in uniquify([password] + self.get_passwords(False)) if f
                ]:
                    try:
                        self.log_debug(f"Extracting using password: {pw}")

                        archive.extract(pw)
                        self.add_password(pw)
                        break

                    except PasswordError:
                        self.log_debug("Password was wrong")
                else:
                    raise PasswordError

            pyfile.set_progress(100)
            pyfile.set_status("processing")

            extracted_files = archive.files or archive.list()

            delfiles = archive.chunks()
            self.log_debug("Would delete: " + ", ".join(delfiles))

            if self.config.get("delete"):
                self.log_info(self._("Deleting {} files").format(len(delfiles)))

                deltotrash = self.config.get("deltotrash")
                for f in delfiles:
                    file = os.fsdecode(f)
                    if not exists(file):
                        continue

                    if not deltotrash:
                        os.remove(file)

                    else:
                        try:
                            send2trash.send2trash(file)

                        except AttributeError:
                            self.log_warning(
                                self._("Unable to move {} to trash").format(
                                    os.path.basename(f)
                                ),
                                self._("Send2Trash lib not found"),
                            )

                        except Exception as exc:
                            self.log_warning(
                                self._("Unable to move {} to trash").format(
                                    os.path.basename(f)
                                ),
                                exc,
                            )

                        else:
                            self.log_info(
                                self._("Moved {} to trash").format(os.path.basename(f))
                            )

            self.log_info(name, self._("Extracting finished"))

            return extracted_files

        except PasswordError:
            self.log_error(
                name, self._("Wrong password" if password else "No password found")
            )

        except CRCError as exc:
            self.log_error(name, self._("CRC mismatch"), exc)

        except ArchiveError as exc:
            self.log_error(name, self._("Archive error"), exc)

        except Exception as exc:
            self.log_error(name, self._("Unknown error"), exc)

        self.m.dispatch_event("archive_extract_failed", pyfile, archive)

        raise Exception(self._("Extract failed"))

    #: Deprecated method, use `get_passwords` instead
    @expose
    def get_passwords(self, *args, **kwargs):
        """
        See `get_passwords`
        """
        return self.get_passwords(*args, **kwargs)

    @expose
    def get_passwords(self, reload=True):
        """
        List of saved passwords.
        """
        if reload:
            self.reload_passwords()

        return self.passwords

    def reload_passwords(self):
        try:
            passwords = []

            file = os.fsdecode(self.config.get("passwordfile"))
            with open(file) as fp:
                for pw in fp.read().splitlines():
                    passwords.append(pw)

        except IOError as exc:
            if exc.errno == 2:
                fp = open(file, mode="w")
                fp.close()

            else:
                self.log_error(exc)

        else:
            self.passwords = passwords

    #: Deprecated method, use `add_password` instead
    @expose
    def add_password(self, *args, **kwargs):
        """
        See `add_password`
        """
        return self.add_password(*args, **kwargs)

    @expose
    def add_password(self, password):
        """
        Adds a password to saved list.
        """
        try:
            self.passwords = uniquify([password] + self.passwords)

            file = os.fsdecode(self.config.get("passwordfile"))
            with open(file, mode="wb") as fp:
                for pw in self.passwords:
                    fp.write(pw + "\n")

        except IOError as exc:
            self.log_error(exc)
