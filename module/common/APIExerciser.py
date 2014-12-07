# -*- coding: utf-8 -*-

import string
from threading import Thread
from random import choice, sample, randint
from time import time
from math import floor
import gc
from traceback import print_exc, format_exc

from module.remote.thriftbackend.ThriftClient import ThriftClient, Destination


def createURLs():
    """ create some urls, some may fail """
    urls = []
    for x in range(0, randint(20, 100)):
        name = "DEBUG_API"
        if randint(0, 5) == 5:
            name = ""  # this link will fail

        urls.append(name + "".join(sample(string.ascii_letters, randint(10, 20))))

    return urls


AVOID = (0, 3, 8)

idPool = 0
sumCalled = 0


def startApiExerciser(core, n):
    for _ in range(n):
        APIExerciser(core).start()


class APIExerciser(Thread):
    def __init__(self, core, thrift=False, user=None, pw=None):
        global idPool

        Thread.__init__(self)
        self.setDaemon(True)
        self.core = core
        self.count = 0  # number of methods
        self.time = time()

        self.api = ThriftClient(user=user, password=pw) if thrift else core.api

        self.id = idPool

        idPool += 1

        # self.start()

    def run(self):

        self.core.log.info("API Excerciser started %d" % self.id)

        out = open("error.log", "ab")
        # core errors are not logged of course
        out.write("\n" + "Starting\n")
        out.flush()

        while True:
            try:
                self.testAPI()
            except Exception:
                self.core.log.error("Excerciser %d throw an execption" % self.id)
                print_exc()
                out.write(format_exc() + 2 * "\n")
                out.flush()

            if not self.count % 100:
                self.core.log.info("Exerciser %d tested %d api calls" % (self.id, self.count))
            if not self.count % 1000:
                out.flush()

            if not sumCalled % 1000:  # not thread safe
                self.core.log.info("Exercisers tested %d api calls" % sumCalled)
                persec = sumCalled / (time() - self.time)
                self.core.log.info("Approx. %.2f calls per second." % persec)
                self.core.log.info("Approx. %.2f ms per call." % (1000 / persec))
                self.core.log.info("Collected garbage: %d" % gc.collect())
                # sleep(random() / 500)

    def testAPI(self):
        global sumCalled

        m = ["statusDownloads", "statusServer", "addPackage", "getPackageData", "getFileData", "deleteFiles",
             "deletePackages", "getQueue", "getCollector", "getQueueData", "getCollectorData", "isCaptchaWaiting",
             "getCaptchaTask", "stopAllDownloads", "getAllInfo", "getServices", "getAccounts", "getAllUserData"]

        method = choice(m)
        # print "Testing:", method

        if hasattr(self, method):
            res = getattr(self, method)()
        else:
            res = getattr(self.api, method)()

        self.count += 1
        sumCalled += 1

        # print res

    def addPackage(self):
        name = "".join(sample(string.ascii_letters, 10))
        urls = createURLs()

        self.api.addPackage(name, urls, choice([Destination.Queue, Destination.Collector]))

    def deleteFiles(self):
        info = self.api.getQueueData()
        if not info: return

        pack = choice(info)
        fids = pack.links

        if len(fids):
            fids = [f.fid for f in sample(fids, randint(1, max(len(fids) / 2, 1)))]
            self.api.deleteFiles(fids)

    def deletePackages(self):
        info = choice([self.api.getQueue(), self.api.getCollector()])
        if not info: return

        pids = [p.pid for p in info]
        if pids:
            pids = sample(pids, randint(1, max(floor(len(pids) / 2.5), 1)))
            self.api.deletePackages(pids)

    def getFileData(self):
        info = self.api.getQueueData()
        if info:
            p = choice(info)
            if p.links:
                self.api.getFileData(choice(p.links).fid)

    def getPackageData(self):
        info = self.api.getQueue()
        if info:
            self.api.getPackageData(choice(info).pid)

    def getAccounts(self):
        self.api.getAccounts(False)

    def getCaptchaTask(self):
        self.api.getCaptchaTask(False)
