# -*- coding: utf-8 -*-

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
    """
    Provides: unrarFinished (folder, filename)
    """
    __name__ = "ExtractArchive"
    __type__ = "hook"
    __version__ = "0.16"

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

    __description__ = """Extract different kind of archives"""
    __author_name__ = ("pyLoad Team", "AndroKev")
    __author_mail__ = ("admin@pyload.org", "@pyloadforum")

    event_list = ["allDownloadsProcessed"]


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
                    self.logWarning(_("Could not activate %s") % p, str(e))
                    if self.core.debug:
                        print_exc()

            except Exception, e:
                self.logWarning(_("Could not activate %s") % p, str(e))
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
        if self.getConfig("queue"):
            self.logInfo(_("Package %s queued for later extracting") % pypack.name)
            self.queue.append(pypack.id)
        else:
            self.manager.startThread(self.extract, [pypack.id])

    @threaded
    def allDownloadsProcessed(self, thread):
        local = copy(self.queue)
        del self.queue[:]
        self.extract(local, thread)

    def extract(self, ids, thread=None):
        # reload from txt file
        self.reloadPasswords()

        # dl folder
        dl = self.config['general']['download_folder']

        extracted = []

        #iterate packages -> plugins -> targets
        for pid in ids:
            p = self.core.files.getPackage(pid)
            self.logInfo(_("Check package %s") % p.name)
            if not p:
                continue

            # determine output folder
            out = save_join(dl, p.folder, "")
            # force trailing slash

            if self.getConfig("destination") and self.getConfig("destination").lower() != "none":

                out = save_join(dl, p.folder, self.getConfig("destination"), "")
                #relative to package folder if destination is relative, otherwise absolute path overwrites them

                if self.getConfig("subfolder"):
                    out = save_join(out, fs_encode(p.folder))

                if not exists(out):
                    makedirs(out)

            files_ids = [(save_join(dl, p.folder, x['name']), x['id']) for x in p.getChildren().itervalues()]
            matched = False

            # check as long there are unseen files
            while files_ids:
                new_files_ids = []

                for plugin in self.plugins:
                    targets = plugin.getTargets(files_ids)
                    if targets:
                        self.logDebug("Targets for %s: %s" % (plugin.__name__, targets))
                        matched = True
                    for target, fid in targets:
                        if target in extracted:
                            self.logDebug(basename(target), "skipped")
                            continue
                        extracted.append(target)  # prevent extracting same file twice

                        klass = plugin(self, target, out, self.getConfig("fullpath"), self.getConfig("overwrite"), self.getConfig("excludefiles"),
                                       self.getConfig("renice"))
                        klass.init()

                        self.logInfo(basename(target), _("Extract to %s") % out)
                        new_files = self.startExtracting(klass, fid, p.password.strip().splitlines(), thread)
                        self.logDebug("Extracted: %s" % new_files)
                        self.setPermissions(new_files)

                        for file in new_files:
                            if not exists(file):
                                self.logDebug("new file %s does not exists" % file)
                                continue
                            if self.getConfig("recursive") and isfile(file):
                                new_files_ids.append((file, fid))  # append as new target

                files_ids = new_files_ids  # also check extracted files

            if not matched:
                self.logInfo(_("No files found to extract"))

    def startExtracting(self, plugin, fid, passwords, thread):
        pyfile = self.core.files.getFile(fid)
        if not pyfile:
            return []

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
                self.logDebug("Passwords: %s" % str(passwords))

                pwlist = copy(self.getPasswords())
                #remove already supplied pws from list (only local)
                for pw in passwords:
                    if pw in pwlist:
                        pwlist.remove(pw)

                for pw in passwords + pwlist:
                    try:
                        self.logDebug("Try password: %s" % pw)
                        if plugin.checkPassword(pw):
                            plugin.extract(progress, pw)
                            self.addPassword(pw)
                            success = True
                            break
                    except WrongPassword:
                        self.logDebug("Password was wrong")

            if not success:
                self.logError(basename(plugin.file), _("Wrong password"))
                return []

            if self.core.debug:
                self.logDebug("Would delete: %s" % ", ".join(plugin.getDeleteFiles()))

            if self.getConfig("deletearchive"):
                files = plugin.getDeleteFiles()
                self.logInfo(_("Deleting %s files") % len(files))
                for f in files:
                    if exists(f):
                        remove(f)
                    else:
                        self.logDebug("%s does not exists" % f)

            self.logInfo(basename(plugin.file), _("Extracting finished"))
            self.manager.dispatchEvent("unrarFinished", plugin.out, plugin.file)

            return plugin.getExtractedFiles()

        except ArchiveError, e:
            self.logError(basename(plugin.file), _("Archive Error"), str(e))
        except CRCError:
            self.logError(basename(plugin.file), _("CRC Mismatch"))
        except Exception, e:
            if self.core.debug:
                print_exc()
            self.logError(basename(plugin.file), _("Unknown Error"), str(e))

        return []

    @Expose
    def getPasswords(self):
        """ List of saved passwords """
        return self.passwords

    def reloadPasswords(self):
        pwfile = self.getConfig("passwordfile")
        if not exists(pwfile):
            open(pwfile, "wb").close()

        passwords = []
        f = open(pwfile, "rb")
        for pw in f.read().splitlines():
            passwords.append(pw)
        f.close()

        self.passwords = passwords

    @Expose
    def addPassword(self, pw):
        """  Adds a password to saved list"""
        pwfile = self.getConfig("passwordfile")

        if pw in self.passwords:
            self.passwords.remove(pw)
        self.passwords.insert(0, pw)

        f = open(pwfile, "wb")
        for pw in self.passwords:
            f.write(pw + "\n")
        f.close()

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
