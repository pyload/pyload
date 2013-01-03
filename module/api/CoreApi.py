#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.Api import Api, RequirePerm, Permission, ServerStatus
from module.utils.fs import join, free_space
from module.utils import compare_time

from ApiComponent import ApiComponent

class CoreApi(ApiComponent):
    """ This module provides methods for general interaction with the core, like status or progress retrieval  """

    @RequirePerm(Permission.All)
    def getServerVersion(self):
        """pyLoad Core version """
        return self.core.version

    @RequirePerm(Permission.All)
    def getWSAddress(self):
        """Gets and address for the websocket based on configuration"""
        # TODO

    @RequirePerm(Permission.All)
    def getServerStatus(self):
        """Some general information about the current status of pyLoad.

        :return: `ServerStatus`
        """
        serverStatus = ServerStatus(self.core.files.getQueueCount(), self.core.files.getFileCount(), 0,
            not self.core.threadManager.pause and self.isTimeDownload(), self.core.threadManager.pause,
            self.core.config['reconnect']['activated'] and self.isTimeReconnect())

        for pyfile in self.core.threadManager.getActiveDownloads():
            serverStatus.speed += pyfile.getSpeed() #bytes/s

        return serverStatus

    @RequirePerm(Permission.All)
    def getProgressInfo(self):
        """ Status of all currently running tasks

        :rtype: list of :class:`ProgressInfo`
        """
        pass

    def pauseServer(self):
        """Pause server: It won't start any new downloads, but nothing gets aborted."""
        self.core.threadManager.pause = True

    def unpauseServer(self):
        """Unpause server: New Downloads will be started."""
        self.core.threadManager.pause = False

    def togglePause(self):
        """Toggle pause state.

        :return: new pause state
        """
        self.core.threadManager.pause ^= True
        return self.core.threadManager.pause

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