# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: zoidberg

Original idea by new.cze
"""
from __future__ import unicode_literals

import re
from time import localtime

from pyload.plugins.hook import Hook


class DownloadScheduler(Hook):
    __name__ = "DownloadScheduler"
    __version__ = "0.21"
    __description__ = """Download Scheduler"""
    __config__ = [("activated", "bool", "Activated", False),
                  ("timetable", "str", "List time periods as hh:mm full or number(kB/s)",
                   "0:00 full, 7:00 250, 10:00 0, 17:00 150"),
                  ("abort", "bool", "Abort active downloads when start period with speed 0", False)]
    __author_name__ = ("zoidberg", "stickell")
    __author_mail__ = ("zoidberg@mujmail.cz", "l.stickell@yahoo.it")

    def setup(self):
        self.cb = None  # callback to scheduler job; will be by removed hookmanager when hook unloaded

    def core_ready(self):
        self.update_schedule()

    def update_schedule(self, schedule=None):
        if schedule is None:
            schedule = self.get_config("timetable")

        schedule = re.findall("(\d{1,2}):(\d{2})[\s]*(-?\d+)",
                              schedule.lower().replace("full", "-1").replace("none", "0"))
        if not schedule:
            self.log_error("Invalid schedule")
            return

        t0 = localtime()
        now = (t0.tm_hour, t0.tm_min, t0.tm_sec, "X")
        schedule = sorted([(int(x[0]), int(x[1]), 0, int(x[2])) for x in schedule] + [now])

        self.log_debug("Schedule", schedule)

        for i, v in enumerate(schedule):
            if v[3] == "X":
                last, next = schedule[i - 1], schedule[(i + 1) % len(schedule)]
                self.log_debug("Now/Last/Next", now, last, next)

                self.set_download_speed(last[3])

                next_time = (((24 + next[0] - now[0]) * 60 + next[1] - now[1]) * 60 + next[2] - now[2]) % 86400
                self.pyload.scheduler.remove_job(self.cb)
                self.cb = self.pyload.scheduler.add_job(next_time, self.updateSchedule, threaded=False)

    def set_download_speed(self, speed):
        if speed == 0:
            abort = self.get_config("abort")
            self.log_info("Stopping download server. (Running downloads will %sbe aborted.)" % ('' if abort else 'not '))
            self.pyload.api.pause_server()
            if abort:
                self.pyload.api.stop_all_downloads()
        else:
            self.pyload.api.unpause_server()

            if speed > 0:
                self.log_info("Setting download speed to %d kB/s" % speed)
                self.pyload.api.set_config_value("download", "limit_speed", 1)
                self.pyload.api.set_config_value("download", "max_speed", speed)
            else:
                self.log_info("Setting download speed to FULL")
                self.pyload.api.set_config_value("download", "limit_speed", 0)
                self.pyload.api.set_config_value("download", "max_speed", -1)
