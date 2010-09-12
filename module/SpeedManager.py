#!/usr/bin/env python
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
    @version: v0.3.2
"""

from threading import Thread
from time import sleep, time

class SpeedManager(Thread):
    def __init__(self, core, hook):
        Thread.__init__(self)
        self.setDaemon(True)

        self.hook = hook
        self.core = core
        self.running = True
        self.lastSlowCheck = 0.0

        stat = {}
        stat["slow_downloads"] = None
        stat["each_speed"] = None
        stat["each_speed_optimized"] = None
        self.stat = stat

        self.slowCheckInterval = 60
        self.slowCheckTestTime = 25

        self.log = self.core.log
        self.start()

    def run(self):
        while self.running:
            sleep(1)
            self.manageSpeed()

    def getMaxSpeed(self):
        return int(self.hook.getConfig("speed"))

    def manageSpeed(self):
        maxSpeed = self.getMaxSpeed()
        if maxSpeed <= 0 or not self.core.compare_time(self.hook.getConfig("start").split(":"),
                                                   self.hook.getConfig("end").split(":")):
            for pyfile in [x.active for x in self.core.threadManager.threads if x.active and x.active != "quit"]:
                pyfile.plugin.req.speedLimitActive = False
            return

        threads = [x.active for x in self.core.threadManager.threads if x.active and x.active != "quit"]
        threadCount = len(threads)
        if not threads:
            return
        eachSpeed = maxSpeed / threadCount

        currentOverallSpeed = 0
        restSpeed = maxSpeed - currentOverallSpeed
        speeds = []
        for thread in threads:
            currentOverallSpeed += thread.plugin.req.dl_speed
            speeds.append((thread.plugin.req.dl_speed, thread.plugin.req.averageSpeed, thread))
            thread.plugin.req.speedLimitActive = True

        if currentOverallSpeed + 50 < maxSpeed:
            for thread in threads:
                thread.plugin.req.speedLimitActive = False
            return

        slowCount = 0
        slowSpeed = 0
        if self.lastSlowCheck + self.slowCheckInterval + self.slowCheckTestTime < time():
            self.lastSlowCheck = time()
        if self.lastSlowCheck + self.slowCheckInterval < time(
        ) < self.lastSlowCheck + self.slowCheckInterval + self.slowCheckTestTime:
            for speed in speeds:
                speed[2].plugin.req.isSlow = False
        else:
            for speed in speeds:
                if speed[0] <= eachSpeed - 7:
                    if speed[1] < eachSpeed - 15:
                        if speed[2].plugin.req.dl_time > 0 and speed[2].plugin.req.dl_time + 30 < time():
                            speed[2].plugin.req.isSlow = True
                            if not speed[1] - 5 < speed[2].plugin.req.maxSpeed / 1024 < speed[1] + 5:
                                speed[2].plugin.req.maxSpeed = (speed[1] + 10) * 1024
                if speed[2].plugin.req.isSlow:
                    slowCount += 1
                    slowSpeed += speed[2].plugin.req.maxSpeed / 1024
        stat = {}
        stat["slow_downloads"] = slowCount
        stat["each_speed"] = eachSpeed
        eachSpeed = (maxSpeed - slowSpeed) / (threadCount - slowCount)
        stat["each_speed_optimized"] = eachSpeed
        self.stat = stat

        for speed in speeds:
            if speed[2].plugin.req.isSlow:
                continue
            speed[2].plugin.req.maxSpeed = eachSpeed * 1024
