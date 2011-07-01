#!/usr/bin/env python
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

    @author: RaNaN
"""

from base64 import standard_b64encode
from os.path import join
from time import time

from remote.thriftbackend.thriftgen.pyload.ttypes import *
from remote.thriftbackend.thriftgen.pyload.Pyload import Iface

from module.PyFile import PyFile
from module.database.UserDatabase import ROLE
from module.utils import freeSpace, compare_time


class Api(Iface):
    """
    **pyLoads API**

    This is accessible either internal via core.api or via thrift backend.

    see Thrift specification file remote/thriftbackend/pyload.thrift\
    for information about data structures and what methods are usuable with rpc.
    """

    def __init__(self, core):
        self.core = core

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
                item.value = str(data["value"]) if type(data["value"]) != basestring else data["value"]
                item.type = data["type"]
                items.append(item)
            section.items = items
            sections.append(section)
        return sections

    def getConfigValue(self, category, option, section):
        """Retrieve config value.

        :param category: name of category, or plugin
        :param option: config option
        :param section: 'plugin' or 'core'
        :return: config value as string
        """
        if section == "core":
            return self.core.config[category][option]
        elif section == "plugin":
            return self.core.config.getPlugin(category, option)

    def setConfigValue(self, category, option, value, section):
        """Set new config value.

        :param category:
        :param option:
        :param value: new config value
        :param section: 'plugin' or 'core
        """
        if section == "core":
            self.core.config[category][option] = value

            if option in ("limit_speed", "max_speed"): #not so nice to update the limit
                self.core.requestFactory.updateBucket()

        elif section == "plugin":
            self.core.config.setPlugin(category, option, value)

    def getConfig(self):
        """Retrieves complete config of core.
        
        :return: list of `ConfigSection`
        """
        return self._convertConfigFormat(self.core.config.config)

    def getPluginConfig(self):
        """Retrieves complete config for all plugins.

        :return: list of `ConfigSection`
        """
        return self._convertConfigFormat(self.core.config.plugin)

    def pauseServer(self):
        """Pause server: Tt wont start any new downloads, but nothing gets aborted."""
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

    def statusServer(self):
        """Some general information about the current status of pyLoad.
        
        :return: `ServerStatus`
        """
        serverStatus = ServerStatus()
        serverStatus.pause = self.core.threadManager.pause
        serverStatus.active = len(self.core.threadManager.processingIds())
        serverStatus.queue = self.core.files.getFileCount() #TODO: real amount of queued files
        serverStatus.total = self.core.files.getFileCount()
        serverStatus.speed = 0
        for pyfile in [x.active for x in self.core.threadManager.threads if x.active and isinstance(x, PyFile)]:
            serverStatus.speed += pyfile.getSpeed() #bytes/s

        serverStatus.download = not self.core.threadManager.pause and self.isTimeDownload()
        serverStatus.reconnect = self.core.config['reconnect']['activated'] and self.isTimeReconnect()
        return serverStatus

    def freeSpace(self):
        return freeSpace(self.core.config["general"]["download_folder"])

    def getServerVersion(self):
        return self.core.version

    def kill(self):
        """Clean way to quit pyLoad"""
        self.core.do_kill = True

    def restart(self):
        """Untested"""
        self.core.do_restart = True

    def getLog(self, offset):
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

    def checkURL(self, urls):
        raise NotImplemented #TODO

    def isTimeDownload(self):
        """Checks if pyload will start new downloads according to time in config .

        :return: bool
        """
        start = self.core.config['downloadTime']['start'].split(":")
        end = self.core.config['downloadTime']['end'].split(":")
        return compare_time(start, end)

    def isTimeReconnect(self):
        """Checks if pyload will try to make a reconnect

        :return: bool
        """
        start = self.core.config['reconnect']['startTime'].split(":")
        end = self.core.config['reconnect']['endTime'].split(":")
        return compare_time(start, end) and self.core.config["reconnect"]["activated"]

    def statusDownloads(self):
        """ Status off all currently running downloads.

        :return: list of `DownloadStatus`
        """
        data = []
        for pyfile in [x.active for x in self.core.threadManager.threads + self.core.threadManager.localThreads if
                       x.active]:
            if not isinstance(pyfile, PyFile) or not pyfile.hasPlugin():
                continue

            data.append(DownloadInfo(
                pyfile.id, pyfile.name, pyfile.getSpeed(), pyfile.getETA(), pyfile.formatETA(),
                pyfile.getBytesLeft(), pyfile.getSize(), pyfile.formatSize(), pyfile.getPercent(),
                pyfile.status, pyfile.m.statusMsg[pyfile.status], pyfile.formatWait(),
                pyfile.waitUntil, pyfile.packageid, pyfile.package().name, pyfile.pluginname))

        return data

    def addPackage(self, name, links, dest):
        """Adds a package, with links to desired destination.

        :param name: name of the new package
        :param links: list of urls
        :param dest: `Destination`
        :return: package id of the new package
        """
        if self.core.config['general']['folder_per_package']:
            folder = name
        else:
            folder = ""

        folder = folder.replace("http://", "").replace(":", "").replace("/", "_").replace("\\", "_")

        pid = self.core.files.addPackage(name, folder, dest)

        self.core.files.addLinks(links, pid)

        self.core.log.info(_("Added package %(name)s containing %(count)d links") % {"name": name, "count": len(links)})

        self.core.files.save()

        return pid

    def getPackageData(self, pid):
        """Returns complete information about package, and included files.

        :param pid: package id
        :return: `PackageData` with .links attribute
        """
        data = self.core.files.getPackageData(int(pid))
        if not data:
            raise PackageDoesNotExists(pid)

        pdata = PackageData(data["id"], data["name"], data["folder"], data["site"], data["password"],
                            data["queue"], data["order"], data["priority"],
                            links=[self._convertPyFile(x) for x in data["links"].itervalues()])

        return pdata

    def getPackageInfo(self, pid):
        """Returns information about package, without detailed information about containing files

        :param pid: package id
        :return: `PackageData` with .fid attribute
        """
        data = self.core.files.getPackageData(int(pid))
        if not data:
            raise PackageDoesNotExists(pid)

        pdata = PackageData(data["id"], data["name"], data["folder"], data["site"], data["password"],
                            data["queue"], data["order"], data["priority"], fids=[int(x) for x in data["links"]])

        return pdata

    def getFileData(self, fid):
        """Get complete information about a specific file.

        :param fid: file id
        :return: `FileData`
        """
        info = self.core.files.getFileData(int(fid))
        fdata = self._convertPyFile(info.values()[0])
        return fdata

    def deleteFiles(self, fids):
        """Deletes several file entries from pyload.
        
        :param fids: list of file ids
        """
        for id in fids:
            self.core.files.deleteLink(int(id))

        self.core.files.save()

    def deletePackages(self, pids):
        """Deletes packages and containing links.

        :param pids: list of package ids
        """
        for id in pids:
            self.core.files.deletePackage(int(id))

        self.core.files.save()

    def getQueue(self):
        """Returns info about queue and packages, **not** about files, see `getQueueData` \
        or `getPackageData` instead.

        :return: list of `PackageInfo`
        """
        return [PackageData(pack["id"], pack["name"], pack["folder"], pack["site"],
                            pack["password"], pack["queue"], pack["order"], pack["priority"],
                            fids=[int(x) for x in pack["links"]])
                for pack in self.core.files.getInfoData(Destination.Queue).itervalues()]

    def getQueueData(self):
        """Return complete data about everything in queue, this is very expensive use it sparely.\
           See `getQueue` for alternative.

        :return: list of `PackageData`
        """
        return [PackageData(pack["id"], pack["name"], pack["folder"], pack["site"],
                            pack["password"], pack["queue"], pack["order"], pack["priority"],
                            links=[self._convertPyFile(x) for x in pack["links"].itervalues()])
                for pack in self.core.files.getCompleteData(Destination.Queue).itervalues()]

    def getCollector(self):
        """same as `getQueue` for collector.

        :return: list of `PackageInfo`
        """
        return [PackageData(pack["id"], pack["name"], pack["folder"], pack["site"],
                            pack["password"], pack["queue"], pack["order"], pack["priority"],
                            fids=[int(x) for x in pack["links"]])
                for pack in self.core.files.getInfoData(Destination.Collector).itervalues()]

    def getCollectorData(self):
        """same as `getQueueData` for collector.

        :return: list of `PackageInfo`
        """
        return [PackageData(pack["id"], pack["name"], pack["folder"], pack["site"],
                            pack["password"], pack["queue"], pack["order"], pack["priority"],
                            links=[self._convertPyFile(x) for x in pack["links"].itervalues()])
                for pack in self.core.files.getCompleteData(Destination.Collector).itervalues()]


    def addFiles(self, pid, links):
        """Adds files to specific package.
        
        :param pid: package id
        :param links: list of urls
        """
        self.core.files.addLinks(links, int(pid))

        self.core.log.info(_("Added %(count)d links to package #%(package)d ") % {"count": len(links), "package": pid})
        self.core.files.save()

    def pushToQueue(self, pid):
        """Moves package from Collector to Queue.

        :param pid: package id
        """
        self.core.files.setPackageLocation(pid, Destination.Queue)

    def pullFromQueue(self, pid):
        """Moves package from Queue to Collector.

        :param pid: package id
        """
        self.core.files.setPackageLocation(pid, Destination.Collector)

    def restartPackage(self, pid):
        """Restarts a package, resets every containing files.

        :param pid: package id
        """
        self.core.files.restartPackage(int(pid))

    def restartFile(self, fid):
        """Resets file status, so it will be downloaded again.

        :param fid:  file id
        """
        self.core.files.restartFile(int(fid))

    def recheckPackage(self, pid):
        """Proofes online status of all files in a package, also a default action when package is added.

        :param pid:
        :return:
        """
        self.core.files.reCheckPackage(int(pid))

    def stopAllDownloads(self):
        """Aborts all running downloads."""

        pyfiles = self.core.files.cache.values()
        for pyfile in pyfiles:
            pyfile.abortDownload()

    def stopDownloads(self, fids):
        """Aborts specific downloads.

        :param fids: list of file ids
        :return:
        """
        pyfiles = self.core.files.cache.values()

        for pyfile in pyfiles:
            if pyfile.id in fids:
                pyfile.abortDownload()

    def setPackageName(self, pid, name):
        """Renames a package.

        :param pid: package id
        :param name: new package name
        """
        pack = self.core.files.getPackage(pid)
        pack.name = name
        pack.sync()

    def movePackage(self, destination, pid):
        """Set a new package location.

        :param destination: `Destination`
        :param pid: package id
        """
        if destination not in (0, 1): return
        self.core.files.setPackageLocation(pid, destination)

    def uploadContainer(self, filename, data):
        """Uploads and adds a container file to pyLoad.

        :param filename: filename, extension is important so it can correctly decrypted
        :param data: file content
        """
        th = open(join(self.core.config["general"]["download_folder"], "tmp_" + filename), "wb")
        th.write(str(data))
        th.close()

        self.addPackage(th.name, [th.name], Destination.Queue)

    def setPriority(self, pid, priority):
        """Set a new priority, so a package will be downloaded before others.

        :param pid: package id
        :param priority:
        """
        p = self.core.files.getPackage(pid)
        p.setPriority(priority)

    def orderPackage(self, pid, position):
        """Gives a package a new position.

        :param pid: package id
        :param position: 
        """
        self.core.files.reorderPackage(pid, position)

    def orderFile(self, fid, position):
        """Gives a new position to a file within its package.

        :param fid: file id
        :param position:
        """
        self.core.files.reorderFile(fid, position)

    def setPackageData(self, pid, data):
        """Allows to modify several package attributes.

        :param pid: package id
        :param data: dict that maps attribute to desired value
        """
        p = self.core.files.getPackage(pid)
        if not p: raise PackageDoesNotExists(pid)

        for key, value in data.iteritems():
            if key == "id": continue
            setattr(p, key, value)

        p.sync()
        self.core.files.save()

    def deleteFinished(self):
        """Deletes all finished files and completly finished packages.

        :return: list of deleted package ids
        """
        deleted = self.core.files.deleteFinishedLinks()
        return deleted

    def restartFailed(self):
        """Restarts all failed failes."""
        self.core.files.restartFailed()

    def getPackageOrder(self, destination):
        """Returns information about package order.

        :param destination: `Destination`
        :return: dict mapping order to package id
        """

        packs = self.core.files.getInfoData(destination)
        order = {}

        for pid in packs:
            pack = self.core.files.getPackageData(int(pid))
            while pack["order"] in order.keys(): #just in case
                pack["order"] += 1
            order[pack["order"]] = pack["id"]
        return order

    def getFileOrder(self, pid):
        """Information about file order within package.

        :param pid:
        :return: dict mapping order to file id
        """
        rawData = self.core.files.getPackageData(int(pid))
        order = {}
        for id, pyfile in rawData["links"].iteritems():
            while pyfile["order"] in order.keys(): #just in case
                pyfile["order"] += 1
            order[pyfile["order"]] = pyfile["id"]
        return order


    def isCaptchaWaiting(self):
        """Indicates wether a captcha task is available

        :return: bool
        """
        self.core.lastClientConnected = time()
        task = self.core.captchaManager.getTask()
        return not task is None

    def getCaptchaTask(self, exclusive):
        """Returns a captcha task

        :param exclusive: unused
        :return: `CaptchaTask`
        """
        self.core.lastClientConnected = time()
        task = self.core.captchaManager.getTask()
        if task:
            task.setWatingForUser(exclusive=exclusive)
            data, type, result = task.getCaptcha()
            t = CaptchaTask(int(task.tid), standard_b64encode(data), type, result)
            return t
        else:
            return CaptchaTask()

    def getCaptchaTaskStatus(self, tid):
        """Get information about captcha task

        :param tid: task id
        :return: string
        """
        self.core.lastClientConnected = time()
        t = self.core.captchaManager.getTaskByID(tid)
        return t.getStatus() if t else ""

    def setCaptchaResult(self, tid, result):
        """Set result for a captcha task

        :param tid: task id
        :param result: captcha result
        """
        self.core.lastClientConnected = time()
        task = self.core.captchaManager.getTaskByID(tid)
        if task:
            task.setResult(result)
            self.core.captchaManager.removeTask(task)


    def getEvents(self, uuid):
        """Lists occured events, may be affected to changes in future.

        :param uuid:
        :return: list of `Events`
        """
        events = self.core.pullManager.getEvents(uuid)
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

    def getAccounts(self, refresh):
        """Get information about all entered accounts.

        :param refresh: reload account info
        :return: list of `AccountInfo`
        """
        accs = self.core.accountManager.getAccountInfos(False, refresh)
        accounts = []
        for group in accs.values():
            accounts.extend([AccountInfo(acc["validuntil"], acc["login"], acc["options"], acc["valid"],
                                         acc["trafficleft"], acc["maxtraffic"], acc["premium"], acc["type"])
                             for acc in group])
        return accounts

    def getAccountTypes(self):
        """All available account types.

        :return: list
        """
        return self.core.accountManager.getAccountInfos(False, False).keys()

    def updateAccounts(self, data):
        """Changes pw/options for specific account.

        :param data: `AccountData`
        """
        self.core.accountManager.updateAccount(data.type, data.login, data.password, data.options)

    def removeAccount(self, plugin, account):
        """Remove account from pyload.

        :param plugin: pluginname
        :param account: accountname
        """
        self.core.accountManager.removeAccount(plugin, account)

    def login(self, username, password, remoteip=None):
        """Login into pyLoad, this **must** be called when using rpc before any methods can be used.

        :param username:
        :param password:
        :param remoteip:
        :return: bool indicating login was successful
        """
        if self.core.config["remote"]["nolocalauth"] and remoteip == "127.0.0.1":
            return True
        if self.core.startedInGui and remoteip == "127.0.0.1":
            return True

        user = self.core.db.checkAuth(username, password)
        if user and user["role"] == ROLE.ADMIN:
            return True

        return False

    def checkAuth(self, username, password):
        """Check authentication and returns details

        :param username:
        :param password:
        :return: dict with info, empty when login is incorrect
        """
        return self.core.db.checkAuth(username, password)

    def getUserData(self, username, password):
        """see `checkAuth`"""
        return self.checkAuth(username, password)


    def getServices(self):
        """ A dict of available services, these can be defined by hook plugins.

        :return: dict with this style: {"plugin": {"method": "description"}}
        """
        data = {}
        for plugin, funcs in self.core.hookManager.methods.iteritems():
            data[plugin] = funcs

        return data

    def hasService(self, plugin, func):
        """Checks wether a service is available.

        :param plugin:
        :param func:
        :return: bool
        """
        cont = self.core.hookManager.methods
        return cont.has_key(plugin) and cont[plugin].has_key(func)

    def call(self, info):
        """Calls a service (a method in hook plugin).

        :param info: `ServiceCall`
        :return: result
        :raises: ServiceDoesNotExists, when its not available
        :raises: ServiceException, when a exception was raised
        """
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