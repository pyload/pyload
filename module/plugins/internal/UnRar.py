# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.
    
    @author: mkaay
"""
from __future__ import with_statement

import sys
import os
from os.path import exists, join, isabs, isdir
from os import remove, makedirs, rmdir, listdir, chmod
from traceback import print_exc

from module.plugins.hooks.ExtractArchive import AbtractExtractor
from module.lib.pyunrar import Unrar, WrongPasswordError, CommandError, UnknownError, LowRamError

from module.utils import save_join



import re

class UnRar(AbtractExtractor):

    def removeFiles(self, pack, fname):
        if not self.getConfig("deletearchive"):
            return
        m = self.re_splitfile.search(fname)

        download_folder = self.core.config['general']['download_folder']
        if self.core.config['general']['folder_per_package']:
            folder = join(download_folder, pack.folder.decode(sys.getfilesystemencoding()))
        else:
            folder = download_folder
        if m:
            nre = re.compile("%s\.part\d+\.rar" % m.group(1))
            for fid, data in pack.getChildren().iteritems():
                if nre.match(data["name"]):
                    remove(join(folder, data["name"]))
        elif not m and fname.endswith(".rar"):
            nre = re.compile("^%s\.r..$" % fname.replace(".rar", ""))
            for fid, data in pack.getChildren().iteritems():
                if nre.match(data["name"]):
                    remove(join(folder, data["name"]))

    def packageFinished(self, pack):
        if pack.password and pack.password.strip() and pack.password.strip() != "None":
            self.addPassword(pack.password.splitlines())
        files = []

        for fid, data in pack.getChildren().iteritems():
            m = self.re_splitfile.search(data["name"])
            if m and int(m.group(2)) == 1:
                files.append((fid, m.group(0)))
            elif not m and data["name"].endswith(".rar"):
                files.append((fid, data["name"]))

        for fid, fname in files:
            self.core.log.info(_("starting Unrar of %s") % fname)
            pyfile = self.core.files.getFile(fid)
            pyfile.setStatus("processing")

            def s(p):
                pyfile.setProgress(p)

            download_folder = self.core.config['general']['download_folder']
            self.core.log.debug(_("download folder %s") % download_folder)

            folder = save_join(download_folder, pack.folder, "")


            destination = folder
            if self.getConfig("unrar_destination") and not self.getConfig("unrar_destination").lower() == "none":
                destination = self.getConfig("unrar_destination")
                sub = "."
                if self.core.config['general']['folder_per_package']:
                    sub = pack.folder.decode(sys.getfilesystemencoding())
                if isabs(destination):
                    destination = join(destination, sub, "")
                else:
                    destination = join(folder, destination, sub, "")

            self.core.log.debug(_("Destination folder %s") % destination)
            if not exists(destination):
                self.core.log.info(_("Creating destination folder %s") % destination)
                makedirs(destination)

            u = Unrar(join(folder, fname), tmpdir=join(folder, "tmp"),
                      ramSize=(self.ram if self.getConfig("ramwarning") else 0), cpu=self.getConfig("renice"))
            try:
                success = u.crackPassword(passwords=self.passwords, statusFunction=s, overwrite=True,
                                          destination=destination, fullPath=self.getConfig("fullpath"))
            except WrongPasswordError:
                self.core.log.info(_("Unrar of %s failed (wrong password)") % fname)
                continue
            except CommandError, e:
                if self.core.debug:
                    print_exc()
                if re.search("Cannot find volume", e.stderr):
                    self.core.log.info(_("Unrar of %s failed (missing volume)") % fname)
                    continue
                try:
                    if e.getExitCode() == 1 and len(u.listContent(u.getPassword())) == 1:
                        self.core.log.info(_("Unrar of %s ok") % fname)
                        self.removeFiles(pack, fname)
                except:
                    if self.core.debug:
                        print_exc()
                    self.core.log.info(_("Unrar of %s failed") % fname)
                    continue
            except LowRamError:
                self.log.warning(_(
                    "Your ram amount of %s MB seems not sufficient to unrar this file. You can deactivate this warning and risk instability") % self.ram)
                continue
            except UnknownError:
                if self.core.debug:
                    print_exc()
                self.core.log.info(_("Unrar of %s failed") % fname)
                continue
            else:
                if success:
                    self.core.log.info(_("Unrar of %s ok") % fname)
                    self.removeFiles(pack, fname)

                    if os.name != "nt" and self.core.config['permission']['change_dl'] and\
                       self.core.config['permission']['change_file']:
                        ownerUser = self.core.config['permission']['user']
                        fileMode = int(self.core.config['permission']['file'], 8)

                        self.core.log.debug("Setting destination file/directory owner / mode to %s / %s"
                        % (ownerUser, fileMode))

                        uinfo = getpwnam(ownerUser)
                        self.core.log.debug("Uid/Gid is %s/%s." % (uinfo.pw_uid, uinfo.pw_gid))
                        self.setOwner(destination, uinfo.pw_uid, uinfo.pw_gid, fileMode)
                        self.core.log.debug("The owner/rights have been successfully changed.")

                    self.core.hookManager.unrarFinished(folder, fname)
                else:
                    self.core.log.info(_("Unrar of %s failed (wrong password or bad parts)") % fname)
            finally:
                pyfile.setProgress(100)
                pyfile.setStatus("finished")
                pyfile.release()

