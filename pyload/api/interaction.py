# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals
from __future__ import print_function
from __future__ import division

from future import standard_library
standard_library.install_aliases()
from pyload.api import Api, Interaction, Permission, require_perm
from pyload.api.base import BaseApi


class UserInteractionApi(BaseApi):
    """
    Everything needed for user interaction.
    """

    @require_perm(Permission.Interaction)
    def is_interaction_waiting(self, mode):
        """
        Check if task is waiting.

        :param mode: binary or'ed output type
        :return: boolean
        """
        return self.pyload.im.is_task_waiting(self.primary_uid, mode)

    @require_perm(Permission.Interaction)
    def get_interaction_tasks(self, mode):
        """
        Retrieve task for specific mode.

        :param mode: binary or'ed interaction types which should be retrieved
        :rtype list of :class:`InteractionTask`
        """
        tasks = self.pyload.im.get_tasks(self.primary_uid, mode)
        # retrieved tasks count as seen
        for t in tasks:
            t.seen = True
            if t.type == Interaction.Notification:
                t.set_waiting(self.pyload.im.CLIENT_THRESHOLD)

        return tasks

    @require_perm(Permission.Interaction)
    def set_interaction_result(self, iid, result):
        """
        Set Result for a interaction task. It will be immediately removed from task queue afterwards

        :param iid: interaction id
        :param result: result as json string
        """
        task = self.pyload.im.get_task_by_id(iid)
        if task and self.primary_uid == task.owner:
            task.set_result(result)

    @require_perm(Permission.Interaction)
    def get_addon_handler(self):
        raise NotImplementedError

    @require_perm(Permission.Interaction)
    def call_addon_handler(self, plugin, func, pid_or_fid):
        raise NotImplementedError

    @require_perm(Permission.Download)
    def generate_download_link(self, fid, timeout):
        raise NotImplementedError


if Api.extend(UserInteractionApi):
    del UserInteractionApi
