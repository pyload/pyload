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

import re
from base64 import standard_b64encode
from os.path import join, isabs
from time import time
from itertools import chain


from PyFile import PyFile
from utils import freeSpace, compare_time, to_string
from common.packagetools import parseNames
from network.RequestFactory import getURL
from remote import activated

if activated:
    try:
        from remote.thriftbackend.thriftgen.pyload.ttypes import *
        from remote.thriftbackend.thriftgen.pyload.Pyload import Iface

        BaseObject = TBase
    except ImportError:
        print "Thrift not imported"
        from remote.socketbackend.ttypes import *
else:
    from remote.socketbackend.ttypes import *

# contains function names mapped to their permissions
# unlisted functions are for admins only
permMap = {}

# decorator only called on init, never initialized, so has no effect on runtime
def permission(bits):
    class _Dec(object):
        def __new__(cls, func, *args, **kwargs):
            permMap[func.__name__] = bits
            return func

    return _Dec


urlmatcher = re.compile(r"((https?|ftps?|xdcc|sftp):((//)|(\\\\))+[\w\d:#@%/;$()~_?\+\-=\\\.&]*)", re.IGNORECASE)

class PERMS:
    ALL = 0  # requires no permission, but login
    ADD = 1  # can add packages
    DELETE = 2 # can delete packages
    STATUS = 4   # see and change server status
    LIST = 16 # see queue and collector
    MODIFY = 32 # moddify some attribute of downloads
    DOWNLOAD = 64  # can download from webinterface
    SETTINGS = 128 # can access settings
    ACCOUNTS = 256 # can access accounts
    LOGS = 512 # can see server logs


class ROLE:
    ADMIN = 0  #admin has all permissions implicit
    USER = 1


def has_permission(userperms, perms):
    # bytewise or perms before if needed
    return perms == (userperms & perms)


class Api(Iface):
    """
    **pyLoads API**

    This is accessible either internal via core.api or via thrift backend.

    see Thrift specification file remote/thriftbackend/pyload.thrift\
    for information about data structures and what methods are usuable with rpc.

    Most methods requires specific permissions, please look at the source code if you need to know.\
    These can be configured via webinterface.
    Admin user have all permissions, and are the only ones who can access the methods with no specific permission.
    """

    EXTERNAL = Iface  # let the json api know which methods are external

    def __init__(self, core):
        self.core = core

    def _convertPyFile(self, p):
        f = FileData(p["id"], p["url"], p["name"], p["plugin"], p["size"],
            p["format_size"], p["status"], p["statusmsg"],
            p["package"], p["error"], p["order"])
        return f

    @permission(PERMS.SETTINGS)
    def getConfigValue(self, section, option):
        """Retrieve config value.

        :param section: name of category, or plugin
        :param option: config option
        :return: config value as string
        """
        value = self.core.config.get(section, option)
        return to_string(value)

    @permission(PERMS.SETTINGS)
    def setConfigValue(self, section, option, value):
        """Set new config value.

        :param section:
        :param option:
        :param value: new config value
        """
        if option in ("limit_speed", "max_speed"): #not so nice to update the limit
            self.core.requestFactory.updateBucket()

        self.core.config.set(section, option, value)

    @permission(PERMS.SETTINGS)
    def getConfig(self):
        """Retrieves complete config of core.

        :return: list of `ConfigSection`
        """
        return [ConfigSection(section, data.name, data.description, data.long_desc, [
        ConfigItem(option, d.name, d.description, d.type, d.default, self.core.config.get(section, option)) for
        option, d in data.config.iteritems()]) for
                section, data in self.core.config.getBaseSectionns()]


    @permission(PERMS.SETTINGS)
    def getPluginConfig(self):
        """Retrieves complete config for all plugins.

        :return: list of `ConfigSection`
        """
        return [ConfigSection(section, data.name, data.description, data.long_desc) for
                section, data in self.core.config.getPluginSections()]

    def configureSection(self, section):
        data = self.core.config.config[section]
        sec = ConfigSection(section, data.name, data.description, data.long_desc)
        sec.items = [ConfigItem(option, d.name, d.description, d.type, d.default, self.core.config.get(section, option))
                     for
                     option, d in data.config.iteritems()]

        #TODO: config handler

        return sec

    def getConfigPointer(self):
        """Config instance, not for RPC"""
        return self.core.config

    @permission(PERMS.STATUS)
    def pauseServer(self):
        """Pause server: Tt wont start any new downloads, but nothing gets aborted."""
        self.core.threadManager.pause = True

    @permission(PERMS.STATUS)
    def unpauseServer(self):
        """Unpause server: New Downloads will be started."""
        self.core.threadManager.pause = False

    @permission(PERMS.STATUS)
    def togglePause(self):
        """Toggle pause state.

        :return: new pause state
        """
        self.core.threadManager.pause ^= True
        return self.core.threadManager.pause

    @permission(PERMS.STATUS)
    def toggleReconnect(self):
        """Toggle reconnect activation.

        :return: new reconnect state
        """
        self.core.config["reconnect"]["activated"] ^= True
        return self.core.config["reconnect"]["activated"]

    @permission(PERMS.LIST)
    def statusServer(self):
        """Some general information about the current status of pyLoad.

        :return: `ServerStatus`
        """
        serverStatus = ServerStatus(self.core.threadManager.pause, len(self.core.threadManager.processingIds()),
            self.core.files.getQueueCount(), self.core.files.getFileCount(), 0,
            not self.core.threadManager.pause and self.isTimeDownload(),
            self.core.config['reconnect']['activated'] and self.isTimeReconnect())

        for pyfile in [x.active for x in self.core.threadManager.threads if x.active and isinstance(x.active, PyFile)]:
            serverStatus.speed += pyfile.getSpeed() #bytes/s

        return serverStatus

    @permission(PERMS.STATUS)
    def freeSpace(self):
        """Available free space at download directory in bytes"""
        return freeSpace(self.core.config["general"]["download_folder"])

    @permission(PERMS.ALL)
    def getServerVersion(self):
        """pyLoad Core version """
        return self.core.version

    def kill(self):
        """Clean way to quit pyLoad"""
        self.core.do_kill = True

    def restart(self):
        """Restart pyload core"""
        self.core.do_restart = True

    @permission(PERMS.LOGS)
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

    @permission(PERMS.STATUS)
    def isTimeDownload(self):
        """Checks if pyload will start new downloads according to time in config.

        :return: bool
        """
        start = self.core.config['downloadTime']['start'].split(":")
        end = self.core.config['downloadTime']['end'].split(":")
        return compare_time(start, end)

    @permission(PERMS.STATUS)
    def isTimeReconnect(self):
        """Checks if pyload will try to make a reconnect

        :return: bool
        """
        start = self.core.config['reconnect']['startTime'].split(":")
        end = self.core.config['reconnect']['endTime'].split(":")
        return compare_time(start, end) and self.core.config["reconnect"]["activated"]

    @permission(PERMS.LIST)
    def statusDownloads(self):
        """ Status off all currently running downloads.

        :return: list of `DownloadStatus`
        """
        data = []
        for pyfile in self.core.threadManager.getActiveFiles():
            if not isinstance(pyfile, PyFile):
                continue

            data.append(DownloadInfo(
                pyfile.id, pyfile.name, pyfile.getSpeed(), pyfile.getETA(), pyfile.formatETA(),
                pyfile.getBytesLeft(), pyfile.getSize(), pyfile.formatSize(), pyfile.getPercent(),
                pyfile.status, pyfile.getStatusName(), pyfile.formatWait(),
                pyfile.waitUntil, pyfile.packageid, pyfile.package().name, pyfile.pluginname))

        return data

    @permission(PERMS.ADD)
    def addPackage(self, name, links, dest=Destination.Queue, password=""):
        """Adds a package, with links to desired destination.

        :param name: name of the new package
        :param links: list of urls
        :param dest: `Destination`
        :param password: password as string, can be empty
        :return: package id of the new package
        """
        if self.core.config['general']['folder_per_package']:
            folder = name
        else:
            folder = ""

        if isabs(folder):
            folder = folder.replace("/", "_")

        folder = folder.replace("http://", "").replace(":", "").replace("\\", "_").replace("..", "")

        self.core.log.info(_("Added package %(name)s containing %(count)d links") % {"name": name, "count": len(links)})
        pid = self.core.files.addPackage(name, folder, dest, password)
        self.addFiles(pid, links)

        return pid

    @permission(PERMS.ADD)
    def addFiles(self, pid, links):
        """Adds files to specific package.

        :param pid: package id
        :param links: list of urls
        """
        hoster, crypter = self.core.pluginManager.parseUrls(links)

        if hoster:
            self.core.files.addLinks(hoster, pid)

        self.core.threadManager.createInfoThread(hoster, pid)
        self.core.threadManager.createDecryptThread(crypter, pid)

        self.core.log.debug("Added %d links to package #%d " % (len(hoster), pid))
        self.core.files.save()

    @permission(PERMS.ADD)
    def parseURLs(self, html=None, url=None):
        """Parses html content or any arbitaty text for links and returns result of `checkURLs`

        :param html: html source
        :return:
        """
        urls = []

        if html:
            urls += [x[0] for x in urlmatcher.findall(html)]

        if url:
            page = getURL(url)
            urls += [x[0] for x in urlmatcher.findall(page)]

        # remove duplicates
        return self.checkURLs(set(urls))


    @permission(PERMS.ADD)
    def checkURLs(self, urls):
        """ Gets urls and returns pluginname mapped to list of matches urls.

        :param urls:
        :return: {plugin: urls}
        """
        data, crypter = self.core.pluginManager.parseUrls(urls)
        plugins = {}

        for url, plugin in chain(data, crypter):
            if plugin in plugins:
                plugins[plugin].append(url)
            else:
                plugins[plugin] = [url]

        return plugins

    @permission(PERMS.ADD)
    def checkOnlineStatus(self, urls):
        """ initiates online status check, will also decrypt files.

        :param urls:
        :return: initial set of data as `OnlineCheck` instance containing the result id
        """
        data, crypter = self.core.pluginManager.parseUrls(urls)

        # initial result does not contain the crypter links
        tmp = [(url, (url, OnlineStatus(url, pluginname, "unknown", 3, 0))) for url, pluginname in data]
        data = parseNames(tmp)
        result = {}

        for k, v in data.iteritems():
            for url, status in v:
                status.packagename = k
                result[url] = status

        data.update(crypter) # hoster and crypter will be processed
        rid = self.core.threadManager.createResultThread(data, False)

        return OnlineCheck(rid, result)

    @permission(PERMS.ADD)
    def checkOnlineStatusContainer(self, urls, container, data):
        """ checks online status of urls and a submited container file

        :param urls: list of urls
        :param container: container file name
        :param data: file content
        :return: online check
        """
        th = open(join(self.core.config["general"]["download_folder"], "tmp_" + container), "wb")
        th.write(str(data))
        th.close()
        urls.append(th.name)
        return self.checkOnlineStatus(urls)

    @permission(PERMS.ADD)
    def pollResults(self, rid):
        """ Polls the result available for ResultID

        :param rid: `ResultID`
        :return: `OnlineCheck`, if rid is -1 then no more data available
        """
        result = self.core.threadManager.getInfoResult(rid)

        if "ALL_INFO_FETCHED" in result:
            del result["ALL_INFO_FETCHED"]
            return OnlineCheck(-1, result)
        else:
            return OnlineCheck(rid, result)


    @permission(PERMS.ADD)
    def generatePackages(self, links):
        """ Parses links, generates packages names from urls

        :param links: list of urls
        :return: package names mapped to urls
        """
        result = parseNames((x, x) for x in links)
        return result

    @permission(PERMS.ADD)
    def generateAndAddPackages(self, links, dest=Destination.Queue):
        """Generates and add packages

        :param links: list of urls
        :param dest: `Destination`
        :return: list of package ids
        """
        return [self.addPackage(name, urls, dest) for name, urls
                in self.generatePackages(links).iteritems()]


    @permission(PERMS.LIST)
    def getPackageData(self, pid):
        """Returns complete information about package, and included files.

        :param pid: package id
        :return: `PackageData` with .links attribute
        """
        data = self.core.files.getPackageData(int(pid))

        if not data:
            raise PackageDoesNotExists(pid)

        pdata = PackageData(data["id"], data["name"], data["folder"], data["site"], data["password"],
            data["queue"], data["order"],
            links=[self._convertPyFile(x) for x in data["links"].itervalues()])

        return pdata

    @permission(PERMS.LIST)
    def getPackageInfo(self, pid):
        """Returns information about package, without detailed information about containing files

        :param pid: package id
        :return: `PackageData` with .fid attribute
        """
        data = self.core.files.getPackageData(int(pid))

        if not data:
            raise PackageDoesNotExists(pid)

        pdata = PackageData(data["id"], data["name"], data["folder"], data["site"], data["password"],
            data["queue"], data["order"],
            fids=[int(x) for x in data["links"]])

        return pdata

    @permission(PERMS.LIST)
    def getFileData(self, fid):
        """Get complete information about a specific file.

        :param fid: file id
        :return: `FileData`
        """
        info = self.core.files.getFileData(int(fid))
        if not info:
            raise FileDoesNotExists(fid)

        fdata = self._convertPyFile(info.values()[0])
        return fdata

    @permission(PERMS.DELETE)
    def deleteFiles(self, fids):
        """Deletes several file entries from pyload.

        :param fids: list of file ids
        """
        for id in fids:
            self.core.files.deleteLink(int(id))

        self.core.files.save()

    @permission(PERMS.DELETE)
    def deletePackages(self, pids):
        """Deletes packages and containing links.

        :param pids: list of package ids
        """
        for id in pids:
            self.core.files.deletePackage(int(id))

        self.core.files.save()

    @permission(PERMS.LIST)
    def getQueue(self):
        """Returns info about queue and packages, **not** about files, see `getQueueData` \
        or `getPackageData` instead.

        :return: list of `PackageInfo`
        """
        return [PackageData(pack["id"], pack["name"], pack["folder"], pack["site"],
            pack["password"], pack["queue"], pack["order"],
            pack["linksdone"], pack["sizedone"], pack["sizetotal"],
            pack["linkstotal"])
                for pack in self.core.files.getInfoData(Destination.Queue).itervalues()]

    @permission(PERMS.LIST)
    def getQueueData(self):
        """Return complete data about everything in queue, this is very expensive use it sparely.\
           See `getQueue` for alternative.

        :return: list of `PackageData`
        """
        return [PackageData(pack["id"], pack["name"], pack["folder"], pack["site"],
            pack["password"], pack["queue"], pack["order"],
            pack["linksdone"], pack["sizedone"], pack["sizetotal"],
            links=[self._convertPyFile(x) for x in pack["links"].itervalues()])
                for pack in self.core.files.getCompleteData(Destination.Queue).itervalues()]

    @permission(PERMS.LIST)
    def getCollector(self):
        """same as `getQueue` for collector.

        :return: list of `PackageInfo`
        """
        return [PackageData(pack["id"], pack["name"], pack["folder"], pack["site"],
            pack["password"], pack["queue"], pack["order"],
            pack["linksdone"], pack["sizedone"], pack["sizetotal"],
            pack["linkstotal"])
                for pack in self.core.files.getInfoData(Destination.Collector).itervalues()]

    @permission(PERMS.LIST)
    def getCollectorData(self):
        """same as `getQueueData` for collector.

        :return: list of `PackageInfo`
        """
        return [PackageData(pack["id"], pack["name"], pack["folder"], pack["site"],
            pack["password"], pack["queue"], pack["order"],
            pack["linksdone"], pack["sizedone"], pack["sizetotal"],
            links=[self._convertPyFile(x) for x in pack["links"].itervalues()])
                for pack in self.core.files.getCompleteData(Destination.Collector).itervalues()]

    @permission(PERMS.MODIFY)
    def pushToQueue(self, pid):
        """Moves package from Collector to Queue.

        :param pid: package id
        """
        self.core.files.setPackageLocation(pid, Destination.Queue)

    @permission(PERMS.MODIFY)
    def pullFromQueue(self, pid):
        """Moves package from Queue to Collector.

        :param pid: package id
        """
        self.core.files.setPackageLocation(pid, Destination.Collector)

    @permission(PERMS.MODIFY)
    def restartPackage(self, pid):
        """Restarts a package, resets every containing files.

        :param pid: package id
        """
        self.core.files.restartPackage(int(pid))

    @permission(PERMS.MODIFY)
    def restartFile(self, fid):
        """Resets file status, so it will be downloaded again.

        :param fid:  file id
        """
        self.core.files.restartFile(int(fid))

    @permission(PERMS.MODIFY)
    def recheckPackage(self, pid):
        """Proofes online status of all files in a package, also a default action when package is added.

        :param pid:
        :return:
        """
        self.core.files.reCheckPackage(int(pid))

    @permission(PERMS.MODIFY)
    def stopAllDownloads(self):
        """Aborts all running downloads."""

        pyfiles = self.core.files.cache.values()
        for pyfile in pyfiles:
            pyfile.abortDownload()

    @permission(PERMS.MODIFY)
    def stopDownloads(self, fids):
        """Aborts specific downloads.

        :param fids: list of file ids
        :return:
        """
        pyfiles = self.core.files.cache.values()

        for pyfile in pyfiles:
            if pyfile.id in fids:
                pyfile.abortDownload()

    @permission(PERMS.MODIFY)
    def setPackageName(self, pid, name):
        """Renames a package.

        :param pid: package id
        :param name: new package name
        """
        pack = self.core.files.getPackage(pid)
        pack.name = name
        pack.sync()

    @permission(PERMS.MODIFY)
    def movePackage(self, destination, pid):
        """Set a new package location.

        :param destination: `Destination`
        :param pid: package id
        """
        if destination not in (0, 1): return
        self.core.files.setPackageLocation(pid, destination)

    @permission(PERMS.MODIFY)
    def moveFiles(self, fids, pid):
        """Move multiple files to another package

        :param fids: list of file ids
        :param pid: destination package
        :return:
        """
        #TODO: implement
        pass


    @permission(PERMS.ADD)
    def uploadContainer(self, filename, data):
        """Uploads and adds a container file to pyLoad.

        :param filename: filename, extension is important so it can correctly decrypted
        :param data: file content
        """
        th = open(join(self.core.config["general"]["download_folder"], "tmp_" + filename), "wb")
        th.write(str(data))
        th.close()

        self.addPackage(th.name, [th.name])

    @permission(PERMS.MODIFY)
    def orderPackage(self, pid, position):
        """Gives a package a new position.

        :param pid: package id
        :param position: 
        """
        self.core.files.reorderPackage(pid, position)

    @permission(PERMS.MODIFY)
    def orderFile(self, fid, position):
        """Gives a new position to a file within its package.

        :param fid: file id
        :param position:
        """
        self.core.files.reorderFile(fid, position)

    @permission(PERMS.MODIFY)
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

    @permission(PERMS.DELETE)
    def deleteFinished(self):
        """Deletes all finished files and completly finished packages.

        :return: list of deleted package ids
        """
        return self.core.files.deleteFinishedLinks()

    @permission(PERMS.MODIFY)
    def restartFailed(self):
        """Restarts all failed failes."""
        self.core.files.restartFailed()

    @permission(PERMS.LIST)
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

    @permission(PERMS.LIST)
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


    @permission(PERMS.STATUS)
    def isCaptchaWaiting(self):
        """Indicates wether a captcha task is available

        :return: bool
        """
        self.core.lastClientConnected = time()
        task = self.core.captchaManager.getTask()
        return not task is None

    @permission(PERMS.STATUS)
    def getCaptchaTask(self, exclusive=False):
        """Returns a captcha task

        :param exclusive: unused
        :return: `CaptchaTask`
        """
        self.core.lastClientConnected = time()
        task = self.core.captchaManager.getTask()
        if task:
            task.setWatingForUser(exclusive=exclusive)
            data, type, result = task.getCaptcha()
            t = CaptchaTask(int(task.id), standard_b64encode(data), type, result)
            return t
        else:
            return CaptchaTask(-1)

    @permission(PERMS.STATUS)
    def getCaptchaTaskStatus(self, tid):
        """Get information about captcha task

        :param tid: task id
        :return: string
        """
        self.core.lastClientConnected = time()
        t = self.core.captchaManager.getTaskByID(tid)
        return t.getStatus() if t else ""

    @permission(PERMS.STATUS)
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


    @permission(PERMS.STATUS)
    def getEvents(self, uuid):
        """Lists occured events, may be affected to changes in future.

        :param uuid: self assigned string uuid which has to be unique
        :return: list of `Events`
        """
        # TODO
        pass

    @permission(PERMS.ACCOUNTS)
    def getAccounts(self, refresh):
        """Get information about all entered accounts.

        :param refresh: reload account info
        :return: list of `AccountInfo`
        """
        accs = self.core.accountManager.getAllAccounts(refresh)
        accounts = []
        for plugin in accs.itervalues():
            accounts.extend(plugin.values())

        return accounts

    @permission(PERMS.ALL)
    def getAccountTypes(self):
        """All available account types.

        :return: string list
        """
        return self.core.pluginManager.getPlugins("accounts").keys()

    @permission(PERMS.ACCOUNTS)
    def updateAccount(self, plugin, account, password=None, options={}):
        """Changes pw/options for specific account."""
        self.core.accountManager.updateAccount(plugin, account, password, options)

    @permission(PERMS.ACCOUNTS)
    def removeAccount(self, plugin, account):
        """Remove account from pyload.

        :param plugin: pluginname
        :param account: accountname
        """
        self.core.accountManager.removeAccount(plugin, account)

    @permission(PERMS.ALL)
    def login(self, username, password, remoteip=None):
        """Login into pyLoad, this **must** be called when using rpc before any methods can be used.

        :param username:
        :param password:
        :param remoteip: Omit this argument, its only used internal
        :return: bool indicating login was successful
        """
        return True if self.checkAuth(username, password, remoteip) else False

    def checkAuth(self, username, password, remoteip=None):
        """Check authentication and returns details

        :param username:
        :param password:
        :param remoteip: 
        :return: dict with info, empty when login is incorrect
        """
        if self.core.config["remote"]["nolocalauth"] and remoteip == "127.0.0.1":
            return "local"
        if self.core.startedInGui and remoteip == "127.0.0.1":
            return "local"

        return self.core.db.checkAuth(username, password)

    def isAuthorized(self, func, userdata):
        """checks if the user is authorized for specific method

        :param func: function name
        :param userdata: dictionary of user data
        :return: boolean
        """
        if userdata == "local" or userdata["role"] == ROLE.ADMIN:
            return True
        elif func in permMap and has_permission(userdata["permission"], permMap[func]):
            return True
        else:
            return False


    @permission(PERMS.ALL)
    def getUserData(self, username, password):
        """similar to `checkAuth` but returns UserData thrift type """
        user = self.checkAuth(username, password)
        if user:
            return UserData(user["name"], user["email"], user["role"], user["permission"], user["template"])

        raise UserDoesNotExists(username)


    def getAllUserData(self):
        """returns all known user and info"""
        res = {}
        for user, data in self.core.db.getAllUserData().iteritems():
            res[user] = UserData(user, data["email"], data["role"], data["permission"], data["template"])

        return res

    @permission(PERMS.STATUS)
    def getServices(self):
        """ A dict of available services, these can be defined by hook plugins.

        :return: dict with this style: {"plugin": {"method": "description"}}
        """
        data = {}
        for plugin, funcs in self.core.hookManager.methods.iteritems():
            data[plugin] = funcs

        return data

    @permission(PERMS.STATUS)
    def hasService(self, plugin, func):
        """Checks wether a service is available.

        :param plugin:
        :param func:
        :return: bool
        """
        cont = self.core.hookManager.methods
        return plugin in cont and func in cont[plugin]

    @permission(PERMS.STATUS)
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

        if not self.hasService(plugin, func):
            raise ServiceDoesNotExists(plugin, func)

        try:
            ret = self.core.hookManager.callRPC(plugin, func, args)
            return str(ret)
        except Exception, e:
            raise ServiceException(e.message)

    @permission(PERMS.STATUS)
    def getAllInfo(self):
        """Returns all information stored by hook plugins. Values are always strings

        :return: {"plugin": {"name": value } }
        """
        return self.core.hookManager.getAllInfo()

    @permission(PERMS.STATUS)
    def getInfoByPlugin(self, plugin):
        """Returns information stored by a specific plugin.

        :param plugin: pluginname
        :return: dict of attr names mapped to value {"name": value}
        """
        return self.core.hookManager.getInfo(plugin)

    def changePassword(self, user, oldpw, newpw):
        """ changes password for specific user """
        return self.core.db.changePassword(user, oldpw, newpw)

    def setUserPermission(self, user, permission, role):
        self.core.db.setPermission(user, permission)
        self.core.db.setRole(user, role)
