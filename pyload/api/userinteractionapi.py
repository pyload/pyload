# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals
from pyload.Api import Api, RequirePerm, Permission, Interaction

from .apicomponent import ApiComponent


class UserInteractionApi(ApiComponent):
    """ Everything needed for user interaction """

    @RequirePerm(Permission.Interaction)
    def isInteractionWaiting(self, mode):
        """ Check if task is waiting.

        :param mode: binary or'ed output type
        :return: boolean
        """
        return self.core.interactionManager.isTaskWaiting(self.primaryUID, mode)

    @RequirePerm(Permission.Interaction)
    def getInteractionTasks(self, mode):
        """Retrieve task for specific mode.

        :param mode: binary or'ed interaction types which should be retrieved
        :rtype list of :class:`InteractionTask`
        """
        tasks = self.core.interactionManager.getTasks(self.primaryUID, mode)
        # retrieved tasks count as seen
        for t in tasks:
            t.seen = True
            if t.type == Interaction.Notification:
                t.setWaiting(self.core.interactionManager.CLIENT_THRESHOLD)

        return tasks

    @RequirePerm(Permission.Interaction)
    def setInteractionResult(self, iid, result):
        """Set Result for a interaction task. It will be immediately removed from task queue afterwards

        :param iid: interaction id
        :param result: result as json string
        """
        task = self.core.interactionManager.getTaskByID(iid)
        if task and self.primaryUID == task.owner:
            task.setResult(result)

    @RequirePerm(Permission.Interaction)
    def getAddonHandler(self):
        pass

    @RequirePerm(Permission.Interaction)
    def callAddonHandler(self, plugin, func, pid_or_fid):
        pass

    @RequirePerm(Permission.Download)
    def generateDownloadLink(self, fid, timeout):
        pass


if Api.extend(UserInteractionApi):
    del UserInteractionApi
