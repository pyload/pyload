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
"""

from uuid import uuid4 as uuid
from threading import Lock

class CaptchaManager():
    def __init__(self, core):
        self.lock = Lock()
        self.core = core
        self.tasks = []
    
    def newTask(self, plugin):
        task = CaptchaTask(plugin, self)
        self.lock.acquire()
        self.tasks.append(task)
        self.lock.release()
        return task
    
    def removeTask(self, task):
        self.lock.acquire()
        self.tasks.remove(task)
        self.lock.release()
    
    def getTask(self):
        self.lock.acquire()
        for task in self.tasks:
            status = task.getStatus()
            if status == "waiting" or status == "shared-user":
                self.lock.release()
                return task
        self.lock.release()
        return None
    
    def getTaskFromID(self, tid):
        self.lock.acquire()
        for task in self.tasks:
            if task.getID() == tid:
                self.lock.release()
                return task
        self.lock.release()
        return None

class CaptchaTask():
    def __init__(self, plugin, manager):
        self.lock = Lock()
        self.plugin = plugin
        self.manager = manager
        self.captchaImg = None
        self.captchaType = None
        self.result = None
        self.status = "preparing"
        self.id = uuid().hex
    
    def setCaptcha(self, img, imgType):
        self.lock.acquire()
        self.captchaImg = img
        self.captchaType = imgType
        self.lock.release()
    
    def getCaptcha(self):
        return self.captchaImg, self.captchaType
    
    def setResult(self, result):
        self.lock.acquire()
        self.result = result
        self.lock.release()
    
    def getResult(self):
        try:
            res = self.result.encode("utf8", "replace")
        except:
            res = self.result

        return res
    
    def getID(self):
        return self.id
    
    def getStatus(self):
        return self.status
    
    def setDone(self):
        self.lock.acquire()
        self.status = "done"
        self.lock.release()
    
    def setWaiting(self):
        self.lock.acquire()
        self.status = "waiting"
        self.lock.release()
    
    def setWatingForUser(self, exclusive):
        self.lock.acquire()
        if exclusive:
            self.status = "user"
        else:
            self.status = "shared-user"
        self.lock.release()
    
    def removeTask(self):
        self.manager.removeTask(self)
    
    def __str__(self):
        return "<CaptchaTask '%s'>" % (self.getID(),)
