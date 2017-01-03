# -*- coding: utf-8 -*-
#@author: RaNaN

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import division
from builtins import object
from threading import Lock
from time import time
from base64 import standard_b64encode

from new_collections import OrderedDict

from pyload.utils import lock, bits_set
from pyload.api import Interaction as IA
from pyload.api import InputType, Input

from pyload.manager.interactiontask import InteractionTask


class InteractionManager(object):
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
        self.pyload = core
        self.tasks = OrderedDict() #task store, for all outgoing tasks

        self.last_clients = {}
        self.ids = 0 #uniue interaction ids

    def is_client_connected(self, user):
        return self.last_clients.get(user, 0) + self.CLIENT_THRESHOLD > time()

    @lock
    def work(self):
        # old notifications will be removed
        for n in [k for k, v in self.tasks.items() if v.timed_out()]:
            del self.tasks[n]

        # keep notifications count limited
        n = [k for k, v in self.tasks.items() if v.type == IA.Notification][::-1]
        for v in n[:self.MAX_NOTIFICATIONS]:
            del self.tasks[v]

    @lock
    def create_notification(self, title, content, desc="", plugin="", owner=None):
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
        self.queue_task(task)
        return task

    @lock
    def create_query_task(self, input, desc, plugin="", owner=None):
        # input type was given, create a input widget
        if isinstance(input, int):
            input = Input(input)
        if not isinstance(input, Input):
            raise TypeError("'Input' class expected not '{}'".format(type(input)))

        task = InteractionTask(self.ids, IA.Query, input, _("Query"), desc, plugin, owner=owner)
        self.ids += 1
        self.queue_task(task)
        return task

    @lock
    def create_captcha_task(self, img, format, filename, plugin="", type=InputType.Text, owner=None):
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
                            _("Captcha request"), _("Please solve the captcha"), plugin, owner=owner)

        self.ids += 1
        self.queue_task(task)
        return task

    @lock
    def remove_task(self, task):
        if task.iid in self.tasks:
            del self.tasks[task.iid]
            self.pyload.evm.dispatch_event("interaction:deleted", task.iid)

    @lock
    def get_task_by_id(self, iid):
        return self.tasks.get(iid, None)

    @lock
    def get_tasks(self, user, mode=IA.All):
        # update last active clients
        self.last_clients[user] = time()

        # filter current mode
        tasks = [t for t in self.tasks.values() if mode == IA.All or bits_set(t.type, mode)]
        # filter correct user / or shared
        tasks = [t for t in tasks if user is None or user == t.owner or t.shared]

        return tasks

    def is_task_waiting(self, user, mode=IA.All):
        tasks = [t for t in self.get_tasks(user, mode) if not t.type == IA.Notification or not t.seen]
        return len(tasks) > 0

    def queue_task(self, task):
        cli = self.is_client_connected(task.owner)

        # set waiting times based on threshold
        if cli:
            task.set_waiting(self.CLIENT_THRESHOLD)
        else: # TODO: higher threshold after client connects?
            task.set_waiting(self.CLIENT_THRESHOLD // 3)

        if task.type == IA.Notification:
            task.set_waiting(self.NOTIFICATION_TIMEOUT) # notifications are valid for 30h

        for plugin in self.pyload.adm.active_plugins():
            try:
                plugin.new_interaction_task(task)
            except Exception:
                self.pyload.print_exc()

        self.tasks[task.iid] = task
        self.pyload.evm.dispatch_event("interaction:added", task)


# if __name__ == "__main__":
    # it = InteractionTask()
