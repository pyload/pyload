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
from threading import Lock
from time import time

from new_collections import OrderedDict

from module.utils import lock, bits_set, to_list
from module.Api import Input, Output

from InteractionTask import InteractionTask

class InteractionManager:
    """
    Class that gives ability to interact with the user.
    Arbitrary tasks with predefined output and input types can be set off.
    Asynchronous callbacks and default values keep the ability to fallback if no user is present.
    """

    # number of seconds a client is classified as active
    CLIENT_THRESHOLD = 60

    def __init__(self, core):
        self.lock = Lock()
        self.core = core
        self.tasks = OrderedDict() #task store, for outgoing tasks only
        self.notifications = [] #list of notifications

        self.last_clients = {
            Output.Notification : 0,
            Output.Captcha : 0,
            Output.Query : 0,
        }

        self.ids = 0 #only for internal purpose


    def isClientConnected(self, mode=Output.All):
        if mode == Output.All:
            return max(self.last_clients.values()) + self.CLIENT_THRESHOLD <= time()
        else:
            self.last_clients.get(mode, 0) + self.CLIENT_THRESHOLD <= time()

    def updateClient(self, mode):
        t = time()
        for output in self.last_clients:
            if bits_set(output, mode):
                self.last_clients[output] = t

    @lock
    def work(self):
        # old notifications will be removed
        for n in [x for x in self.notifications if x.timedOut()]:
            self.notifications.remove(n)

        # store at most 100 notifications
        del self.notifications[50:]


    @lock
    def createNotification(self, title, content, desc="", plugin=""):
        """ Creates and queues a new Notification

        :param title: short title
        :param content: text content
        :param desc: short form of the notification
        :param plugin: plugin name
        :return: :class:`InteractionTask`
        """
        task = InteractionTask(self.ids, Input.Text, [content], Output.Notification, "", title, desc, plugin)
        self.ids += 1
        self.notifications.insert(0, task)
        self.handleTask(task)
        return task

    @lock
    def newQueryTask(self, input, data, desc, default="", plugin=""):
        task = InteractionTask(self.ids, input, to_list(data), Output.Query, default, _("Query"), desc, plugin)
        self.ids += 1
        return task

    @lock
    def newCaptchaTask(self, img, format, filename, plugin="", input=Input.Text):
        #todo: title desc plugin
        task = InteractionTask(self.ids, input, [img, format, filename],Output.Captcha,
            "", _("Captcha request"), _("Please solve the captcha."), plugin)
        self.ids += 1
        return task

    @lock
    def removeTask(self, task):
        if task.iid in self.tasks:
            del self.tasks[task.iid]

    @lock
    def getTask(self, mode=Output.All):
        self.updateClient(mode)

        for task in self.tasks.itervalues():
            if mode == Output.All or bits_set(task.output, mode):
                return task

    @lock
    def getNotifications(self):
        """retrieves notifications, old ones are only deleted after a while\
             client has to make sure itself to dont display it twice"""
        for n in self.notifications:
            n.setWaiting(self.CLIENT_THRESHOLD * 5, True)
            #store notification for shorter period, lock the timeout

        return self.notifications

    def isTaskWaiting(self, mode=Output.All):
        return self.getTask(mode) is not None

    @lock
    def getTaskByID(self, iid):
        if iid in self.tasks:
            task = self.tasks[iid]
            del self.tasks[iid]
            return task

    def handleTask(self, task):
        cli = self.isClientConnected(task.output)

        if cli: #client connected -> should handle the task
            task.setWaiting(self.CLIENT_THRESHOLD) # wait for response

        if task.output == Output.Notification:
            task.setWaiting(60 * 60 * 30) # notifications are valid for 30h

        for plugin in self.core.addonManager.activePlugins():
            try:
                plugin.newInteractionTask(task)
            except:
                self.core.print_exc()

        if task.output != Output.Notification:
            self.tasks[task.iid] = task


if __name__ == "__main__":

    it = InteractionTask()