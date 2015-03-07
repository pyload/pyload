# -*- coding: utf-8 -*-

import os
import subprocess

from module.plugins.Hook import Hook, Expose, threaded
from module.utils import fs_encode, save_join


class AntiVirus(Hook):
    __name__    = "AntiVirus"
    __type__    = "hook"
    __version__ = "0.01"

    __config__ = [("action"    , "Antivirus default;Delete;Quarantine", "Manage infected files"                    , "Antivirus default"),
                  ("quarpath"  , "folder"                             , "Quarantine folder"                        , ""                 ),
                  ("scanfailed", "bool"                               , "Scan incompleted files (failed downloads)", False              ),
                  ("cmdpath"   , "file"                               , "Antivirus executable"                     , ""                 ),
                  ("cmdargs"   , "str"                                , "Scan options"                             , ""                 )]

    __description__ = """Scan downloaded files with antivirus program"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    #@TODO: Remove in 0.4.10
    def initPeriodical(self):
        pass


    @Expose
    @threaded
    def scan(self, pyfile, thread):
        name     = os.path.basename(pyfile.plugin.lastDownload)
        filename = fs_encode(pyfile.plugin.lastDownload)
        cmdpath  = fs_encode(self.getConfig('cmdpath'))
        cmdargs  = fs_encode(self.getConfig('cmdargs').strip())

        if not os.path.isfile(filename) or not os.path.isfile(cmdpath):
            return

        pyfile.setCustomStatus(_("virus scanning"))
        thread.addActive(pyfile)

        try:
            p = subprocess.Popen([cmdpath, cmdargs], bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            out, err = map(str.strip, p.communicate())

            if out:
                self.logInfo(name, out)

            if err:
                self.logWarning(name, err)
                return

            if p.returncode:
                action = self.getConfig('action')
                try:
                    if action == "Delete":
                        os.remove(filename)

                    elif action == "Quarantine":
                        new_filename = save_join(self.getConfig('quarpath'), name)
                        os.rename(filename, new_filename)

                except IOError, e:
                    self.logError(name, action + " action failed!", e)

            elif not out:
                self.logDebug(name, "No virus found")

        finally:
            thread.finishFile(pyfile)


    def downloadFinished(self, pyfile):
        return self.scan(pyfile)


    def downloadFailed(self, pyfile):
        #: Check if pyfile is still "failed",
        #  maybe might has been restarted in meantime
        if pyfile.status == 8 and self.getConfig('scanfailed'):
            return self.scan(pyfile)
