# -*- coding: utf-8 -*-

import os
import shutil
import subprocess

try:
    import send2trash
except ImportError:
    pass

from module.plugins.internal.Addon import Addon, Expose, threaded
from module.plugins.internal.Plugin import exists
from module.utils import fs_encode, save_join as fs_join


class AntiVirus(Addon):
    __name__    = "AntiVirus"
    __type__    = "hook"
    __version__ = "0.14"
    __status__  = "testing"

    #@TODO: add trash option (use Send2Trash lib)
    __config__ = [("activated" , "bool"                               , "Activated"                   , False              ),
                  ("action"    , "Antivirus default;Delete;Quarantine", "Manage infected files"       , "Antivirus default"),
                  ("quardir"   , "folder"                             , "Quarantine folder"           , ""                 ),
                  ("deltotrash", "bool"                               , "Move to trash instead delete", True               ),
                  ("scanfailed", "bool"                               , "Scan failed downloads"       , False              ),
                  ("avfile"    , "file"                               , "Antivirus executable"        , ""                 ),
                  ("avargs"    , "str"                                , "Executable arguments"        , ""                 ),
                  ("avtarget"  , "file;folder"                        , "Scan target"                 , "file"             ),
                  ("ignore-err", "bool"                               , "Ignore scan errors"          , False              )]

    __description__ = """Scan downloaded files with antivirus program"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    @Expose
    @threaded
    def scan(self, pyfile, thread):
        avfile = fs_encode(self.get_config('avfile'))
        avargs = fs_encode(self.get_config('avargs').strip())

        if not os.path.isfile(avfile):
            self.fail(_("Antivirus executable not found"))

        scanfolder = self.get_config('avtarget') is "folder"

        if scanfolder:
            download_folder = self.pyload.config.get("general", "download_folder")
            package_folder  = pyfile.package().folder if self.pyload.config.get("general", "folder_per_package") else ""
            target      = fs_join(download_folder, package_folder, pyfile.name)
            target_repr = "Folder: " + package_folder or download_folder
        else:
            target      = fs_encode(pyfile.plugin.last_download)
            target_repr = "File: " + os.path.basename(pyfile.plugin.last_download)

        if not exists(target):
            return

        thread.addActive(pyfile)
        pyfile.setCustomStatus(_("virus scanning"))
        pyfile.setProgress(0)

        try:
            p = subprocess.Popen([avfile, avargs, target],
                                 bufsize=-1,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)

            out, err = map(str.strip, p.communicate())

            if out:
                self.log_info(target_repr, out)

            if err:
                self.log_warning(target_repr, err)
                if not self.get_config('ignore-err'):
                    self.log_debug("Delete/Quarantine task aborted due scan error")
                    return

            if p.returncode:
                action = self.get_config('action')

                if scanfolder:
                    if action is "Antivirus default":
                        self.log_warning(_("Delete/Quarantine task skipped in folder scan mode"))
                    return

                pyfile.error = _("Infected file")

                try:
                    if action is "Delete":
                        if not self.get_config('deltotrash'):
                            os.remove(file)

                        else:
                            try:
                                send2trash.send2trash(file)

                            except NameError:
                                self.log_warning(_("Send2Trash lib not found, moving to quarantine instead"))
                                pyfile.setCustomStatus(_("file moving"))
                                shutil.move(file, self.get_config('quardir'))

                            except Exception, e:
                                self.log_warning(_("Unable to move file to trash: %s, moving to quarantine instead") % e.message)
                                pyfile.setCustomStatus(_("file moving"))
                                shutil.move(file, self.get_config('quardir'))

                            else:
                                self.log_debug("Successfully moved file to trash")

                    elif action is "Quarantine":
                        pyfile.setCustomStatus(_("file moving"))
                        shutil.move(file, self.get_config('quardir'))

                except (IOError, shutil.Error), e:
                    self.log_error(target_repr, action + " action failed!", e)

            elif not err:
                self.log_debug(target_repr, "No infected file found")

        finally:
            pyfile.setProgress(100)
            thread.finishFile(pyfile)


    def download_finished(self, pyfile):
        return self.scan(pyfile)


    def download_failed(self, pyfile):
        #: Check if pyfile is still "failed", maybe might has been restarted in meantime
        if pyfile.status is 8 and self.get_config('scanfailed'):
            return self.scan(pyfile)
