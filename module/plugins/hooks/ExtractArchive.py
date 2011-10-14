#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from os import remove, chmod
from os.path import exists, basename, isfile, isdir
from traceback import print_exc
from copy import copy

if os.name != "nt":
    from os import chown
    from pwd import getpwnam
    from grp import getgrnam

from module.plugins.Hook import Hook, threaded, Expose
from module.utils import save_join


class ArchiveError(Exception):
    pass


class CRCError(Exception):
    pass


class WrongPassword(Exception):
    pass


class ExtractArchive(Hook):
    __name__ = "ExtractArchive"
    __version__ = "0.1"
    __description__ = "Extract different kind of archives"
    __config__ = [("activated", "bool", "Activated", True),
        ("fullpath", "bool", "Extract full path", True),
        ("overwrite", "bool", "Overwrite files", True),
        ("passwordfile", "file", "password file", "unrar_passwords.txt"),
        ("deletearchive", "bool", "Delete archives when done", False),
        ("destination", "folder", "Extract files to", ""),
        ("queue", "bool", "Wait for all downloads to be fninished", True),
        ("renice", "int", "CPU Priority", 0), ]
    __author_name__ = ("pyload Team")
    __author_mail__ = ("admin<at>pyload.org")

    event_list = ["allDownloadsProcessed"]

    def setup(self):
        self.plugins = []
        self.passwords = []
        names = []

        for p in ("UnRar",):
            try:
                module = self.core.pluginManager.getInternalModule(p)
                klass = getattr(module, p)
                if klass.checkDeps():
                    names.append(p)
                    self.plugins.append(klass)

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
            if not p: continue

            # determine output folder
            out = save_join(dl, p.folder, "")
            # force trailing slash

            if self.getConfig("destination") and self.getConfig("destination").lower() != "none":
                if exists(self.getConfig("destination")):
                    out = save_join(self.getConfig("destination"), "")

            files_ids = [(save_join(dl, p.folder, x["name"]), x["id"]) for x in p.getChildren().itervalues()]

            # check as long there are unseen files
            while files_ids:
                new_files_ids = []

                for plugin in self.plugins:
                    targets = plugin.getTargets(files_ids)
                    self.logDebug("Targets: %s" % targets)
                    for target, fid in targets:
                        if target in extracted:
                            self.logDebug(basename(target), "skipped")
                            continue
                        extracted.append(target) #prevent extracting same file twice

                        klass = plugin(self, target, out, self.getConfig("fullpath"), self.getConfig("overwrite"),
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
                            if isfile(file):
                                new_files_ids.append((file, fid)) #append as new target

                files_ids = new_files_ids # also check extracted files


    def startExtracting(self, plugin, fid, passwords, thread):
        pyfile = self.core.files.getFile(fid)
        if not pyfile: return []

        pyfile.setCustomStatus(_("extracting"))
        thread.addActive(pyfile) #keep this file until everything is done

        try:
            progress = lambda x: pyfile.setProgress(x)
            success = False

            if not plugin.checkArchive():
                plugin.extract(progress)
                success = True
            else:
                self.logInfo(basename(plugin.file), _("Password protected"))
                self.logDebug("Passwords: %s" % str(passwords))
                for pw in passwords + self.getPasswords():
                    try:
                        if plugin.checkPassword(pw):
                            plugin.extract(progress, pw)
                            self.addPassword(pw)
                            success = True
                            break
                    except WrongPassword:
                        self.logDebug("Tried wrong password %s" % pw)

            if not success:
                self.logError(basename(plugin.file), _("Wrong password"))
                return []

            if self.core.debug:
                self.logDebug("Would delete: %s" % ", ".join(plugin.getDeleteFiles()))

            if self.getConfig("deletearchive"):
                files = plugin.getDeleteFiles()
                self.logInfo(_("Deleting %s files") % len(files))
                for f in files:
                    if exists(f): remove(f)
                    else: self.logDebug("%s does not exists" % f)

            self.logInfo(basename(plugin.file), _("Extracting finished"))
            self.core.hookManager.unrarFinished(plugin.out, plugin.file)

            return plugin.getExtractedFiles()


        except ArchiveError, e:
            self.logError(basename(plugin.file), _("Archive Error"), str(e))
        except CRCError:
            self.logError(basename(plugin.file), _("CRC Mismatch"))
        except Exception, e:
            if self.core.debug:
                print_exc()
            self.logError(basename(plugin.file), _("Unkown Error"), str(e))

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

        if pw in self.passwords: self.passwords.remove(pw)
        self.passwords.insert(0, pw)

        f = open(pwfile, "wb")
        for pw in self.passwords:
            f.write(pw + "\n")
        f.close()

    def setPermissions(self, files):
        for f in files:
            if not exists(f): continue
            try:
                if self.core.config["permission"]["change_file"]:
                    if isfile(f):
                        chmod(f, int(self.core.config["permission"]["file"], 8))
                    elif isdir(f):
                        chmod(f, int(self.core.config["permission"]["folder"], 8))

                if self.core.config["permission"]["change_dl"] and os.name != "nt":
                    uid = getpwnam(self.config["permission"]["user"])[2]
                    gid = getgrnam(self.config["permission"]["group"])[2]
                    chown(f, uid, gid)
            except Exception, e:
                self.log.warning(_("Setting User and Group failed"), e)

    def archiveError(self, msg):
        raise ArchiveError(msg)

    def wrongPassword(self):
        raise WrongPassword()

    def crcError(self):
        raise CRCError()


class AbtractExtractor:
    @staticmethod
    def checkDeps():
        """ Check if system statisfy dependencies
        :return: boolean
        """
        return True

    @staticmethod
    def getTargets(files_ids):
        """ Filter suited targets from list of filename id tuple list
        :param files_ids: List of filepathes
        :return: List of targets, id tuple list
        """
        raise NotImplementedError


    def __init__(self, m, file, out, fullpath, overwrite, renice):
        """Initialize extractor for specifiy file

        :param m: ExtractArchive Hook plugin
        :param file: Absolute filepath
        :param out: Absolute path to destination directory
        :param fullpath: extract to fullpath
        :param overwrite: Overwrite existing archives
        :param renice: Renice value
        """
        self.m = m
        self.file = file
        self.out = out
        self.fullpath = fullpath
        self.overwrite = overwrite
        self.renice = renice
        self.files = [] # Store extracted files here


    def init(self):
        """ Initialize additional data structures """
        pass


    def checkArchive(self):
        """Check if password if needed. Raise ArchiveError if integrity is
        questionable.

        :return: boolean
        :raises ArchiveError
        """
        return False

    def checkPassword(self, password):
        """ Check if the given password is/might be correct.
        If it can not be decided at this point return true.

        :param password:
        :return: boolean
        """
        return True

    def extract(self, progress, password=None):
        """Extract the archive. Raise specific errors in case of failure.

        :param progress: Progress function, call this to update status
        :param password password to use
        :raises WrongPassword
        :raises CRCError
        :raises ArchiveError
        :return:
        """
        raise NotImplementedError

    def getDeleteFiles(self):
        """Return list of files to delete, do *not* delete them here.

        :return: List with paths of files to delete
        """
        raise NotImplementedError

    def getExtractedFiles(self):
        """Populate self.files at some point while extracting"""
        return self.files