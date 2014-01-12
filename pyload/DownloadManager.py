#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#   Copyright(c) 2008-2014 pyLoad Team
#   http://www.pyload.org
#
#   This file is part of pyLoad.
#   pyLoad is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   Subjected to the terms and conditions in LICENSE
#
#   @author: RaNaN
###############################################################################

from threading import Event
from ReadWriteLock import ReadWriteLock

from utils import lock, read_lock, primary_uid
from threads.DownloadThread import DownloadThread
from threads.DecrypterThread import DecrypterThread

class DownloadManager:
    """ Schedules and manages download and decrypter jobs. """

    def __init__(self, core):
        self.core = core

        #: won't start download when true
        self.paused = True

        #: each thread is in exactly one category
        self.free = []
        #: a thread that in working must have a pyfile as active attribute
        self.working = []

        #: indicates when reconnect has occured
        self.reconnecting = Event()
        self.reconnecting.clear()

        self.lock = ReadWriteLock()

    @lock
    def done(self, thread):
        """ Switch thread from working to free state """
        self.working.remove(thread)
        self.free.append(thread)

    @read_lock
    def activeDownloads(self, user):
        """ retrieve pyfiles of running downloads  """
        uid = primary_uid(user)
        return [x.active for x in self.working if uid is None or x.active.owner == uid]

    def getProgressList(self, user):
        """ Progress of all running downloads """
        return [p.getProgressInfo() for p in self.activeDownloads(user)]

    def canDownload(self, user):
        """ check if a user is eligible to start a new download """

    def abort(self):
        """ Cancels all downloads """

    def work(self):
        """ main routine that does the periodical work """

