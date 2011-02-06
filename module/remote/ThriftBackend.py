# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: mkaay
"""
from module.remote.RemoteManager import BackendBase
from module.PyFile import PyFile

from module.remote.thriftgen.pyload import Pyload
from module.remote.thriftgen.pyload.ttypes import *

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

import threading
import logging

class Processor(Pyload.Processor):
    def __init__(self, *args, **kwargs):
        Pyload.Processor.__init__(self, *args, **kwargs)
        self.authenticated = {}
    
    def process(self, iprot, oprot):
        trans = oprot.trans
        if not self.authenticated.has_key(trans):
            self.authenticated[trans] = False
            oldclose = trans.close
            def wrap():
                del self.authenticated[trans]
                oldclose()
            trans.close = wrap
        authenticated = self.authenticated[trans]
        (name, type, seqid) = iprot.readMessageBegin()
        if name not in self._processMap or (not authenticated and not name == "login"):
            iprot.skip(Pyload.TType.STRUCT)
            iprot.readMessageEnd()
            x = Pyload.TApplicationException(Pyload.TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % (name))
            oprot.writeMessageBegin(name, Pyload.TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return
        elif not authenticated and name == "login":
            args = Pyload.login_args()
            args.read(iprot)
            iprot.readMessageEnd()
            result = Pyload.login_result()
            self.authenticated[trans] = self._handler.login(args.username, args.password)
            result.success = self.authenticated[trans]
            oprot.writeMessageBegin("login", Pyload.TMessageType.REPLY, seqid)
            result.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
        else:
            self._processMap[name](self, seqid, iprot, oprot)
        return True

class PyloadHandler:
    def __init__(self, backend):
        self.backend = backend
        self.core = backend.core
        self.serverMethods = self.core.server_methods
    
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
    
    def _convertConfigFormat(self, c):
        sections = []
        for sectionName, sub in c.iteritems():
            section = ConfigSection()
            section.name = sectionName
            section.decription = sub["desc"]
            items = []
            for key, data in sub.iteritems():
                if key == "desc":
                    continue
                item = ConfigItem()
                item.name = key
                item.decription = data["desc"]
                item.value = str(data["value"])
                if data["type"] == "str":
                    item.type = ConfigItemType.String
                elif data["type"] == "int":
                    item.type = ConfigItemType.Integer
                elif data["type"] == "bool":
                    item.type = ConfigItemType.Bool
                elif data["type"] == "password":
                    item.type = ConfigItemType.Password
                elif data["type"] == "ip":
                    item.type = ConfigItemType.IP
                elif data["type"] == "file":
                    item.type = ConfigItemType.File
                elif data["type"] == "folder":
                    item.type = ConfigItemType.Folder
                elif data["type"] == "time":
                    item.type = ConfigItemType.Time
                else:
                    item.type = ConfigItemType.Choice
                    item.choice = set([x.strip() for x in data["type"].split(";")])
                items.append(item)
            section.items = items
            sections.append(section)
        return sections
    
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
        return self.serverMethods.toggle_server()

    def statusServer(self):
        status = self.serverMethods.status_server()
        serverStatus = ServerStatus()
        serverStatus.pause = status["pause"]
        serverStatus.active = status["activ"]
        serverStatus.queue = status["queue"]
        serverStatus.total = status["total"]
        serverStatus.speed = status["speed"]
        serverStatus.download = status["download"]
        serverStatus.reconnect = status["reconnect"]
        return serverStatus

    def freeSpace(self):
        return self.serverMethods.free_space()

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
        return list(self.serverMethods.restart(offset))

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
        for pyfile in [x.active for x in self.core.threadManager.threads + self.core.threadManager.localThreads if x.active and x.active != "quit"]:
            if not isinstance(pyfile, PyFile):
                continue
            status = DownloadStatus()
            status.id = pyfile.id
            status.name = pyfile.name
            status.speed = pyfile.getSpeed()/1024
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
            data.append(status)
        return data

    def addPackage(self, name, links, dest):
        """
        Parameters:
         - name
         - links
         - dest
        """
        return self.serverMethods.add_package(name, links, dest)

    def getPackageData(self, pid):
        """
        Parameters:
         - pid
        """
        pdata = PackageData()
        rawData = self.serverMethods.get_package_data(pid)
        pdata.pid = rawData["id"]
        pdata.name = rawData["name"]
        pdata.folder = rawData["folder"]
        pdata.site = rawData["site"]
        pdata.password = rawData["password"]
        pdata.queue = rawData["queue"]
        pdata.order = rawData["order"]
        pdata.priority = rawData["priority"]
        pdata.links = []
        for pyfile in rawData["links"]:
            pdata.links.append(pyfile["id"])
        return pdata

    def getFileData(self, fid):
        """
        Parameters:
         - fid
        """
        fdata = FileData()
        rawData = self.serverMethods.get_file_data(pid)
        fdata.pid = rawData["id"]
        fdata.url = rawData["url"]
        fdata.name = rawData["name"]
        fdata.plugin = rawData["plugin"]
        fdata.size = rawData["size"]
        fdata.format_size = rawData["format_size"]
        fdata.status = rawData["status"]
        fdata.statusmsg = rawData["statusmsg"]
        fdata.package = rawData["package"]
        fdata.error = rawData["error"]
        fdata.order = rawData["order"]
        fdata.progress = rawData["progress"]
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
        for pid in packs:
            pack = self.serverMethods.get_package_data(pid)
            pdata = PackageData()
            pdata.pid = pack["id"]
            pdata.name = pack["name"]
            pdata.folder = pack["folder"]
            pdata.site = pack["site"]
            pdata.password = pack["password"]
            pdata.queue = pack["queue"]
            pdata.order = pack["order"]
            pdata.priority = pack["priority"]
            pdata.fileids = [int(x) for x in pack["links"].keys()]
            ret.append(pdata)
        return ret

    def getCollector(self):
        packs = self.serverMethods.get_queue()
        ret = []
        for pid in packs:
            pack = self.serverMethods.get_package_data(pid)
            pdata = PackageData()
            pdata.pid = pack["id"]
            pdata.name = pack["name"]
            pdata.folder = pack["folder"]
            pdata.site = pack["site"]
            pdata.password = pack["password"]
            pdata.queue = pack["queue"]
            pdata.order = pack["order"]
            pdata.priority = pack["priority"]
            pdata.fileids = [int(x) for x in pack["links"].keys()]
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
        packdata = {}
        packdata["id"] = data.pid
        packdata["name"] = data.name
        packdata["folder"] = data.folder
        packdata["site"] = data.site
        packdata["password"] = data.password
        packdata["queue"] = data.queue
        packdata["order"] = data.order
        packdata["priority"] = data.priority
        self.serverMethods.set_package_data(pid, packdata)

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
            order[pack["order"]] = pack["id"]
        return order

    def getFileOrder(self, pid):
        """
        Parameters:
         - pid
        """
        rawData = self.serverMethods.get_package_data(pid)
        order = {}
        for pyfile in rawData["links"]:
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
        t = CaptchaTask()
        t.tid, t.data, t.type = self.serverMethods.get_captcha_task(exclusive)
        return t

    def getCaptchaTaskStatus(self, tid):
        """
        Parameters:
         - tid
        """
        status = self.serverMethods.get_task_status(tid)
        if status == "init":
            return CaptchaStatus.Init
        elif status == "waiting":
            return CaptchaStatus.Waiting
        elif status == "user":
            return CaptchaStatus.User
        elif status == "shared-user":
            return CaptchaStatus.SharedUser
        elif status == "done":
            return CaptchaStatus.Done

    def setCaptchaResult(self, tid, result):
        """
        Parameters:
         - tid
         - result
        """
        self.serverMethods.set_captcha_result(tid, result)
    
    #events
    def getEvents(self):
        events = serverMethods.get_events()
        newEvents = []
        for e in events:
            e = Event()
            if e[0] in ("update", "remove", "insert"):
                event.id = e[3]
                event.type = ElementType.Package if e[2] == "pack" else ElementType.File
                event.destination = e[1]
            if e[0] == "update":
                event.event = EventType.Update
            elif e[0] == "remove":
                event.event = EventType.Remove
            elif e[0] == "insert":
                event.event = EventType.Insert
            elif e[0] == "reload":
                event.event = EventType.ReloadAll
                event.destination = e[1]
            elif e[0] == "account":
                event.event = EventType.ReloadAccounts
            elif e[0] == "config":
                event.event = EventType.ReloadConfig
            elif e[0] == "order":
                event.event = EventType.ReloadOrder
                if e[1]:
                    event.id = e[1]
                    event.type = ElementType.Package if e[2] == "pack" else ElementType.File
                    event.destination = e[3]
            newEvents.append(event)
        return newEvents
    
    #accounts
    def getAccounts(self):
        accs = self.serverMethods.get_accounts()
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
    def login(self, username, password):
        """
        Parameters:
         - username
         - password
        """
        return True if self.serverMethods.checkAuth(username, password) else False

    def getUserData(self):
        return self.serverMethods.checkAuth(username, password)

class ThriftBackend(BackendBase):
    def setup(self):
        handler = PyloadHandler(self)
        processor = Processor(handler)
        transport = TSocket.TServerSocket(9090)
        tfactory = TTransport.TBufferedTransportFactory()
        pfactory = TBinaryProtocol.TBinaryProtocolFactory()
        
        #self.server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)
        self.server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
        
        #server = TServer.TThreadPoolServer(processor, transport, tfactory, pfactory)
    
    def serve(self):
        self.server.serve()
