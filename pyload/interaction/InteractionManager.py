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
from base64 import standard_b64encode

from new_collections import OrderedDict

from pyload.utils import lock, bits_set
from pyload.Api import Interaction as IA
from pyload.Api import InputType, Input

from InteractionTask import InteractionTask


class InteractionManager:
    """
    Class that gives ability to interact with the user.
    Arbitrary tasks with predefined output and input types can be set off.
    """

    # number of seconds a client is classified as active
    CLIENT_THRESHOLD = 60
    NOTIFICATION_TIMEOUT = 60 * 60 * 30
    MAX_NOTIFICATIONS = 50

    def __init__(self, core):
        self.lock = Lock()
        self.core = core
        self.tasks = OrderedDict() #task store, for all outgoing tasks

        self.last_clients = {}
        self.ids = 0 #uniue interaction ids

    def isClientConnected(self, user):
        return self.last_clients.get(user, 0) + self.CLIENT_THRESHOLD > time()

    @lock
    def work(self):
        # old notifications will be removed
        for n in [k for k, v in self.tasks.iteritems() if v.timedOut()]:
            del self.tasks[n]

        # keep notifications count limited
        n = [k for k,v in self.tasks.iteritems() if v.type == IA.Notification]
        n.reverse()
        for v in n[:self.MAX_NOTIFICATIONS]:
            del self.tasks[v]

    @lock
    def createNotification(self, title, content, desc="", plugin="", owner=None):
        """ Creates and queues a new Notification

        :param title: short title
        :param content: text content
        :param desc: short form of the notification
        :param plugin: plugin name
        :return: :class:`InteractionTask`
        """
        task = InteractionTask(self.ids, IA.Notification, Input(InputType.Text, None, content), title, desc, plugin,
                               owner=owner)
        self.ids += 1
        self.queueTask(task)
        return task

    @lock
    def createQueryTask(self, input, desc, plugin="", owner=None):
        # input type was given, create a input widget
        if type(input) == int:
            input = Input(input)
        if not isinstance(input, Input):
            raise TypeError("'Input' class expected not '%s'" % type(input))

        task = InteractionTask(self.ids, IA.Query, input, _("Query"), desc, plugin, owner=owner)
        self.ids += 1
        self.queueTask(task)
        return task

    @lock
    def createCaptchaTask(self, img, format, filename, plugin="", type=InputType.Text, owner=None):
        """ Createss a new captcha task.

        :param img: image content (not base encoded)
        :param format: img format
        :param type: :class:`InputType`
        :return:
        """
        if type == 'textual':
            type = InputType.Text
        elif type == 'positional':
            type = InputType.Click

        input = Input(type, data=[standard_b64encode(img), format, filename])

        #todo: title desc plugin
        task = InteractionTask(self.ids, IA.Captcha, input,
                            _("Captcha request"), _("Please solve the captcha."), plugin, owner=owner)

        self.ids += 1
        self.queueTask(task)
        return task

    @lock
    def removeTask(self, task):
        if task.iid in self.tasks:
            del self.tasks[task.iid]
            self.core.evm.dispatchEvent("interaction:deleted", task.iid)

    @lock
    def getTaskByID(self, iid):
        return self.tasks.get(iid, None)

    @lock
    def getTasks(self, user, mode=IA.All):
        # update last active clients
        self.last_clients[user] = time()

        # filter current mode
        tasks = [t for t in self.tasks.itervalues() if mode == IA.All or bits_set(t.type, mode)]
        # filter correct user / or shared
        tasks = [t for t in tasks if user is None or user == t.owner or t.shared]

        return tasks

    def isTaskWaiting(self, user, mode=IA.All):
        tasks = [t for t in self.getTasks(user, mode) if not t.type == IA.Notification or not t.seen]
        return len(tasks) > 0

    def queueTask(self, task):
        cli = self.isClientConnected(task.owner)

        # set waiting times based on threshold
        if cli:
            task.setWaiting(self.CLIENT_THRESHOLD)
        else: # TODO: higher threshold after client connects?
            task.setWaiting(self.CLIENT_THRESHOLD / 3)

        if task.type == IA.Notification:
            task.setWaiting(self.NOTIFICATION_TIMEOUT) # notifications are valid for 30h

        for plugin in self.core.addonManager.activePlugins():
            try:
                plugin.newInteractionTask(task)
            except:
                self.core.print_exc()

        self.tasks[task.iid] = task
        self.core.evm.dispatchEvent("interaction:added", task)


if __name__ == "__main__":
    it = InteractionTask()