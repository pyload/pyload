# -*- coding: utf-8 -*-

from __future__ import with_statement

import os
import time
import subprocess
import sys

try:
    import caffeine
except ImportError:
    pass

from module.plugins.internal.Addon import Addon, Expose
from module.utils import save_join as fs_join, fs_encode


class Kernel32(object):
    ES_AWAYMODE_REQUIRED = 0x00000040
    ES_CONTINUOUS        = 0x80000000
    ES_DISPLAY_REQUIRED  = 0x00000002
    ES_SYSTEM_REQUIRED   = 0x00000001
    ES_USER_PRESENT      = 0x00000004


class AntiStandby(Addon):
    __name__    = "AntiStandby"
    __type__    = "hook"
    __version__ = "0.11"
    __status__  = "testing"

    __config__ = [("activated", "bool", "Activated"                       , True ),
                  ("hdd"      , "bool", "Prevent HDD standby"             , True ),
                  ("system"   , "bool", "Prevent OS standby"              , True ),
                  ("display"  , "bool", "Prevent display standby"         , False),
                  ("interval" , "int" , "HDD touching interval in seconds", 25   )]

    __description__ = """Prevent OS, HDD and display standby"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    TMP_FILE     = ".antistandby"
    MIN_INTERVAL = 5


    def init(self):
        self.pid   = None
        self.mtime = 0


    def activate(self):
        hdd     = self.get_config('hdd')
        system  = not self.get_config('system')
        display = not self.get_config('display')

        if hdd:
            self.interval = max(self.get_config('interval'), self.MIN_INTERVAL)
            self.init_periodical(threaded=True)

        if os.name == "nt":
            self.win_standby(system, display)

        elif sys.platform == "darwin":
            self.osx_standby(system, display)

        else:
            self.linux_standby(system, display)


    def deactivate(self):
        try:
            os.remove(self.TMP_FILE)

        except OSError:
            pass

        if os.name == "nt":
            self.win_standby(True)

        elif sys.platform == "darwin":
            self.osx_standby(True)

        else:
            self.linux_standby(True)


    @Expose
    def win_standby(self, system=True, display=True):
        import ctypes

        set = ctypes.windll.kernel32.SetThreadExecutionState

        if system:
            if display:
                set(Kernel32.ES_CONTINUOUS)
            else:
                set(Kernel32.ES_CONTINUOUS | Kernel32.ES_DISPLAY_REQUIRED)
        else:
            if display:
                set(Kernel32.ES_CONTINUOUS | Kernel32.ES_SYSTEM_REQUIRED)
            else:
                set(Kernel32.ES_CONTINUOUS | Kernel32.ES_SYSTEM_REQUIRED | Kernel32.ES_DISPLAY_REQUIRED)


    @Expose
    def osx_standby(self, system=True, display=True):
        try:
            if system:
                caffeine.off()
            else:
                caffeine.on(display)

        except NameError:
            self.log_warning(_("Unable to change power state"),
                             _("caffeine lib not found"))

        except Exception, e:
            self.log_warning(_("Unable to change power state"), e)


    @Expose
    def linux_standby(self, system=True, display=True):
        try:
            if system:
                if self.pid:
                    self.pid.kill()

            elif not self.pid:
                self.pid = subprocess.Popen(["caffeine"])

        except Exception, e:
            self.log_warning(_("Unable to change system power state"), e)

        try:
            if display:
                subprocess.call(["xset", "+dpms", "s", "default"])
            else:
                subprocess.call(["xset", "-dpms", "s", "off"])

        except Exception, e:
            self.log_warning(_("Unable to change display power state"), e)


    @Expose
    def touch(self, path):
        with open(path, 'w'):
            os.utime(path, None)

        self.mtime = time.time()


    @Expose
    def max_mtime(self, path):
        return max(0, 0,
                   *(os.path.getmtime(fs_join(root, file))
                        for root, dirs, files in os.walk(fs_encode(path), topdown=False)
                            for file in files))


    def periodical(self):
        if self.get_config('hdd') is False:
            return

        if (self.pyload.threadManager.pause or
                not self.pyload.api.isTimeDownload() or
                    not self.pyload.threadManager.getActiveFiles()):
            return

        download_folder = self.pyload.config.get("general", "download_folder")
        if (self.max_mtime(download_folder) - self.mtime) < self.interval:
            return

        self.touch(self.TMP_FILE)
