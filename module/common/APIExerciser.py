# -*- coding: utf-8 -*-

import string
from threading import Thread
from random import choice, random, sample, randint
from time import time, sleep

from traceback import print_exc, format_exc

from module.remote.thriftbackend.ThriftClient import ThriftClient

def createURLs():
    """ create some urls, some may fail """
    urls = []
    for x in range(0, randint(20, 100)):
        name = "DEBUG_API"
        if randint(0, 5) == 5:
            name = "" #this link will fail

        urls.append(name + "".join(sample(string.ascii_letters, randint(10, 20))))

    return urls

AVOID = (0,3,8)

class APIExerciser(Thread):
    def __init__(self, core, thrift=False):
        Thread.__init__(self)
        self.setDaemon(True)
        self.core = core
        self.count = 0 #number of methods
        self.time = time()

        if thrift:
            self.api = ThriftClient()
            self.api.login("user", "pw")
        else:
            self.api = core.api

        self.start()

    def run(self):
        out = open("error.log", "ab")
        #core errors are not logged of course
        out.write("\n" + "Starting\n")
        out.flush()

        while True:
            try:
                self.testAPI()
            except Exception:
                print_exc()
                out.write(format_exc() + 2 * "\n")
                out.flush()

            if not self.count % 100:
                print "Tested %s api calls" % self.count
            if not self.count % 1000:
                out.write("Tested %s api calls\n" % self.count)
                out.flush()


                #sleep(random() / 500)

    def testAPI(self):
        m = ["statusDownloads", "statusServer", "addPackage", "getPackageData", "getFileData", "deleteFiles",
             "deletePackages", "getQueue", "getCollector", "getQueueData", "getCollectorData", "isCaptchaWaiting"]

        method = choice(m)
        #print "Testing:", method

        if hasattr(self, method):
            res = getattr(self, method)()
        else:
            res = getattr(self.api, method)()

        self.count += 1

        #print res

    def addPackage(self):
        name = "".join(sample(string.ascii_letters, 10))
        urls = createURLs()

        self.api.addPackage(name, urls, 0)


    def deleteFiles(self):
        info = self.api.getQueueData()
        if not info: return

        pack = choice(info)
        fids = pack.links

        if len(fids):
            fids = [f.fid for f in sample(fids, randint(1, max(len(fids) / 2, 1)))]
            self.api.deleteFiles(fids)


    def deletePackages(self):
        info = self.api.getQueue()
        if not info: return

        pids = [p.pid for p in info]
        if len(pids):
            pids = sample(pids, randint(1, max(len(pids) / 2, 1)))
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