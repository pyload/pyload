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
    """ tests api randomly """

    def __init__(self, core):
        Thread.__init__(self)
        self.setDaemon(True)
        self.core = core
        self.methods = core.server_methods
        self.count = 0 #number of methods
        self.time = time()

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
        m = ["status_downloads", "status_server", "add_package", "get_package_data", "get_file_data", "del_links",
             "del_packages",
             "get_queue", "get_collector", "get_queue_info", "get_collector_info", "is_captcha_waiting"]

        method = choice(m)
        #print "Testing:", method

        if hasattr(self, method):
            res = getattr(self, method)()
        else:
            res = getattr(self.methods, method)()

        self.count += 1

        #print res

    def add_package(self):
        name = "".join(sample(string.ascii_letters, 10))
        urls = createURLs()

        self.methods.add_package(name, urls, 1)


    def del_links(self):
        info = self.methods.get_queue()
        if not info: return

        pid = choice(info.keys())
        pack = info[pid]
        links = pack["links"]
        #filter links which are not queued, finished or failed
        fids = filter(lambda x: links[x]["status"] not in AVOID, links.keys())

        if len(fids):
            fids = sample(fids, randint(1, max(len(fids) / 2, 1)))
            self.methods.del_links(fids)


    def del_packages(self):
        info = self.methods.get_queue_info()
        if not info: return

        pids = info.keys()
        if len(pids):
            pids = sample(pids, randint(1, max(len(pids) / 2, 1)))
            filtered = []

            for p in pids:
                info = self.methods.get_package_data(p)
                append = True
                for link in info["links"].itervalues():
                    if link["status"] not in AVOID:
                        append = False
                        break

                if append: filtered.append(p)

            self.methods.del_packages(filtered)

    def get_file_data(self):
        info = self.methods.get_queue()
        if info:
            p = info[choice(info.keys())]
            if p["links"]:
                self.methods.get_file_data(choice(p["links"].keys()))

    def get_package_data(self):
        info = self.methods.get_queue_info()
        if info:
            self.methods.get_package_data(choice(info.keys()))


class ThriftExerciser(APIExerciser):
    def __init__(self, core):
        self.thrift = ThriftClient()
        self.thrift.login("user", "pw")

        APIExerciser.__init__(self, core)

    def testAPI(self):
        m = ["statusDownloads", "statusServer", "addPackage", "getPackageData", "getFileData", "deleteFiles",
             "deletePackages",
             "getQueue", "getCollector", "getQueueData", "getCollectorData", "isCaptchaWaiting"]

        method = choice(m)
        #print "Testing:", method

        if hasattr(self, method):
            res = getattr(self, method)()
        else:
            res = getattr(self.thrift, method)()

        self.count += 1

        #print res

    def addPackage(self):
        name = "".join(sample(string.ascii_letters, 10))
        urls = createURLs()

        self.thrift.addPackage(name, urls, 0)


    def deleteFiles(self):
        info = self.thrift.getQueueData()
        if not info: return

        pack = choice(info)
        fids = pack.links

        if len(fids):
            fids = [f.fid for f in sample(fids, randint(1, max(len(fids) / 2, 1)))]
            self.thrift.deleteFiles(fids)


    def deletePackages(self):
        info = self.thrift.getQueue()
        if not info: return

        pids = [p.pid for p in info]
        if len(pids):
            pids = sample(pids, randint(1, max(len(pids) / 2, 1)))
            self.thrift.deletePackages(pids)

    def getFileData(self):
        info = self.thrift.getQueueData()
        if info:
            p = choice(info)
            if p.links:
                self.thrift.getFileData(choice(p.links).fid)

    def getPackageData(self):
        info = self.thrift.getQueue()
        if info:
            self.thrift.getPackageData(choice(info).pid)