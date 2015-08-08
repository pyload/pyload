# -*- coding: utf-8 -*-

import os
import shutil
import subprocess

try:
    import send2trash
except ImportError:
    pass

from module.plugins.internal.Addon import Addon, Expose, threaded
from module.utils import fs_encode, save_join as fs_join


class AntiVirus(Addon):
    __name__    = "AntiVirus"
    __type__    = "hook"
    __version__ = "0.12"
    __status__  = "testing"

    #@TODO: add trash option (use Send2Trash lib)
    __config__ = [("action"    , "Antivirus default;Delete;Quarantine", "Manage infected files"                     , "Antivirus default"),
                  ("quardir"   , "folder"                             , "Quarantine folder"                         , ""                 ),
                  ("deltotrash", "bool"                               , "Move to trash (recycle bin) instead delete", True               ),
                  ("scanfailed", "bool"                               , "Scan incompleted files (failed downloads)" , False              ),
                  ("cmdfile"   , "file"                               , "Antivirus executable"                      , ""                 ),
                  ("cmdargs"   , "str"                                , "Scan options"                              , ""                 ),
                  ("ignore-err", "bool"                               , "Ignore scan errors"                        , False              )]

    __description__ = """Scan downloaded files with antivirus program"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    @Expose
    @threaded
    def scan(self, pyfile, thread):
        file     = fs_encode(pyfile.plugin.last_download)
        filename = os.path.basename(pyfile.plugin.last_download)
        cmdfile  = fs_encode(self.get_config('cmdfile'))
        cmdargs  = fs_encode(self.get_config('cmdargs').strip())

        if not os.path.isfile(file) or not os.path.isfile(cmdfile):
            return

        thread.addActive(pyfile)
        pyfile.setCustomStatus(_("virus scanning"))
        pyfile.setProgress(0)

        try:
            p = subprocess.Popen([cmdfile, cmdargs, file], bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            out, err = map(str.strip, p.communicate())

            if out:
                self.log_info(filename, out)

            if err:
                self.log_warning(filename, err)
                if not self.get_config('ignore-err'):
                    self.log_debug("Delete/Quarantine task is aborted")
                    return

            if p.returncode:
                pyfile.error = _("Infected file")
                action = self.get_config('action')
                try:
                    if action == "Delete":
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

                    elif action == "Quarantine":
                        pyfile.setCustomStatus(_("file moving"))
                        shutil.move(file, self.get_config('quardir'))

                except (IOError, shutil.Error), e:
                    self.log_error(filename, action + " action failed!", e)

            elif not out and not err:
                self.log_debug(filename, "No infected file found")

        finally:
            pyfile.setProgress(100)
            thread.finishFile(pyfile)


    def download_finished(self, pyfile):
        return self.scan(pyfile)


    def download_failed(self, pyfile):
        #: Check if pyfile is still "failed", maybe might has been restarted in meantime
        if pyfile.status == 8 and self.get_config('scanfailed'):
            return self.scan(pyfile)
