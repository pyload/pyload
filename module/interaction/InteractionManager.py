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

    @author: RaNaN
"""
from utils import lock
from traceback import print_exc
from threading import Lock

class InteractionManager:
    """
    Class that gives ability to interact with the user.
    Arbitary task with predefined output and input type can be set off.
    Asyncronous callbacks and default values keeps the ability to fallback if no user is present.
    """
    def __init__(self, core):
        self.lock = Lock()
        self.core = core
        self.tasks = [] #task store, for outgoing tasks only

        self.ids = 0 #only for internal purpose

    def work(self):
        """Mainloop that gets the work done"""

    def newTask(self, img, format, file, result_type):
        task = CaptchaTask(self.ids, img, format, file, result_type)
        self.ids += 1
        return task

    @lock
    def removeTask(self, task):
        if task in self.tasks:
            self.tasks.remove(task)

    @lock
    def getTask(self):
        for task in self.tasks:
            if task.status in ("waiting", "shared-user"):
                return task

    @lock
    def getTaskByID(self, tid):
        for task in self.tasks:
            if task.id == str(tid): #task ids are strings
                self.lock.release()
                return task

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


if __name__ == "__main__":

    it = InteractionTask()