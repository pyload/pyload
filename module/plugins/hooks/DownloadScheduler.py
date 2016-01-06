# -*- coding: utf-8 -*-

import re
import time

from module.plugins.internal.Addon import Addon


class DownloadScheduler(Addon):
    __name__    = "DownloadScheduler"
    __type__    = "hook"
    __version__ = "0.26"
    __status__  = "testing"

    __config__ = [("activated", "bool", "Activated"                                            , False                                    ),
                  ("timetable", "str" , "List time periods as hh:mm full or number(kB/s)"      , "0:00 full, 7:00 250, 10:00 0, 17:00 150"),
                  ("abort"    , "bool", "Abort active downloads when start period with speed 0", False                                    )]

    __description__ = """Download Scheduler"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    def activate(self):
        self.update_schedule()


    def update_schedule(self, schedule=None):
        if schedule is None:
            schedule = self.config.get('timetable')

        schedule = re.findall("(\d{1,2}):(\d{2})[\s]*(-?\d+)",
                              schedule.lower().replace("full", "-1").replace("none", "0"))
        if not schedule:
            self.log_error(_("Invalid schedule"))
            return

        t0  = time.localtime()
        now = (t0.tm_hour, t0.tm_min, t0.tm_sec, "X")
        schedule = sorted([(int(x[0]), int(x[1]), 0, int(x[2])) for x in schedule] + [now])

        self.log_debug("Schedule", schedule)

        for i, v in enumerate(schedule):
            if v[3] == "X":
                last, next = schedule[i - 1], schedule[(i + 1) % len(schedule)]
                self.log_debug("Now/Last/Next", now, last, next)

                self.set_download_speed(last[3])

                next_time = (((24 + next[0] - now[0]) * 60 + next[1] - now[1]) * 60 + next[2] - now[2]) % 86400
                self.pyload.scheduler.removeJob(self.cb)
                self.cb = self.pyload.scheduler.addJob(next_time, self.update_schedule, threaded=False)


    def set_download_speed(self, speed):
        if speed == 0:
            abort = self.config.get('abort')
            self.log_info(_("Stopping download server. (Running downloads will %sbe aborted.)") % '' if abort else _('not '))
            self.pyload.api.pauseServer()
            if abort:
                self.pyload.api.stopAllDownloads()
        else:
            self.pyload.api.unpauseServer()

            if speed > 0:
                self.log_info(_("Setting download speed to %d kB/s") % speed)
                self.pyload.config.set('download', 'limit_speed', 1)
                self.pyload.config.set('download', 'max_speed', speed)
            else:
                self.log_info(_("Setting download speed to FULL"))
                self.pyload.config.set('download', 'limit_speed', 0)
                self.pyload.config.set('download', 'max_speed', -1)
