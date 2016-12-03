# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals
from pyload.Api import Api, RequirePerm, Permission, StatusInfo, Interaction
from pyload.utils.fs import join, free_space, exists
from pyload.utils import compare_time

from .ApiComponent import ApiComponent

class CoreApi(ApiComponent):
    """ This module provides methods for general interaction with the core, like status or progress retrieval  """

    @RequirePerm(Permission.All)
    def getServerVersion(self):
        """pyLoad Core version """
        return self.core.version

    def isWSSecure(self):
        # needs to use TLS when either requested or webUI is also using encryption
        if not self.core.config['ssl']['activated'] or self.core.config['webUI']['https']:
            return False

        if not exists(self.core.config['ssl']['cert']) or not exists(self.core.config['ssl']['key']):
            self.core.log.warning(_('SSL key or certificate not found'))
            return False

        return True

    @RequirePerm(Permission.All)
    def getWSAddress(self):
        """Gets and address for the websocket based on configuration"""
        if self.isWSSecure():
            ws = "wss"
        else:
            ws = "ws"

        return "%s://%%s:%d" % (ws, self.core.config['webUI']['wsPort'])

    @RequirePerm(Permission.All)
    def getStatusInfo(self):
        """Some general information about the current status of pyLoad.

        :return: `StatusInfo`
        """
        queue = self.core.files.getQueueStats(self.primaryUID)
        total = self.core.files.getDownloadStats(self.primaryUID)

        serverStatus = StatusInfo(0,
                                    total[0], queue[0],
                                    total[1], queue[1],
                                    self.isInteractionWaiting(Interaction.All),
                                    not self.core.dlm.paused and self.isTimeDownload(),
                                    self.core.dlm.paused,
                                    self.core.config['reconnect']['activated'] and self.isTimeReconnect(),
                                    self.getQuota())

        for pyfile in self.core.dlm.activeDownloads(self.primaryUID):
            serverStatus.speed += pyfile.getSpeed() #bytes/s

        return serverStatus

    @RequirePerm(Permission.All)
    def getProgressInfo(self):
        """ Status of all currently running tasks

        :rtype: list of :class:`ProgressInfo`
        """
        return self.core.dlm.getProgressList(self.primaryUID) +\
            self.core.threadManager.getProgressList(self.primaryUID)

    def pauseServer(self):
        """Pause server: It won't start any new downloads, but nothing gets aborted."""
        self.core.dlm.paused = True

    def unpauseServer(self):
        """Unpause server: New Downloads will be started."""
        self.core.dlm.paused = False

    def togglePause(self):
        """Toggle pause state.

        :return: new pause state
        """
        self.core.dlm.paused ^= True
        return self.core.dlm.paused

    def toggleReconnect(self):
        """Toggle reconnect activation.

        :return: new reconnect state
        """
        self.core.config["reconnect"]["activated"] ^= True
        return self.core.config["reconnect"]["activated"]

    def freeSpace(self):
        """Available free space at download directory in bytes"""
        return free_space(self.core.config["general"]["download_folder"])


    def quit(self):
        """Clean way to quit pyLoad"""
        self.core.do_kill = True

    def restart(self):
        """Restart pyload core"""
        self.core.do_restart = True

    def getLog(self, offset=0):
        """Returns most recent log entries.

        :param offset: line offset
        :return: List of log entries
        """
        filename = join(self.core.config['log']['log_folder'], 'log.txt')
        try:
            fh = open(filename, "r")
            lines = fh.readlines()
            fh.close()
            if offset >= len(lines):
                return []
            return lines[offset:]
        except:
            return ['No log available']

    @RequirePerm(Permission.All)
    def isTimeDownload(self):
        """Checks if pyload will start new downloads according to time in config.

        :return: bool
        """
        start = self.core.config['downloadTime']['start'].split(":")
        end = self.core.config['downloadTime']['end'].split(":")
        return compare_time(start, end)

    @RequirePerm(Permission.All)
    def isTimeReconnect(self):
        """Checks if pyload will try to make a reconnect

        :return: bool
        """
        start = self.core.config['reconnect']['startTime'].split(":")
        end = self.core.config['reconnect']['endTime'].split(":")
        return compare_time(start, end) and self.core.config["reconnect"]["activated"]


if Api.extend(CoreApi):
    del CoreApi
