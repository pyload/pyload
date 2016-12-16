# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import str
import sys
import os
from os import remove, chmod, makedirs
from os.path import exists, basename, isfile, isdir, join
from traceback import print_exc
from copy import copy

# monkey patch bug in python 2.6 and lower
# see http://bugs.python.org/issue6122
# http://bugs.python.org/issue1236
# http://bugs.python.org/issue1731717
if sys.version_info < (2, 7) and os.name != "nt":
    from subprocess import Popen
    import errno

    def _eintr_retry_call(func, *args):
        while True:
            try:
                return func(*args)
            except OSError as e:
                if e.errno == errno.EINTR:
                    continue
                raise

    # unsued timeout option for older python version
    def wait(self, timeout=0):
        """Wait for child process to terminate.  Returns returncode
        attribute."""
        if self.returncode is None:
            try:
                pid, sts = _eintr_retry_call(os.waitpid, self.pid, 0)
            except OSError as e:
                if e.errno != errno.ECHILD:
                    raise
                    # This happens if SIGCLD is set to be ignored or waiting
                # for child processes has otherwise been disabled for our
                # process.  This child is dead, we can't get the status.
                sts = 0
            self._handle_exitstatus(sts)
        return self.returncode

    Popen.wait = wait

if os.name != "nt":
    from os import chown
    from pwd import getpwnam
    from grp import getgrnam

from pyload.utils.fs import safe_join as save_join, fs_encode

from pyload.plugin.addon import Addon, threaded, addon_handler
from pyload.plugin.internal.abstractextractor import ArchiveError, CRCError, WrongPassword


# TODO: plugin needs a rewrite to work on unfinished packages
class ExtractArchive(Addon):
    """
    Provides: unrarFinished (folder, filename)
    """
    __name__ = "ExtractArchive"
    __version__ = "0.16"
    __description__ = """Extract different kind of archives"""
    __config__ = [("activated", "bool", "Activated", True),
                  ("fullpath", "bool", "Extract full path", True),
                  ("overwrite", "bool", "Overwrite files", True),
                  ("passwordfile", "file", "password file", "unrar_passwords.txt"),
                  ("deletearchive", "bool", "Delete archives when done", False),
                  ("subfolder", "bool", "Create subfolder for each package", False),
                  ("destination", "folder", "Extract files to", ""),
                  ("excludefiles", "str", "Exclude files from unpacking (seperated by ;)", ""),
                  ("recursive", "bool", "Extract archives in archvies", True),
                  ("queue", "bool", "Wait for all downloads to be finished", True),
                  ("renice", "int", "CPU Priority", 0)]
    __author_name__ = ("pyload Team", "AndroKev")
    __author_mail__ = ("admin<at>pyload.net", "@pyloadforum")

    event_list = ["allDownloadsProcessed"]

    def init(self):
        self.plugins = []
        self.passwords = []
        names = []

        for p in ("UnRar", "UnZip"):
            try:
                module = self.pyload.pluginmanager.load_module("internal", p)
                klass = getattr(module, p)
                if klass.check_deps():
                    names.append(p)
                    self.plugins.append(klass)

            except OSError as e:
                if e.errno == 2:
                    self.log_info(_("No %s installed") % p)
                else:
                    self.log_warning(_("Could not activate %s") % p, str(e))
                    if self.pyload.debug:
                        print_exc()

            except Exception as e:
                self.log_warning(_("Could not activate %s") % p, str(e))
                if self.pyload.debug:
                    print_exc()

        if names:
            self.log_info(_("Activated") + " " + " ".join(names))
        else:
            self.log_info(_("No Extract plugins activated"))

        # queue with package ids
        self.queue = []

    @addon_handler(_("Extract package"), _("Scans package for archives and extract them"))
    def extract_package(self, pid):
        """ Extract package with given id"""
        self.manager.start_thread(self.extract, [pid])

    def package_finished(self, pypack):
        if self.get_config("queue"):
            self.log_info(_("Package %s queued for later extracting") % pypack.name)
            self.queue.append(pypack.pid)
        else:
            self.manager.start_thread(self.extract, [pypack.pid])

    @threaded
    def all_downloads_processed(self, thread):
        local = copy(self.queue)
        del self.queue[:]
        self.extract(local, thread)

    def extract(self, ids, thread=None):
        # reload from txt file
        self.reload_passwords()

        # dl folder
        dl = self.config['general']['download_folder']

        extracted = []

        #iterate packages -> plugins -> targets
        for pid in ids:
            p = self.pyload.files.get_package(pid)
            self.log_info(_("Check package %s") % p.name)
            if not p:
                continue

            # determine output folder
            out = save_join(dl, p.folder, "")
            # force trailing slash

            if self.get_config("destination") and self.get_config("destination").lower() != "none":

                out = save_join(dl, p.folder, self.get_config("destination"), "")
                #relative to package folder if destination is relative, otherwise absolute path overwrites them

                if self.get_config("subfolder"):
                    out = join(out, fs_encode(p.folder))

                if not exists(out):
                    makedirs(out)

            files_ids = [(save_join(dl, p.folder, f.name), f.fid) for f in p.get_files().values()]
            matched = False

            # check as long there are unseen files
            while files_ids:
                new_files_ids = []

                for plugin in self.plugins:
                    targets = plugin.getTargets(files_ids)
                    if targets:
                        self.log_debug("Targets for %s: %s" % (plugin.__name__, targets))
                        matched = True
                    for target, fid in targets:
                        if target in extracted:
                            self.log_debug(basename(target), "skipped")
                            continue
                        extracted.append(target)  # prevent extracting same file twice

                        klass = plugin(self, target, out, self.get_config("fullpath"), self.get_config("overwrite"), self.get_config("excludefiles"),
                                       self.get_config("renice"))
                        klass.init()

                        self.log_info(basename(target), _("Extract to %s") % out)
                        new_files = self.start_extracting(klass, fid, p.password.strip().splitlines(), thread)
                        self.log_debug("Extracted: %s" % new_files)
                        self.set_permissions(new_files)

                        for file in new_files:
                            if not exists(file):
                                self.log_debug("new file %s does not exists" % file)
                                continue
                            if self.get_config("recursive") and isfile(file):
                                new_files_ids.append((file, fid))  # append as new target

                files_ids = new_files_ids  # also check extracted files

            if not matched:
                self.log_info(_("No files found to extract"))

    def start_extracting(self, plugin, fid, passwords, thread):
        pyfile = self.pyload.files.get_file(fid)
        if not pyfile:
            return []

        pyfile.setCustomStatus(_("extracting"))
        thread.addActive(pyfile)  # keep this file until everything is done

        try:
            progress = lambda x: thread.setProgress(x)
            success = False

            if not plugin.checkArchive():
                plugin.extract(progress)
                success = True
            else:
                self.log_info(basename(plugin.file), _("Password protected"))
                self.log_debug("Passwords: %s" % str(passwords))

                pwlist = copy(self.get_passwords())
                #remove already supplied pws from list (only local)
                for pw in passwords:
                    if pw in pwlist:
                        pwlist.remove(pw)

                for pw in passwords + pwlist:
                    try:
                        self.log_debug("Try password: %s" % pw)
                        if plugin.checkPassword(pw):
                            plugin.extract(progress, pw)
                            self.add_password(pw)
                            success = True
                            break
                    except WrongPassword:
                        self.log_debug("Password was wrong")

            if not success:
                self.log_error(basename(plugin.file), _("Wrong password"))
                return []

            if self.pyload.debug:
                self.log_debug("Would delete: %s" % ", ".join(plugin.getDeleteFiles()))

            if self.get_config("deletearchive"):
                files = plugin.getDeleteFiles()
                self.log_info(_("Deleting %s files") % len(files))
                for f in files:
                    if exists(f):
                        remove(f)
                    else:
                        self.log_debug("%s does not exists" % f)

            self.log_info(basename(plugin.file), _("Extracting finished"))
            self.manager.dispatch_event("extracting:finished", plugin.out, plugin.file)

            return plugin.getExtractedFiles()

        except ArchiveError as e:
            self.log_error(basename(plugin.file), _("Archive Error"), str(e))
        except CRCError:
            self.log_error(basename(plugin.file), _("CRC Mismatch"))
        except Exception as e:
            if self.pyload.debug:
                print_exc()
            self.log_error(basename(plugin.file), _("Unknown Error"), str(e))

        return []

    # TODO: config handler for passwords?

    def get_passwords(self):
        """ List of saved passwords """
        return self.passwords

    def add_password(self, pw):
        """  Adds a password to saved list"""
        pwfile = self.get_config("passwordfile")

        if pw in self.passwords:
            self.passwords.remove(pw)
        self.passwords.insert(0, pw)

        f = open(pwfile, "wb")
        for pw in self.passwords:
            f.write(pw + "\n")
        f.close()

    def reload_passwords(self):
        pwfile = self.get_config("passwordfile")
        if not exists(pwfile):
            open(pwfile, "wb").close()

        passwords = []
        f = open(pwfile, "rb")
        for pw in f.read().splitlines():
            passwords.append(pw)
        f.close()

        self.passwords = passwords

    def set_permissions(self, files):
        for f in files:
            if not exists(f):
                continue
            try:
                if self.config["permission"]["change_file"]:
                    if isfile(f):
                        chmod(f, int(self.config["permission"]["file"], 8))
                    elif isdir(f):
                        chmod(f, int(self.config["permission"]["folder"], 8))

                if self.config["permission"]["change_dl"] and os.name != "nt":
                    uid = getpwnam(self.config["permission"]["user"])[2]
                    gid = getgrnam(self.config["permission"]["group"])[2]
                    chown(f, uid, gid)
            except Exception as e:
                self.log_warning(_("Setting User and Group failed"), e)
