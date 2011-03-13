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
    
    @author: mkaay, RaNaN
"""

from time import time
from traceback import print_exc
from threading import Lock

class CaptchaManager():
    def __init__(self, core):
        self.lock = Lock()
        self.core = core
        self.tasks = [] #task store, for outgoing tasks only

        self.ids = 0 #only for internal purpose

    def newTask(self, img, type, temp):
        task = CaptchaTask(self.ids, img, type, temp)
        self.ids += 1
        return task

    def removeTask(self, task):
        self.lock.acquire()
        if task in self.tasks:
            self.tasks.remove(task)
        self.lock.release()

    def getTask(self):
        self.lock.acquire()
        for task in self.tasks:
            if task.status in ("waiting", "shared-user"):
                self.lock.release()
                return task
        self.lock.release()
        return None

    def getTaskByID(self, tid):
        self.lock.acquire()
        for task in self.tasks:
            if task.id == tid:
                self.lock.release()
                return task
        self.lock.release()
        return None

    def handleCaptcha(self, task):
        cli = self.core.isClientConnected()

        if cli: #client connected -> should solve the captcha
            task.setWaiting(50) #wait 50 sec for response

        for plugin in self.core.hookManager.activePlugins():
            try:
                plugin.newCaptchaTask(task)
            except:
                if self.core.debug:
                    print_exc()
            
        if task.handler or cli: #the captcha was handled
            self.tasks.append(task)
            return True

        task.error = _("No Client connected for captcha decrypting")

        return False


class CaptchaTask():
    def __init__(self, id, img, type, temp):
        self.id = id
        self.captchaImg = img
        self.captchaType = type
        self.captchaFile = temp
        self.handler = [] #the hook plugins that will take care of the solution
        self.result = None
        self.waitUntil = None
        self.error = None #error message

        self.status = "init"
        self.data = {} #handler can store data here

    def getCaptcha(self):
        return self.captchaImg, self.captchaType

    def setResult(self, result):
        self.result = result

    def getResult(self):
        try:
            res = self.result.encode("utf8", "replace")
        except:
            res = self.result

        return res

    def getStatus(self):
        return self.status

    def setWaiting(self, sec):
        """ let the captcha wait secs for the solution """
        self.waitUntil = max(time() + sec, self.waitUntil)
        self.status = "waiting"

    def isWaiting(self):
        if self.result or self.error or time() > self.waitUntil:
            return False

        return True

    def setWatingForUser(self, exclusive):
        if exclusive:
            self.status = "user"
        else:
            self.status = "shared-user"

    def timedOut(self):
        return time() > self.waitUntil

    def invalid(self):
        """ indicates the captcha was not correct """
        [x.captchaInvalid(self) for x in self.handler]

    def correct(self):
        [x.captchaCorrect(self) for x in self.handler]

    def __str__(self):
        return "<CaptchaTask '%s'>" % self.id
