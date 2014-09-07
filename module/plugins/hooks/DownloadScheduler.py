# -*- coding: utf-8 -*-

import re

from time import localtime

from module.plugins.Hook import Hook


class DownloadScheduler(Hook):
    __name__ = "DownloadScheduler"
    __type__ = "hook"
    __version__ = "0.21"

    __config__ = [("activated", "bool", "Activated", False),
                  ("timetable", "str", "List time periods as hh:mm full or number(kB/s)",
                   "0:00 full, 7:00 250, 10:00 0, 17:00 150"),
                  ("abort", "bool", "Abort active downloads when start period with speed 0", False)]

    __description__ = """Download Scheduler"""
    __author_name__ = ("zoidberg", "stickell")
    __author_mail__ = ("zoidberg@mujmail.cz", "l.stickell@yahoo.it")


    def setup(self):
        self.cb = None  # callback to scheduler job; will be by removed hookmanager when hook unloaded

    def coreReady(self):
        self.updateSchedule()

    def updateSchedule(self, schedule=None):
        if schedule is None:
            schedule = self.getConfig("timetable")

        schedule = re.findall("(\d{1,2}):(\d{2})[\s]*(-?\d+)",
                              schedule.lower().replace("full", "-1").replace("none", "0"))
        if not schedule:
            self.logError("Invalid schedule")
            return

        t0 = localtime()
        now = (t0.tm_hour, t0.tm_min, t0.tm_sec, "X")
        schedule = sorted([(int(x[0]), int(x[1]), 0, int(x[2])) for x in schedule] + [now])

        self.logDebug("Schedule", schedule)

        for i, v in enumerate(schedule):
            if v[3] == "X":
                last, next = schedule[i - 1], schedule[(i + 1) % len(schedule)]
                self.logDebug("Now/Last/Next", now, last, next)

                self.setDownloadSpeed(last[3])

                next_time = (((24 + next[0] - now[0]) * 60 + next[1] - now[1]) * 60 + next[2] - now[2]) % 86400
                self.core.scheduler.removeJob(self.cb)
                self.cb = self.core.scheduler.addJob(next_time, self.updateSchedule, threaded=False)

    def setDownloadSpeed(self, speed):
        if speed == 0:
            abort = self.getConfig("abort")
            self.logInfo("Stopping download server. (Running downloads will %sbe aborted.)" % ('' if abort else 'not '))
            self.core.api.pauseServer()
            if abort:
                self.core.api.stopAllDownloads()
        else:
            self.core.api.unpauseServer()

            if speed > 0:
                self.logInfo("Setting download speed to %d kB/s" % speed)
                self.core.api.setConfigValue("download", "limit_speed", 1)
                self.core.api.setConfigValue("download", "max_speed", speed)
            else:
                self.logInfo("Setting download speed to FULL")
                self.core.api.setConfigValue("download", "limit_speed", 0)
                self.core.api.setConfigValue("download", "max_speed", -1)
