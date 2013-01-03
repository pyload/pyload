#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.Api import Api, RequirePerm, Permission, InteractionTask

from ApiComponent import ApiComponent

class UserInteractionApi(ApiComponent):
    """ Everything needed for user interaction """

    @RequirePerm(Permission.Interaction)
    def isInteractionWaiting(self, mode):
        """ Check if task is waiting.

        :param mode: binary or'ed output type
        :return: boolean
        """
        return self.core.interactionManager.isTaskWaiting(mode)

    @RequirePerm(Permission.Interaction)
    def getInteractionTask(self, mode):
        """Retrieve task for specific mode.

        :param mode: binary or'ed output type
        :return: :class:`InteractionTask`
        """
        task = self.core.interactionManager.getTask(mode)
        return InteractionTask(-1) if  not task else task


    @RequirePerm(Permission.Interaction)
    def setInteractionResult(self, iid, result):
        """Set Result for a interaction task. It will be immediately removed from task queue afterwards

        :param iid: interaction id
        :param result: result as string
        """
        task = self.core.interactionManager.getTaskByID(iid)
        if task:
            task.setResult(result)

    @RequirePerm(Permission.Interaction)
    def getNotifications(self):
        """List of all available notifcations. They stay in queue for some time, client should\
           save which notifications it already has seen.

        :return: list of :class:`InteractionTask`
        """
        return self.core.interactionManager.getNotifications()

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