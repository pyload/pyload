# -*- coding: utf-8 -*-

import gc
import string
import time
import traceback
from builtins import range
from math import floor
from random import choice, randint, sample
from threading import Thread

from pyload.core.remote.thriftbackend.thriftClient import Destination, ThriftClient


def createURLs():
    """
    create some urls, some may fail.
    """
    urls = []
    for x in range(0, randint(20, 100)):
        name = "DEBUG_API"
        if randint(0, 5) == 5:
            name = ""  #: this link will fail

        urls.append(name + "".join(sample(string.ascii_letters, randint(10, 20))))

    return urls


AVOID = (0, 3, 8)

idPool = 0
sumCalled = 0


def startApiExerciser(core, n):
    for i in range(n):
        APIExerciser(core).start()


class APIExerciser(Thread):
    def __init__(self, core, thrift=False, user=None, pw=None):
        global idPool

        super()
        self.daemon = True
        self.pyload = core
        self.count = 0  #: number of methods
        self.time = time.time()

        if thrift:
            self.api = ThriftClient(user=user, password=pw)
        else:
            self.api = core.api

        self.id = idPool

        idPool += 1

        # self.start()

    def run(self):

        self.pyload.log.info("API Excerciser started {}".format(self.id))

        with open("error.log", mode="ab") as out:
            # core errors are not logged of course
            out.write("\n" + "Starting\n")
            out.flush()

            while True:
                try:
                    self.testAPI()
                except Exception:
                    self.pyload.log.error(
                        "Excerciser {} throw an execption".format(self.id)
                    )
                    traceback.print_exc()
                    out.write(traceback.format_exc() + 2 * "\n")
                    out.flush()

                if not self.count % 100:
                    self.pyload.log.info(
                        "Exerciser {} tested {} api calls".format(self.id, self.count)
                    )
                if not self.count % 1000:
                    out.flush()

                if not sumCalled % 1000:  #: not thread safe
                    self.pyload.log.info(
                        "Exercisers tested {} api calls".format(sumCalled)
                    )
                    persec = sumCalled // (time() - self.time)
                    self.pyload.log.info(
                        "Approx. {:.2f} calls per second.".format(persec)
                    )
                    self.pyload.log.info(
                        "Approx. {:.2f} ms per call.".format(1000 // persec)
                    )
                    self.pyload.log.info("Collected garbage: {}".format(gc.collect()))

                    # time.sleep(random() / 500)

    def testAPI(self):
        global sumCalled

        m = [
            "statusDownloads",
            "statusServer",
            "addPackage",
            "getPackageData",
            "getFileData",
            "deleteFiles",
            "deletePackages",
            "getQueue",
            "getCollector",
            "getQueueData",
            "getCollectorData",
            "isCaptchaWaiting",
            "getCaptchaTask",
            "stopAllDownloads",
            "getAllInfo",
            "getServices",
            "getAccounts",
            "getAllUserData",
        ]

        method = choice(m)
        # print("Testing:", method)

        if hasattr(self, method):
            res = getattr(self, method)()
        else:
            res = getattr(self.api, method)()

        self.count += 1
        sumCalled += 1

        # print(res)

    def addPackage(self):
        name = "".join(sample(string.ascii_letters, 10))
        urls = createURLs()

        self.api.addPackage(
            name, urls, choice([Destination.Queue, Destination.Collector])
        )

    def deleteFiles(self):
        info = self.api.getQueueData()
        if not info:
            return

        pack = choice(info)
        fids = pack.links

        if len(fids):
            fids = [f.fid for f in sample(fids, randint(1, max(len(fids) // 2, 1)))]
            self.api.deleteFiles(fids)

    def deletePackages(self):
        info = choice([self.api.getQueue(), self.api.getCollector()])
        if not info:
            return

        pids = [p.pid for p in info]
        if len(pids):
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
