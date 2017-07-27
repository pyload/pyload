# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, unicode_literals

import time
from base64 import standard_b64encode

from future import standard_library

from pyload.utils.check import bitset
from pyload.utils.layer.legacy.collections_ import OrderedDict
from pyload.utils.struct.lock import lock

from pyload.core.datatype.init import Input, InputType
from pyload.core.datatype.task import Interaction, InteractionTask
from pyload.core.manager.base import BaseManager

standard_library.install_aliases()


class ExchangeManager(BaseManager):
    """
    Class that gives ability to interact with the user.
    Arbitrary tasks with predefined output and input types can be set off
    """
    # number of seconds a client is classified as active
    CLIENT_THRESHOLD = 60
    NOTIFICATION_TIMEOUT = 60 * 60 * 30
    MAX_NOTIFICATIONS = 50

    def __init__(self, core):
        BaseManager.__init__(self, core)
        self.tasks = OrderedDict()  # task store, for all outgoing tasks
        self.last_clients = {}
        self.ids = 0  # uniue interaction ids

    def is_client_connected(self, user):
        return self.last_clients.get(
            user, 0) + self.CLIENT_THRESHOLD > time.time()

    @lock
    def work(self):
        # old notifications will be removed
        for n in (k for k, v in self.tasks.items() if v.timed_out()):
            del self.tasks[n]

        # keep notifications count limited
        n = [
            k for k, v in self.tasks.items()
            if v.type == Interaction.Notification][
            :: -1]
        for v in n[:self.MAX_NOTIFICATIONS]:
            del self.tasks[v]

    @lock
    def create_notification(self, title, content,
                            desc="", plugin="", owner=None):
        """
        Creates and queues a new Notification

        :param title: short title
        :param content: text content
        :param desc: short form of the notification
        :param plugin: plugin name
        :return: :class:`InteractionTask`
        """
        task = InteractionTask(
            self.ids, Interaction.Notification,
            Input(InputType.Str, None, content),
            title, desc, plugin, owner=owner)
        self.ids += 1
        self.queue_task(task)
        return task

    @lock
    def create_query_task(self, input, desc, plugin="", owner=None):
        # input type was given, create a input widget
        if isinstance(input, int):
            input = Input(input)
        if not isinstance(input, Input):
            raise TypeError(
                "'Input' class expected not '{0}'".format(type(input)))

        task = InteractionTask(self.ids, Interaction.Query, input, self._(
            "Query"), desc, plugin, owner=owner)
        self.ids += 1
        self.queue_task(task)
        return task

    @lock
    def create_captcha_task(self, img, format, filename,
                            plugin="", type_=InputType.Str, owner=None):
        """
        Createss a new captcha task.

        :param img: image content (not base encoded)
        :param format: img format
        :param type_: :class:`InputType`
        :return:
        """
        if type_ == 'textual':
            type_ = InputType.Str
        elif type_ == 'positional':
            type_ = InputType.Click

        input = Input(type_, data=[standard_b64encode(img), format, filename])

        # TODO: title desc plugin
        task = InteractionTask(
            self.ids, Interaction.Captcha, input,
            self._("Captcha request"), self._("Please solve the captcha"),
            plugin, owner=owner)

        self.ids += 1
        self.queue_task(task)
        return task

    @lock
    def remove_task(self, task):
        if task.iid in self.tasks:
            del self.tasks[task.iid]
            self.pyload_core.evm.fire("interaction:deleted", task.iid)

    @lock
    def get_task_by_id(self, iid):
        return self.tasks.get(iid, None)

    @lock
    def get_tasks(self, user, mode=Interaction.All):
        # update last active clients
        self.last_clients[user] = time.time()

        # filter current mode
        tasks = [tsk for tsk in self.tasks.values() if mode ==
                 Interaction.All or bitset(tsk.type, mode)]
        # filter correct user / or shared
        tasks = [tsk for tsk in tasks if user is None or user ==
                 tsk.owner or tsk.shared]

        return tasks

    def is_task_waiting(self, user, mode=Interaction.All):
        tasks = [
            tsk for tsk in self.get_tasks(user, mode)
            if not tsk.type == Interaction.Notification or not tsk.seen]
        return len(tasks) > 0

    def queue_task(self, task):
        cli = self.is_client_connected(task.owner)

        # set waiting times based on threshold
        if cli:
            task.set_waiting(self.CLIENT_THRESHOLD)
        else:  # TODO: higher threshold after client connects?
            task.set_waiting(self.CLIENT_THRESHOLD // 3)

        if task.type == Interaction.Notification:
            # notifications are valid for 30h
            task.set_waiting(self.NOTIFICATION_TIMEOUT)

        for plugin in self.pyload_core.adm.active_plugins():
            try:
                plugin.new_interaction_task(task)
            except Exception:
                # self.pyload_core.print_exc()
                pass

        self.tasks[task.iid] = task
        self.pyload_core.evm.fire("interaction:added", task)
