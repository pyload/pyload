# -*- coding: utf-8 -*-

import os
import shutil
import subprocess

try:
    import send2trash
except ImportError:
    pass

from module.plugins.Hook import Hook, Expose, threaded
from module.utils import fs_encode, save_join


class AntiVirus(Hook):
    __name__    = "AntiVirus"
    __type__    = "hook"
    __version__ = "0.09"

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


    interval = 0  #@TODO: Remove in 0.4.10


    def setup(self):
        self.info = {}  #@TODO: Remove in 0.4.10


    @Expose
    @threaded
    def scan(self, pyfile, thread):
        file     = fs_encode(pyfile.plugin.lastDownload)
        filename = os.path.basename(pyfile.plugin.lastDownload)
        cmdfile  = fs_encode(self.getConfig('cmdfile'))
        cmdargs  = fs_encode(self.getConfig('cmdargs').strip())

        if not os.path.isfile(file) or not os.path.isfile(cmdfile):
            return

        thread.addActive(pyfile)
        pyfile.setCustomStatus(_("virus scanning"))
        pyfile.setProgress(0)

        try:
            p = subprocess.Popen([cmdfile, cmdargs, file], bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            out, err = map(str.strip, p.communicate())

            if out:
                self.logInfo(filename, out)

            if err:
                self.logWarning(filename, err)
                if not self.getConfig('ignore-err'):
                    self.logDebug("Delete/Quarantine task is aborted")
                    return

            if p.returncode:
                pyfile.error = _("infected file")
                action = self.getConfig('action')
                try:
                    if action == "Delete":
                        if not self.getConfig('deltotrash'):
                            os.remove(file)

                        else:
                            try:
                                send2trash.send2trash(file)

                            except NameError:
                                self.logWarning(_("Send2Trash lib not found, moving to quarantine instead"))
                                pyfile.setCustomStatus(_("file moving"))
                                shutil.move(file, self.getConfig('quardir'))

                            except Exception, e:
                                self.logWarning(_("Unable to move file to trash: %s, moving to quarantine instead") % e.message)
                                pyfile.setCustomStatus(_("file moving"))
                                shutil.move(file, self.getConfig('quardir'))

                            else:
                                self.logDebug(_("Successfully moved file to trash"))

                    elif action == "Quarantine":
                        pyfile.setCustomStatus(_("file moving"))
                        shutil.move(file, self.getConfig('quardir'))

                except (IOError, shutil.Error), e:
                    self.logError(filename, action + " action failed!", e)

            elif not out and not err:
                self.logDebug(filename, "No infected file found")

        finally:
            pyfile.setProgress(100)
            thread.finishFile(pyfile)


    def downloadFinished(self, pyfile):
        return self.scan(pyfile)


    def downloadFailed(self, pyfile):
        #: Check if pyfile is still "failed",
        #  maybe might has been restarted in meantime
        if pyfile.status == 8 and self.getConfig('scanfailed'):
            return self.scan(pyfile)
