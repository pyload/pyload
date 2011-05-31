# -*- coding: utf-8 -*-

from thriftgen.pyload.ttypes import *
from thriftgen.pyload.Pyload import Iface

from module.PyFile import PyFile
from module.utils import freeSpace

from base64 import standard_b64encode

class Handler(Iface):
    def __init__(self, backend):
        self.backend = backend
        self.core = backend.core
        self.serverMethods = self.core.server_methods


    def _convertPyFile(self, p):
        f = FileData(p["id"], p["url"], p["name"], p["plugin"], p["size"],
                     p["format_size"], p["status"], p["statusmsg"],
                     p["package"], p["error"], p["order"], p["progress"])
        return f

    def _convertConfigFormat(self, c):
        sections = []
        for sectionName, sub in c.iteritems():
            section = ConfigSection()
            section.name = sectionName
            section.description = sub["desc"]
            items = []
            for key, data in sub.iteritems():
                if key == "desc":
                    continue
                item = ConfigItem()
                item.name = key
                item.description = data["desc"]
                item.value = str(data["value"]) if type(data["value"]) not in (str, unicode) else data["value"]
                item.type = data["type"]
                items.append(item)
            section.items = items
            sections.append(section)
        return sections

    #general
    def getConfigValue(self, category, option, section):
        """
        Parameters:
         - category
         - option
         - section
        """
        self.serverMethods.get_conf_val(category, option, section)

    def setConfigValue(self, category, option, value, section):
        """
        Parameters:
         - category
         - option
         - value
         - section
        """
        self.serverMethods.set_conf_val(category, option, value, section)

    def getConfig(self):
        c = self.serverMethods.get_config()
        return self._convertConfigFormat(c)

    def getPluginConfig(self):
        c = self.serverMethods.get_plugin_config()
        return self._convertConfigFormat(c)

    def pauseServer(self):
        self.serverMethods.pause_server()

    def unpauseServer(self):
        self.serverMethods.unpause_server()

    def togglePause(self):
        return self.serverMethods.toggle_pause()

    def toggleReconnect(self):
        return self.serverMethods.toggle_reconnect()

    def statusServer(self):
        status = self.serverMethods.status_server()
        serverStatus = ServerStatus()
        serverStatus.pause = status["pause"]
        serverStatus.active = status["activ"]
        serverStatus.queue = status["queue"]
        serverStatus.total = status["total"]
        serverStatus.speed = 0
        for pyfile in [x.active for x in self.core.threadManager.threads if x.active and x.active != "quit"]:
            serverStatus.speed += pyfile.getSpeed() #bytes/s
        serverStatus.download = status["download"]
        serverStatus.reconnect = status["reconnect"]
        return serverStatus

    def freeSpace(self):
        return freeSpace(self.core.config["general"]["download_folder"])

    def getServerVersion(self):
        return self.serverMethods.get_server_version()

    def kill(self):
        self.serverMethods.kill()

    def restart(self):
        self.serverMethods.restart()

    def getLog(self, offset):
        """
        Parameters:
         - offset
        """
        log = self.serverMethods.get_log(offset)
        return log or []

    def checkURL(self, urls):
        """
        Parameters:
         - urls
        """
        checked = {}
        for u, p in self.core.pluginManager.parseUrls(urls):
            if p == "BasePlugin":
                checked[u] = ""
            else:
                checked[u] = p
        return checked

    def isTimeDownload(self):
        return self.serverMethods.is_time_download()

    def isTimeReconnect(self):
        return self.serverMethods.is_time_reconnect()

    #downloads
    def statusDownloads(self):
        data = []
        for pyfile in [x.active for x in self.core.threadManager.threads + self.core.threadManager.localThreads if
                       x.active and x.active != "quit"]:
            if not isinstance(pyfile, PyFile):
                continue
            status = DownloadInfo()
            status.fid = pyfile.id
            status.name = pyfile.name
            status.speed = pyfile.getSpeed() #bytes
            status.eta = pyfile.getETA()
            status.format_eta = pyfile.formatETA()
            status.kbleft = pyfile.getBytesLeft() #holded for backward comp.
            status.bleft = pyfile.getBytesLeft()
            status.size = pyfile.getSize()
            status.format_size = pyfile.formatSize()
            status.percent = pyfile.getPercent()
            status.status = pyfile.status
            status.statusmsg = pyfile.m.statusMsg[pyfile.status]
            status.format_wait = pyfile.formatWait()
            status.wait_until = pyfile.waitUntil
            status.package = pyfile.package().name
            status.packageID = pyfile.package().id
            data.append(status)
        return data

    def addPackage(self, name, links, dest):
        """
        Parameters:
         - name
         - links
         - dest
        """
        return self.serverMethods.add_package(name, links, 0 if dest == Destination.Collector else 1)

    def getPackageData(self, pid):
        """
        Parameters:
         - pid
        """
        pdata = PackageData()
        rawData = self.serverMethods.get_package_data(pid)

        if not rawData:
            raise PackageDoesNotExists(pid)

        pdata.pid = rawData["id"]
        pdata.name = rawData["name"]
        pdata.folder = rawData["folder"]
        pdata.site = rawData["site"]
        pdata.password = rawData["password"]
        pdata.dest = rawData["queue"]
        pdata.order = rawData["order"]
        pdata.priority = rawData["priority"]
        pdata.links = []
        for id, pyfile in rawData["links"].iteritems():
            pdata.links.append(self._convertPyFile(pyfile))
            
        return pdata

    def getFileData(self, fid):
        """
        Parameters:
         - fid
        """
        rawData = self.serverMethods.get_file_data(fid)
        if rawData:
            rawData = rawData.values()[0]
        else:
            raise FileDoesNotExists(fid)

        fdata = self._convertPyFile(rawData)
        return fdata

    def deleteFiles(self, fids):
        """
        Parameters:
         - fids
        """
        self.serverMethods.del_links(fids)

    def deletePackages(self, pids):
        """
        Parameters:
         - pids
        """
        self.serverMethods.del_packages(pids)

    def getQueue(self):
        packs = self.serverMethods.get_queue()
        ret = []
        for pid, pack in packs.iteritems():
            pdata = PackageInfo()
            pdata.pid = pack["id"]
            pdata.name = pack["name"]
            pdata.folder = pack["folder"]
            pdata.site = pack["site"]
            pdata.password = pack["password"]
            pdata.dest = pack["queue"]
            pdata.order = pack["order"]
            pdata.priority = pack["priority"]
            pdata.links = [int(x) for x in pack["links"].keys()]
            ret.append(pdata)
        return ret

    def getQueueData(self):
        packs = self.serverMethods.get_queue()
        ret = []
        for pid, pack in packs.iteritems():
            pdata = PackageData()
            pdata.pid = pack["id"]
            pdata.name = pack["name"]
            pdata.folder = pack["folder"]
            pdata.site = pack["site"]
            pdata.password = pack["password"]
            pdata.dest = pack["queue"]
            pdata.order = pack["order"]
            pdata.priority = pack["priority"]
            pdata.links = [self._convertPyFile(x) for x in pack["links"].values()]
            ret.append(pdata)
        return ret

    def getCollector(self):
        packs = self.serverMethods.get_collector()
        ret = []
        for pid, pack in packs.iteritems():
            pdata = PackageInfo()
            pdata.pid = pack["id"]
            pdata.name = pack["name"]
            pdata.folder = pack["folder"]
            pdata.site = pack["site"]
            pdata.password = pack["password"]
            pdata.dest = pack["queue"]
            pdata.order = pack["order"]
            pdata.priority = pack["priority"]
            pdata.links = [int(x) for x in pack["links"].keys()]
            ret.append(pdata)
        return ret

    def getCollectorData(self):
        packs = self.serverMethods.get_collector()
        ret = []
        for pid, pack in packs.iteritems():
            pdata = PackageData()
            pdata.pid = pack["id"]
            pdata.name = pack["name"]
            pdata.folder = pack["folder"]
            pdata.site = pack["site"]
            pdata.password = pack["password"]
            pdata.dest = pack["queue"]
            pdata.order = pack["order"]
            pdata.priority = pack["priority"]
            pdata.links = [self._convertPyFile(x) for x in pack["links"].values()]
            ret.append(pdata)
        return ret

    def addFiles(self, pid, links):
        """
        Parameters:
         - pid
         - links
        """
        self.serverMethods.add_files(pid, links)

    def pushToQueue(self, pid):
        """
        Parameters:
         - pid
        """
        self.serverMethods.push_package_to_queue(pid)

    def pullFromQueue(self, pid):
        """
        Parameters:
         - pid
        """
        self.serverMethods.pull_out_package(pid)

    def restartPackage(self, pid):
        """
        Parameters:
         - pid
        """
        self.serverMethods.restart_package(pid)

    def restartFile(self, fid):
        """
        Parameters:
         - fid
        """
        self.serverMethods.restart_file(fid)

    def recheckPackage(self, pid):
        """
        Parameters:
         - pid
        """
        self.serverMethods.recheck_package(pid)

    def stopAllDownloads(self):
        self.serverMethods.stop_downloads()

    def stopDownloads(self, fids):
        """
        Parameters:
         - fids
        """
        self.serverMethods.abort_files(fids)

    def setPackageName(self, pid, name):
        """
        Parameters:
         - pid
         - name
        """
        self.serverMethods.set_package_name(pid, name)

    def movePackage(self, destination, pid):
        """
        Parameters:
         - destination
         - pid
        """
        self.serverMethods.move_package(destination, pid)

    def uploadContainer(self, filename, data):
        """
        Parameters:
         - filename
         - data
        """
        self.serverMethods.upload_container(filename, data)

    def setPriority(self, pid, priority):
        """
        Parameters:
         - pid
         - priority
        """
        self.serverMethods.set_priority(pid, priority)

    def orderPackage(self, pid, position):
        """
        Parameters:
         - pid
         - position
        """
        self.serverMethods.order_package(pid, position)

    def orderFile(self, fid, position):
        """
        Parameters:
         - fid
         - position
        """
        self.serverMethods.order_file(fid, position)

    def setPackageData(self, pid, data):
        """
        Parameters:
         - pid
         - data
        """
        self.serverMethods.set_package_data(pid, data)

    def deleteFinished(self):
        self.serverMethods.delete_finished()

    def restartFailed(self):
        self.serverMethods.restart_failed()

    def getPackageOrder(self, destination):
        """
        Parameters:
         - destination
        """
        order = {}
        if destination == Destination.Queue:
            packs = self.serverMethods.get_queue()
        else:
            packs = self.serverMethods.get_collector()
        for pid in packs:
            pack = self.serverMethods.get_package_data(pid)
            while pack["order"] in order.keys(): #just in case
                pack["order"] += 1
            order[pack["order"]] = pack["id"]
        return order

    def getFileOrder(self, pid):
        """
        Parameters:
         - pid
        """
        rawData = self.serverMethods.get_package_data(pid)
        order = {}
        for id, pyfile in rawData["links"].iteritems():
            while pyfile["order"] in order.keys(): #just in case
                pyfile["order"] += 1
            order[pyfile["order"]] = pyfile["id"]
        return order

    #captcha
    def isCaptchaWaiting(self):
        return self.serverMethods.is_captcha_waiting()

    def getCaptchaTask(self, exclusive):
        """
        Parameters:
         - exclusive
        """
        tid, data, type, result = self.serverMethods.get_captcha_task(exclusive)
        t = CaptchaTask(int(tid), standard_b64encode(data), type, result)
        return t

    def getCaptchaTaskStatus(self, tid):
        """
        Parameters:
         - tid
        """
        return self.serverMethods.get_task_status(tid)

    def setCaptchaResult(self, tid, result):
        """
        Parameters:
         - tid
         - result
        """
        self.serverMethods.set_captcha_result(tid, result)

    #events
    def getEvents(self, uuid):
        events = self.serverMethods.get_events(uuid)
        newEvents = []
        def convDest(d):
            return Destination.Queue if d == "queue" else Destination.Collector
        for e in events:
            event = Event()
            event.event = e[0]
            if e[0] in ("update", "remove", "insert"):
                event.id = e[3]
                event.type = ElementType.Package if e[2] == "pack" else ElementType.File
                event.destination = convDest(e[1])
            elif e[0] == "order":
                if e[1]:
                    event.id = e[1]
                    event.type = ElementType.Package if e[2] == "pack" else ElementType.File
                    event.destination = convDest(e[3])
            elif e[0] == "reload":
                event.destination = convDest(e[1])
            newEvents.append(event)
        return newEvents

    #accounts
    def getAccounts(self, refresh):
        """
        Parameters:
         - refresh
        """
        accs = self.serverMethods.get_accounts(False, refresh)
        accounts = []
        for group in accs.values():
            for acc in group:
                account = AccountInfo()
                account.validuntil = acc["validuntil"]
                account.login = acc["login"]
                account.options = acc["options"]
                account.valid = acc["valid"]
                account.trafficleft = acc["trafficleft"]
                account.maxtraffic = acc["maxtraffic"]
                account.premium = acc["premium"]
                account.type = acc["type"]
                accounts.append(account)
        return accounts
    
    def getAccountTypes(self):
        return self.serverMethods.get_accounts().keys()

    def updateAccounts(self, data):
        """
        Parameters:
         - data
        """
        self.serverMethods.update_account(data.type, data.login, data.password, data.options)

    def removeAccount(self, plugin, account):
        """
        Parameters:
         - plugin
         - account
        """
        self.serverMethods.remove_account(plugin, account)

    #auth
    def login(self, username, password, remoteip=None):
        """
        Parameters:
         - username
         - password
        """
        return self.backend.checkAuth(username, password, remoteip)

    def getUserData(self, username, password):
        return self.serverMethods.checkAuth(username, password)


    def getServices(self):
        data = {}
        for plugin, funcs in self.core.hookManager.methods.iteritems():
            data[plugin] = ServiceInfo(funcs)

        return data

    def hasService(self, plugin, func):
        cont = self.core.hookManager.methods
        return cont.has_key(plugin) and cont[plugin].has_key(func)

    def call(self, info):
        plugin = info.plugin
        func = info.func
        args = info.arguments
        parse = info.parseArguments

        if not self.hasService(plugin, func):
            raise ServiceDoesNotExists(plugin, func)

        try:
            ret = self.core.hookManager.callRPC(plugin, func, args, parse)
            return str(ret)
        except Exception, e:
            raise ServiceException(e.message)
        