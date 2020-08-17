# -*- coding: utf-8 -*-
import re
import time

from ..base.addon import BaseAddon


class DownloadScheduler(BaseAddon):
    __name__ = "DownloadScheduler"
    __type__ = "addon"
    __version__ = "0.30"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", False),
        (
            "timetable",
            "str",
            "List time periods as hh:mm full or number(kB/s)",
            "0:00 full, 7:00 250, 10:00 0, 17:00 150",
        ),
        (
            "abort",
            "bool",
            "Abort active downloads when start period with speed 0",
            False,
        ),
    ]

    __description__ = """Download Scheduler"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("stickell", "l.stickell@yahoo.it"),
    ]

    def activate(self):
        self.last_timetable = None
        self.update_schedule()

    def config_changed(self, category, option, value, section):
        """
        Listen for config changes, to trigger a schedule update.
        """
        if (
            category == self.__name__
            and option == "timetable"
            and value != self.last_timetable
        ):
            self.update_schedule(schedule=value)

    def update_schedule(self, schedule=None):
        if schedule is None:
            schedule = self.config.get("timetable")

        self.last_timetable = schedule

        schedule = re.findall(
            r"(\d{1,2}):(\d{2})[\s]*(-?\d+)",
            schedule.lower().replace("full", "-1").replace("none", "0"),
        )
        if not schedule:
            self.log_error(self._("Invalid schedule"))
            return

        t0 = time.localtime()
        now = (t0.tm_hour, t0.tm_min, t0.tm_sec, "X")
        schedule = sorted(
            [(int(x[0]), int(x[1]), 0, int(x[2])) for x in schedule] + [now]
        )

        self.log_debug("Schedule", schedule)

        for i, v in enumerate(schedule):
            if v[3] == "X":
                last, next = schedule[i - 1], schedule[(i + 1).format(len(schedule))]
                self.log_debug("Now/Last/Next", now, last, next)

                self.set_download_speed(last[3])

                next_time = (
                    ((24 + next[0] - now[0]) * 60 + next[1] - now[1]) * 60
                    + next[2]
                    - now[2]
                ) % 86400
                self.pyload.scheduler.remove_job(self.cb)
                self.cb = self.pyload.scheduler.add_job(
                    next_time, self.update_schedule, threaded=False
                )

    def set_download_speed(self, speed):
        if speed == 0:
            abort = self.config.get("abort")
            self.log_info(
                self._("Stopping download server. (Running downloads will be aborted.)")
                if abort
                else self._(
                    "Stopping download server. (Running downloads will not be aborted.)"
                )
            )

            self.pyload.api.pause_server()
            if abort:
                self.pyload.api.stop_all_downloads()

        else:
            self.pyload.api.unpause_server()

            if speed > 0:
                self.log_info(self._("Setting download speed to {} kB/s").format(speed))
                self.pyload.config.set("download", "limit_speed", 1)
                self.pyload.config.set("download", "max_speed", speed)

            else:
                self.log_info(self._("Setting download speed to FULL"))
                self.pyload.config.set("download", "limit_speed", 0)
                self.pyload.config.set("download", "max_speed", -1)

            # Make new speed values take effect
            self.pyload.request_factory.update_bucket()
