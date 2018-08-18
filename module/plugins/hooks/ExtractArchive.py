# -*- coding: utf-8 -*-

from __future__ import with_statement

import os
import sys

from ..internal.Addon import Addon
from ..internal.Extractor import ArchiveError, CRCError, PasswordError
from ..internal.misc import Expose, encode, exists, fsjoin, safename, threaded, uniqify

# monkey patch bug in python 2.6 and lower
# http://bugs.python.org/issue6122 , http://bugs.python.org/issue1236 ,
# http://bugs.python.org/issue1731717
if sys.version_info < (2, 7) and os.name != "nt":
    import errno
    import subprocess

    def _eintr_retry_call(func, *args):
        while True:
            try:
                return func(*args)

            except OSError, e:
                if e.errno == errno.EINTR:
                    continue
                raise

    #: Unsued timeout option for older python version
    def wait(self, timeout=0):
        """
        Wait for child process to terminate.  Returns returncode
        attribute.
        """
        if self.returncode is None:
            try:
                pid, sts = _eintr_retry_call(os.waitpid, self.pid, 0)

            except OSError, e:
                if e.errno != errno.ECHILD:
                    raise
                #: This happens if SIGCLD is set to be ignored or waiting
                #: For child processes has otherwise been disabled for our
                #: process.  This child is dead, we can't get the status.
                sts = 0
            self._handle_exitstatus(sts)
        return self.returncode

    subprocess.Popen.wait = wait

try:
    import send2trash
except ImportError:
    pass


class ArchiveQueue(object):

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


class ExtractArchive(Addon):
    __name__ = "ExtractArchive"
    __type__ = "hook"
    __version__ = "1.67"
    __status__ = "testing"

    __config__ = [("activated", "bool", "Activated", False),
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
                  ("extensions", "str", "Extract archives ending with extension", "7z,bz2,bzip2,gz,gzip,lha,lzh,lzma,rar,tar,taz,tbz,tbz2,tgz,xar,xz,z,zip"),
                  ("excludefiles", "str", "Don't extract the following files", "*.nfo,*.DS_Store,index.dat,thumb.db"),
                  ("recursive", "bool", "Extract archives in archives", True),
                  ("waitall", "bool", "Run after all downloads was processed", False),
                  ("priority", "int", "Process priority", 0)]

    __description__ = """Extract different kind of archives"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com"),
                   ("Immenz", "immenz@gmx.net"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    def init(self):
        self.event_map = {'allDownloadsProcessed': "all_downloads_processed",
                          'packageDeleted': "package_deleted"}

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
                module = self.pyload.pluginManager.loadModule("internal", p)
                klass = getattr(module, p)
                if klass.find():
                    self.extractors.append(klass)
                if klass.REPAIR:
                    self.repair = self.config.get('repair')

            except OSError, e:
                if e.errno == 2:
                    self.log_warning(_("No %s installed") % p)
                else:
                    self.log_warning(_("Could not activate: %s") % p, e)

            except Exception, e:
                self.log_warning(_("Could not activate: %s") % p, e)

        if self.extractors:
            self.log_debug(*["Found %s %s" % (Extractor.__name__,
                                              Extractor.VERSION) for Extractor in self.extractors])
            self.extract_queued()  #: Resume unfinished extractions
        else:
            self.log_info(_("No Extract plugins activated"))

    @threaded
    def extract_queued(self, thread):
        # @NOTE: doing the check here for safety (called by coreReady)
        if self.extracting:
            return

        self.extracting = True

        packages = self.queue.get()
        while packages:
            if self.last_package:  #: Called from allDownloadsProcessed
                self.last_package = False
                if self.extract(packages, thread):  # @NOTE: check only if all gone fine, no failed reporting for now
                    self.manager.dispatchEvent("all_archives_extracted")
                self.manager.dispatchEvent("all_archives_processed")

            else:
                if self.extract(packages, thread):  # @NOTE: check only if all gone fine, no failed reporting for now
                    pass

            packages = self.queue.get()  #: Check for packages added during extraction

        self.extracting = False

    #: Deprecated method, use `extract_package` instead
    @Expose
    def extractPackage(self, *args, **kwargs):
        """
        See `extract_package`
        """
        return self.extract_package(*args, **kwargs)

    @Expose
    def extract_package(self, *ids):
        """
        Extract packages with given id
        """
        for id in ids:
            self.queue.add(id)
        if not self.config.get('waitall') and not self.extracting:
            self.extract_queued()

    def package_deleted(self, pid):
        self.queue.remove(pid)

    def package_finished(self, pypack):
        self.queue.add(pypack.id)
        if not self.config.get('waitall') and not self.extracting:
            self.extract_queued()

    def all_downloads_processed(self):
        self.last_package = True
        if self.config.get('waitall') and not self.extracting:
            self.extract_queued()

    @Expose
    def extract(self, ids, thread=None):  # @TODO: Use pypack, not pid to improve method usability
        if not ids:
            return False

        extracted = []
        failed = []

        toList = lambda string: string.replace(' ', '').replace(',','|').replace(';', '|').split('|')

        destination = self.config.get('destination')
        subfolder = self.config.get('subfolder')
        fullpath = self.config.get('fullpath')
        overwrite = self.config.get('overwrite')
        priority = self.config.get('priority')
        recursive = self.config.get('recursive')
        keepbroken = self.config.get('keepbroken')

        extensions = [x.lstrip('.').lower()
                      for x in toList(self.config.get('extensions'))]
        excludefiles = toList(self.config.get('excludefiles'))

        if extensions:
            self.log_debug("Use for extensions: .%s" % "|.".join(extensions))

        #: Reload from txt file
        self.reload_passwords()

        dl_folder = self.pyload.config.get("general", "download_folder")

        #: Iterate packages -> extractors -> targets
        for pid in ids:
            pypack = self.pyload.files.getPackage(pid)

            if not pypack:
                self.queue.remove(pid)
                continue

            self.log_info(_("Check package: %s") % pypack.name)

            pack_dl_folder = fsjoin(
                dl_folder,
                pypack.folder,
                "")  #: Force trailing slash

            #: Determine output folder
            extract_folder = fsjoin(
                pack_dl_folder,
                destination,
                "")  #: Force trailing slash

            if subfolder:
                extract_folder = fsjoin(extract_folder,
                                        pypack.folder or safename(pypack.name.replace("http://", "")))

            if not exists(extract_folder):
                os.makedirs(extract_folder)

                if subfolder:
                    self.set_permissions(extract_folder)

            matched = False
            success = True
            files_ids = dict((fdata['name'], (fdata['id'], (fsjoin(pack_dl_folder, fdata['name'])), extract_folder)) for fdata
                             in pypack.getChildren().values()).values()  #: Remove duplicates

            #: Check as long there are unseen files
            while files_ids:
                new_files_ids = []

                if extensions:  #: Include only specified archive types
                    files_ids = filter(lambda file_id: any([Extractor.archivetype(file_id[1]) in extensions
                                                            for Extractor in self.extractors]), files_ids)

                #: Sort by filename to ensure (or at least try) that a multivolume archive is targeted by its first part
                #: This is important because, for example, UnRar ignores preceding parts in listing mode
                files_ids.sort(key=lambda file_id: file_id[1])

                for Extractor in self.extractors:
                    targets = Extractor.get_targets(files_ids)
                    if targets:
                        self.log_debug("Targets for %s: %s" % (Extractor.__name__, targets))
                        matched = True

                        for fid, fname, fout in targets:
                            name = os.path.basename(fname)

                            if not exists(fname):
                                self.log_debug(name, "File not found")
                                continue

                            self.log_info(name, _("Extract to: %s") % fout)
                            try:
                                pyfile = self.pyload.files.getFile(fid)
                                archive = Extractor(pyfile,
                                                    fname,
                                                    fout,
                                                    fullpath,
                                                    overwrite,
                                                    excludefiles,
                                                    priority,
                                                    keepbroken)

                                thread.addActive(pyfile)
                                archive.init()

                                #: Save for removal from file processing list, which happens after deletion.
                                #: So archive.chunks() would just return an empty list.
                                chunks = archive.chunks()

                                try:
                                    new_files = self._extract(pyfile, archive, pypack.password)

                                finally:
                                    pyfile.setProgress(100)
                                    thread.finishFile(pyfile)

                            except Exception, e:
                                self.log_error(name, e)
                                success = False
                                continue

                            #: Remove processed file and related multiparts from list
                            files_ids = [(fid, fname, fout) for fid, fname, fout in files_ids
                                         if fname not in chunks]
                            self.log_debug("Extracted files: %s" % new_files)

                            new_folders = uniqify([os.path.dirname(_f) for _f in new_files])
                            for foldername in new_folders:
                                self.set_permissions(fsjoin(extract_folder, foldername))

                            for filename in new_files:
                                self.set_permissions(fsjoin(extract_folder, filename))

                            for filename in new_files:
                                file = encode(fsjoin(os.path.dirname(archive.filename), filename))
                                if not exists(file):
                                    self.log_debug("New file %s does not exists" % filename)
                                    continue

                                if recursive and os.path.isfile(file):
                                    new_files_ids.append((fid, filename, os.path.dirname(filename)))  #: Append as new target

                            self.manager.dispatchEvent("archive_extracted", pyfile, archive)

                files_ids = new_files_ids  #: Also check extracted files

            if matched:
                if success:
                    #: Delete empty pack folder if extract_folder resides outside download folder
                    if self.config.get('delete') and self.pyload.config.get('general', 'folder_per_package'):
                        if not extract_folder.startswith(pack_dl_folder):
                            if len(os.listdir(pack_dl_folder)) == 0:
                                try:
                                    os.rmdir(pack_dl_folder)
                                    self.log_debug("Successfully deleted pack folder %s" % pack_dl_folder)

                                except OSError:
                                    self.log_warning("Unable to delete pack folder %s" % pack_dl_folder)

                            else:
                                self.log_warning("Not deleting pack folder %s, folder not empty" % pack_dl_folder)

                    extracted.append(pid)
                    self.manager.dispatchEvent("package_extracted", pypack)

                else:
                    failed.append(pid)
                    self.manager.dispatchEvent("package_extract_failed", pypack)

                    self.failed.add(pid)
            else:
                self.log_info(_("No files found to extract"))

            if not matched or not success and subfolder:
                try:
                    os.rmdir(extract_folder)

                except OSError:
                    pass

            self.queue.remove(pid)

        return True if not failed else False

    def _extract(self, pyfile, archive, password):
        name = os.path.basename(archive.filename)

        pyfile.setStatus("processing")

        encrypted = False
        try:
            self.log_debug("Password: %s" % (password or "None provided"))
            passwords = uniqify([password] + self.get_passwords(False)) if \
                self.config.get('usepasswordfile') else [password]

            for pw in passwords:
                try:
                    pyfile.setCustomStatus(_("archive testing"))
                    pyfile.setProgress(0)
                    archive.verify(pw)
                    pyfile.setProgress(100)

                except PasswordError:
                    if not encrypted:
                        self.log_info(name, _("Password protected"))
                        encrypted = True

                except CRCError, e:
                    self.log_debug(name, e)
                    self.log_info(name, _("CRC Error"))

                    if not self.repair:
                        raise CRCError("Archive damaged")

                    else:
                        self.log_warning(name, _("Repairing..."))
                        pyfile.setCustomStatus(_("archive repairing"))
                        pyfile.setProgress(0)
                        repaired = archive.repair()
                        pyfile.setProgress(100)

                        if not repaired and not self.config.get('keepbroken'):
                            raise CRCError("Archive damaged")

                        else:
                            self.add_password(pw)
                            break

                except ArchiveError, e:
                    raise ArchiveError(e)

                else:
                    self.add_password(pw)
                    break

            pyfile.setCustomStatus(_("archive extracting"))
            pyfile.setProgress(0)

            if not encrypted or not self.config.get('usepasswordfile'):
                self.log_debug("Extracting using password: %s" % (password or "None"))
                archive.extract(password)
            else:
                for pw in filter(None, uniqify([password] + self.get_passwords(False))):
                    try:
                        self.log_debug("Extracting using password: %s" % pw)

                        archive.extract(pw)
                        self.add_password(pw)
                        break

                    except PasswordError:
                        self.log_debug("Password was wrong")
                else:
                    raise PasswordError

            pyfile.setProgress(100)
            pyfile.setStatus("processing")

            extracted_files = archive.files or archive.list()

            delfiles = archive.chunks()
            self.log_debug("Would delete: " + ", ".join(delfiles))

            if self.config.get('delete'):
                self.log_info(_("Deleting %s files") % len(delfiles))

                deltotrash = self.config.get('deltotrash')
                for f in delfiles:
                    file = encode(f)
                    if not exists(file):
                        continue

                    if not deltotrash:
                        os.remove(file)

                    else:
                        try:
                            send2trash.send2trash(file)

                        except NameError:
                            self.log_warning(_("Unable to move %s to trash") % os.path.basename(f),
                                             _("Send2Trash lib not found"))

                        except Exception, e:
                            self.log_warning(_("Unable to move %s to trash") % os.path.basename(f),
                                             e.message)

                        else:
                            self.log_info(_("Moved %s to trash") % os.path.basename(f))

            self.log_info(name, _("Extracting finished"))

            return extracted_files

        except PasswordError:
            self.log_error(name, _("Wrong password" if password else "No password found"))

        except CRCError, e:
            self.log_error(name, _("CRC mismatch"), e)

        except ArchiveError, e:
            self.log_error(name, _("Archive error"), e)

        except Exception, e:
            self.log_error(name, _("Unknown error"), e)

        self.manager.dispatchEvent("archive_extract_failed", pyfile, archive)

        raise Exception(_("Extract failed"))

    #: Deprecated method, use `get_passwords` instead
    @Expose
    def getPasswords(self, *args, **kwargs):
        """
        See `get_passwords`
        """
        return self.get_passwords(*args, **kwargs)

    @Expose
    def get_passwords(self, reload=True):
        """
        List of saved passwords
        """
        if reload:
            self.reload_passwords()

        return self.passwords

    def reload_passwords(self):
        try:
            passwords = []

            file = encode(self.config.get('passwordfile'))
            with open(file) as f:
                for pw in f.read().splitlines():
                    passwords.append(pw)

        except IOError, e:
            if e.errno == 2:
                with open(file, "wb") as f:
                    pass

            else:
                self.log_error(e)

        else:
            self.passwords = passwords

    #: Deprecated method, use `add_password` instead
    @Expose
    def addPassword(self, *args, **kwargs):
        """
        See `add_password`
        """
        return self.add_password(*args, **kwargs)

    @Expose
    def add_password(self, password):
        """
         Adds a password to saved list
        """
        try:
            self.passwords = uniqify([password] + self.passwords)

            file = encode(self.config.get('passwordfile'))
            with open(file, "wb") as f:
                for pw in self.passwords:
                    f.write(pw + '\n')

        except IOError, e:
            self.log_error(e)
