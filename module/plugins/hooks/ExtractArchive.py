# -*- coding: utf-8 -*-

from __future__ import with_statement

import os
import sys

from copy import copy
from os import remove, chmod, makedirs
from os.path import exists, basename, isfile, isdir
from traceback import print_exc

# monkey patch bug in python 2.6 and lower
# http://bugs.python.org/issue6122 , http://bugs.python.org/issue1236 , http://bugs.python.org/issue1731717
if sys.version_info < (2, 7) and os.name != "nt":
    import errno
    from subprocess import Popen


    def _eintr_retry_call(func, *args):
        while True:
            try:
                return func(*args)
            except OSError, e:
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
            except OSError, e:
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
    from grp import getgrnam
    from os import chown
    from pwd import getpwnam

from module.plugins.Hook import Hook, threaded, Expose
from module.plugins.internal.AbstractExtractor import ArchiveError, CRCError, WrongPassword
from module.utils import save_join, fs_encode


class ExtractArchive(Hook):
    __name__    = "ExtractArchive"
    __type__    = "hook"
    __version__ = "0.19"

    __config__ = [("activated", "bool", "Activated", True),
                  ("fullpath", "bool", "Extract full path", True),
                  ("overwrite", "bool", "Overwrite files", True),
                  ("passwordfile", "file", "password file", "archive_password.txt"),
                  ("deletearchive", "bool", "Delete archives when done", False),
                  ("subfolder", "bool", "Create subfolder for each package", False),
                  ("destination", "folder", "Extract files to", ""),
                  ("excludefiles", "str", "Exclude files from unpacking (seperated by ;)", ""),
                  ("recursive", "bool", "Extract archives in archvies", True),
                  ("queue", "bool", "Wait for all downloads to be finished", True),
                  ("renice", "int", "CPU Priority", 0)]

    __description__ = """Extract different kind of archives"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "ranan@pyload.org"),
                       ("AndroKev", None),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    event_list = ["allDownloadsProcessed"]


    #@TODO: Remove in 0.4.10
    def initPeriodical(self):
        pass


    def setup(self):
        self.plugins = []
        self.passwords = []
        names = []

        for p in ("UnRar", "UnZip"):
            try:
                module = self.core.pluginManager.loadModule("internal", p)
                klass = getattr(module, p)
                if klass.checkDeps():
                    names.append(p)
                    self.plugins.append(klass)

            except OSError, e:
                if e.errno == 2:
                    self.logInfo(_("No %s installed") % p)
                else:
                    self.logWarning(_("Could not activate %s") % p, e)
                    if self.core.debug:
                        print_exc()

            except Exception, e:
                self.logWarning(_("Could not activate %s") % p, e)
                if self.core.debug:
                    print_exc()

        if names:
            self.logInfo(_("Activated") + " " + " ".join(names))
        else:
            self.logInfo(_("No Extract plugins activated"))

        # queue with package ids
        self.queue = []


    @Expose
    def extractPackage(self, id):
        """ Extract package with given id"""
        self.manager.startThread(self.extract, [id])


    def packageFinished(self, pypack):
        pid = pypack.id
        if self.getConfig("queue"):
            self.logInfo(_("Package %s queued for later extracting") % pypack.name)
            self.queue.append(pid)
        else:
            self.manager.startThread(self.extract, [pid])


    @threaded
    def allDownloadsProcessed(self, thread):
        local = copy(self.queue)
        del self.queue[:]
        if self.extract(local, thread):  #: check only if all gone fine, no failed reporting for now
            self.manager.dispatchEvent("all_archives_extracted")
        self.manager.dispatchEvent("all_archives_processed")


    def extract(self, ids, thread=None):
        processed = []
        extracted = []
        failed = []

        destination = self.getConfig("destination")
        subfolder = self.getConfig("subfolder")
        fullpath = self.getConfig("fullpath")
        overwrite = self.getConfig("overwrite")
        excludefiles = self.getConfig("excludefiles")
        renice = self.getConfig("renice")
        recursive = self.getConfig("recursive")

        # reload from txt file
        self.reloadPasswords()

        # dl folder
        dl = self.config['general']['download_folder']

        #iterate packages -> plugins -> targets
        for pid in ids:
            p = self.core.files.getPackage(pid)
            self.logInfo(_("Check package %s") % p.name)
            if not p:
                continue

            # determine output folder
            out = save_join(dl, p.folder, destination, "")  #: force trailing slash

            if subfolder:
                out = save_join(out, fs_encode(p.folder))

            if not exists(out):
                makedirs(out)

            files_ids = [(save_join(dl, p.folder, x['name']), x['id']) for x in p.getChildren().itervalues()]
            matched = False
            success = True

            # check as long there are unseen files
            while files_ids:
                new_files_ids = []

                for plugin in self.plugins:
                    targets = plugin.getTargets(files_ids)
                    if targets:
                        self.logDebug("Targets for %s: %s" % (plugin.__name__, targets))
                        matched = True

                    for target, fid in targets:
                        if target in processed:
                            self.logDebug(basename(target), "skipped")
                            continue

                        processed.append(target)  # prevent extracting same file twice

                        self.logInfo(basename(target), _("Extract to %s") % out)
                        try:
                            klass = plugin(self, target, out, fullpath, overwrite, excludefiles, renice)
                            klass.init()

                            passwords = p.password.strip().splitlines()
                            new_files = self._extract(klass, fid, passwords, thread)

                        except Exception, e:
                            self.logError(basename(target), e)
                            success = False
                            continue

                        self.logDebug("Extracted", new_files)
                        self.setPermissions(new_files)

                        for file in new_files:
                            if not exists(file):
                                self.logDebug("New file %s does not exists" % file)
                                continue
                            if recursive and isfile(file):
                                new_files_ids.append((file, fid))  # append as new target

                files_ids = new_files_ids  # also check extracted files

            if matched:
                if success:
                    extracted.append(pid)
                    self.manager.dispatchEvent("package_extracted", p)
                else:
                    failed.append(pid)
                    self.manager.dispatchEvent("package_extract_failed", p)
            else:
                self.logInfo(_("No files found to extract"))

        return True if not failed else False


    def _extract(self, plugin, fid, passwords, thread):
        pyfile = self.core.files.getFile(fid)
        deletearchive = self.getConfig("deletearchive")

        pyfile.setCustomStatus(_("extracting"))
        thread.addActive(pyfile)  # keep this file until everything is done

        try:
            progress = lambda x: pyfile.setProgress(x)
            success = False

            if not plugin.checkArchive():
                plugin.extract(progress)
                success = True
            else:
                self.logInfo(basename(plugin.file), _("Password protected"))
                self.logDebug("Passwords", passwords)

                for pw in set(passwords) + set(self.getPasswords()):
                    try:
                        self.logDebug("Try password", pw)
                        if plugin.checkPassword(pw):
                            plugin.extract(progress, pw)
                            self.addPassword(pw)
                            success = True
                            break

                    except WrongPassword:
                        self.logDebug("Password was wrong")

            if not success:
                raise Exception(_("Wrong password"))

            if self.core.debug:
                self.logDebug("Would delete", ", ".join(plugin.getDeleteFiles()))

            if deletearchive:
                files = plugin.getDeleteFiles()
                self.logInfo(_("Deleting %s files") % len(files))
                for f in files:
                    if exists(f):
                        remove(f)
                    else:
                        self.logDebug("%s does not exists" % f)

            self.logInfo(basename(plugin.file), _("Extracting finished"))

            extracted_files = plugin.getExtractedFiles()
            self.manager.dispatchEvent("archive_extracted", pyfile, plugin.out, plugin.file, extracted_files)

            return extracted_files

        except ArchiveError, e:
            self.logError(basename(plugin.file), _("Archive Error"), e)

        except CRCError:
            self.logError(basename(plugin.file), _("CRC Mismatch"))

        except Exception, e:
            if self.core.debug:
                print_exc()
            self.logError(basename(plugin.file), _("Unknown Error"), e)

        self.manager.dispatchEvent("archive_extract_failed", pyfile)
        raise Exception(_("Extract failed"))


    @Expose
    def getPasswords(self):
        """ List of saved passwords """
        return self.passwords


    def reloadPasswords(self):
        passwordfile = self.getConfig("passwordfile")

        try:
            passwords = []
            with open(passwordfile, "a+") as f:
                for pw in f.read().splitlines():
                    passwords.append(pw)

        except IOError, e:
            self.logError(e)

        else:
            self.passwords = passwords


    @Expose
    def addPassword(self, pw):
        """  Adds a password to saved list"""
        passwordfile = self.getConfig("passwordfile")

        if pw in self.passwords:
            self.passwords.remove(pw)

        self.passwords.insert(0, pw)

        try:
            with open(passwordfile, "wb") as f:
                for pw in self.passwords:
                    f.write(pw + "\n")
        except IOError, e:
            self.logError(e)


    def setPermissions(self, files):
        for f in files:
            if not exists(f):
                continue
            try:
                if self.config['permission']['change_file']:
                    if isfile(f):
                        chmod(f, int(self.config['permission']['file'], 8))
                    elif isdir(f):
                        chmod(f, int(self.config['permission']['folder'], 8))

                if self.config['permission']['change_dl'] and os.name != "nt":
                    uid = getpwnam(self.config['permission']['user'])[2]
                    gid = getgrnam(self.config['permission']['group'])[2]
                    chown(f, uid, gid)
            except Exception, e:
                self.logWarning(_("Setting User and Group failed"), e)
