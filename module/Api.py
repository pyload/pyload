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

from PyFile import PyFile
from utils import compare_time, to_string, bits_set
from utils.fs import free_space
from common.packagetools import parseNames
from network.RequestFactory import getURL

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
    LIST = 16 # see listed downloads
    MODIFY = 32 # moddify some attribute of downloads
    DOWNLOAD = 64  # can download from webinterface
    SETTINGS = 128 # can access settings
    ACCOUNTS = 256 # can access accounts
    LOGS = 512 # can see server logs
    INTERACTION = 1024 # can interact with plugins


class ROLE:
    ADMIN = 0  #admin has all permissions implicit
    USER = 1


def has_permission(userperms, perms):
    return bits_set(perms, userperms)


class Api(Iface):
    """
    **pyLoads API**

    This is accessible either internal via core.api, thrift backend or json api.

    see Thrift specification file remote/thriftbackend/pyload.thrift\
    for information about data structures and what methods are usable with rpc.

    Most methods requires specific permissions, please look at the source code if you need to know.\
    These can be configured via web interface.
    Admin user have all permissions, and are the only ones who can access the methods with no specific permission.
    """

    EXTERNAL = Iface  # let the json api know which methods are external

    def __init__(self, core):
        self.core = core

    ##########################
    #  Server Status
    ##########################

    @permission(PERMS.ALL)
    def getServerVersion(self):
        """pyLoad Core version """
        return self.core.version

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
    def pauseServer(self):
        """Pause server: It won't start any new downloads, but nothing gets aborted."""
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

    @permission(PERMS.STATUS)
    def freeSpace(self):
        """Available free space at download directory in bytes"""
        return free_space(self.core.config["general"]["download_folder"])


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


    def scanDownloadFolder(self):
        pass

    @permission(PERMS.STATUS)
    def getProgressInfo(self):
        """ Status of all currently running tasks

        :return: list of `ProgressInfo`
        """
        data = []
        for pyfile in self.core.threadManager.getActiveFiles():
            if not isinstance(pyfile, PyFile):
                continue

            data.append(ProgressInfo(
                pyfile.id, pyfile.name, pyfile.getSpeed(), pyfile.getETA(), pyfile.formatETA(),
                pyfile.getBytesLeft(), pyfile.getSize(), pyfile.formatSize(), pyfile.getPercent(),
                pyfile.status, pyfile.getStatusName(), pyfile.formatWait(),
                pyfile.waitUntil, pyfile.packageid, pyfile.package().name, pyfile.pluginname))

        return data

    ##########################
    #  Configuration
    ##########################

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
        return dict([(section, ConfigSection(section, data.name, data.description, data.long_desc, [
        ConfigItem(option, d.name, d.description, d.type, to_string(d.default), to_string(self.core.config.get(section, option))) for
        option, d in data.config.iteritems()])) for
                section, data in self.core.config.getBaseSections()])


    @permission(PERMS.SETTINGS)
    def getPluginConfig(self):
        """Retrieves complete config for all plugins.

        :return: list of `ConfigSection`
        """
        return dict([(section, ConfigSection(section,
            data.name, data.description, data.long_desc)) for
                section, data in self.core.config.getPluginSections()])

    @permission(PERMS.SETTINGS)
    def configureSection(self, section):
        data = self.core.config.config[section]
        sec = ConfigSection(section, data.name, data.description, data.long_desc)
        sec.items = [ConfigItem(option, d.name, d.description,
            d.type, to_string(d.default), to_string(self.core.config.get(section, option)))
                     for
                     option, d in data.config.iteritems()]

        #TODO: config handler

        return sec


    @permission(PERMS.SETTINGS)
    def setConfigHandler(self, plugin, iid, value):
        pass

    def getConfigRef(self):
        """Config instance, not for RPC"""
        return self.core.config

    ##########################
    #  Download Preparing
    ##########################

    @permission(PERMS.ADD)
    def parseURLs(self, html=None, url=None):
        """Parses html content or any arbitrary text for links and returns result of `checkURLs`

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
        """ Gets urls and returns pluginname mapped to list of matching urls.

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
        :return: initial set of data as :class:`OnlineCheck` instance containing the result id
        """
        data, crypter = self.core.pluginManager.parseUrls(urls)

        # initial result does not contain the crypter links
        tmp = [(url, (url, LinkStatus(url, pluginname, "unknown", 3, 0))) for url, pluginname in data]
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
        """ checks online status of urls and a submitted container file

        :param urls: list of urls
        :param container: container file name
        :param data: file content
        :return: :class:`OnlineCheck`
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
        :return: `OnlineCheck`, if rid is -1 then there is no more data available
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

    ##########################
    #  Adding/Deleting
    ##########################

    @permission(PERMS.ADD)
    def generateAndAddPackages(self, links, paused=False):
        """Generates and add packages

        :param links: list of urls
        :param paused: paused package
        :return: list of package ids
        """
        return [self.addPackageP(name, urls, "", paused) for name, urls
                in self.generatePackages(links).iteritems()]

    @permission(PERMS.ADD)
    def autoAddLinks(self, links):
        pass

    @permission(PERMS.ADD)
    def createPackage(self, name, folder, root, password="", site="", comment="", paused=False):
        """Create a new package.

        :param name: display name of the package
        :param folder: folder name or relative path, abs path are not allowed
        :param root: package id of root package, -1 for top level package
        :param password: single pw or list of passwords separated with new line
        :param site: arbitrary url to site for more information
        :param comment: arbitrary comment
        :param paused: No downloads will be started when True
        :return: pid of newly created package
        """

        if isabs(folder):
           folder = folder.replace("/", "_")

        folder = folder.replace("http://", "").replace(":", "").replace("\\", "_").replace("..", "")

        self.core.log.info(_("Added package %(name)s as folder %(folder)s") % {"name": name, "folder": folder})
        pid = self.core.files.addPackage(name, folder, root, password, site, comment, paused)

        return pid


    @permission(PERMS.ADD)
    def addPackage(self, name, links, password=""):
        """Convenient method to add a package to the top-level and for adding links.

        :return: package id
        """
        self.addPackageChild(name, links, password, -1, False)

    @permission(PERMS.ADD)
    def addPackageP(self, name, links, password, paused):
        """ Same as above with additional paused attribute. """
        self.addPackageChild(name, links, password, -1, paused)

    @permission(PERMS.ADD)
    def addPackageChild(self, name, links, password, root, paused):
       """Adds a package, with links to desired package.

       :param root: parents package id
       :return: package id of the new package
       """
       if self.core.config['general']['folder_per_package']:
           folder = name
       else:
           folder = ""

       pid = self.createPackage(name, folder, root, password)
       self.addLinks(pid, links)

       return pid

    @permission(PERMS.ADD)
    def addLinks(self, pid, links):
       """Adds links to specific package. Initiates online status fetching.

       :param pid: package id
       :param links: list of urls
       """
       hoster, crypter = self.core.pluginManager.parseUrls(links)

       if hoster:
           self.core.files.addLinks(hoster, pid)
           self.core.threadManager.createInfoThread(hoster, pid)

       self.core.threadManager.createDecryptThread(crypter, pid)

       self.core.log.info((_("Added %d links to package") + " #%d" % pid) % len(hoster))
       self.core.files.save()

    @permission(PERMS.ADD)
    def uploadContainer(self, filename, data):
       """Uploads and adds a container file to pyLoad.

       :param filename: filename, extension is important so it can correctly decrypted
       :param data: file content
       """
       th = open(join(self.core.config["general"]["download_folder"], "tmp_" + filename), "wb")
       th.write(str(data))
       th.close()

       return self.addPackage(th.name, [th.name])

    @permission(PERMS.DELETE)
    def deleteFiles(self, fids):
        """Deletes several file entries from pyload.

        :param fids: list of file ids
        """
        for fid in fids:
            self.core.files.deleteFile(fid)

        self.core.files.save()

    @permission(PERMS.DELETE)
    def deletePackages(self, pids):
        """Deletes packages and containing links.

        :param pids: list of package ids
        """
        for pid in pids:
            self.core.files.deletePackage(pid)

        self.core.files.save()

    ##########################
    #  Collector
    ##########################

    @permission(PERMS.LIST)
    def getCollector(self):
        pass

    @permission(PERMS.ADD)
    def addToCollector(self, links):
        pass

    @permission(PERMS.ADD)
    def addFromCollector(self, name, paused):
        pass

    @permission(PERMS.DELETE)
    def deleteCollPack(self, name):
        pass

    @permission(PERMS.DELETE)
    def deleteCollLink(self, url):
        pass

    @permission(PERMS.ADD)
    def renameCollPack(self, name, new_name):
        pass

    #############################
    #  File Information retrival
    #############################

    @permission(PERMS.LIST)
    def getAllFiles(self):
        """ same as `getFileTree` for toplevel root and full tree"""
        return self.getFileTree(-1, True)

    @permission(PERMS.LIST)
    def getAllUnfinishedFiles(self):
        """ same as `getUnfinishedFileTree for toplevel root and full tree"""
        return self.getUnfinishedFileTree(-1, True)

    @permission(PERMS.LIST)
    def getFileTree(self, pid, full):
        """ Retrieve data for specific package. full=True will retrieve all data available
            and can result in greater delays.

        :param pid: package id
        :param full: go down the complete tree or only the first layer
        :return: :class:`PackageView`
        """
        return self.core.files.getView(pid, full, False)

    @permission(PERMS.LIST)
    def getUnfinishedFileTree(self, pid, full):
        """ Same as `getFileTree` but only contains unfinished files.

        :param pid: package id
        :param full: go down the complete tree or only the first layer
        :return: :class:`PackageView`
        """
        return self.core.files.getView(pid, full, False)

    @permission(PERMS.LIST)
    def getPackageContent(self, pid):
        """  Only retrieve content of a specific package. see `getFileTree`"""
        return self.getFileTree(pid, False)

    @permission(PERMS.LIST)
    def getPackageInfo(self, pid):
        """Returns information about package, without detailed information about containing files

        :param pid: package id
        :raises PackageDoesNotExists:
        :return: :class:`PackageInfo`
        """
        info = self.core.files.getPackageInfo(pid)
        if not info:
            raise PackageDoesNotExists(pid)
        return info

    @permission(PERMS.LIST)
    def getFileInfo(self, fid):
        """ Info for specific file

        :param fid: file id
        :raises FileDoesNotExists:
        :return: :class:`FileInfo`

        """
        info = self.core.files.getFileInfo(fid)
        if not info:
            raise FileDoesNotExists(fid)
        return info

    @permission(PERMS.LIST)
    def findFiles(self, pattern):
        pass

    #############################
    #  Modify Downloads
    #############################

    @permission(PERMS.MODIFY)
    def restartPackage(self, pid):
        """Restarts a package, resets every containing files.

        :param pid: package id
        """
        self.core.files.restartPackage(pid)

    @permission(PERMS.MODIFY)
    def restartFile(self, fid):
        """Resets file status, so it will be downloaded again.

        :param fid: file id
        """
        self.core.files.restartFile(fid)

    @permission(PERMS.MODIFY)
    def recheckPackage(self, pid):
        """Check online status of all files in a package, also a default action when package is added. """
        self.core.files.reCheckPackage(pid)

    @permission(PERMS.MODIFY)
    def stopAllDownloads(self):
        """Aborts all running downloads."""

        pyfiles = self.core.files.cachedFiles()
        for pyfile in pyfiles:
            pyfile.abortDownload()

    @permission(PERMS.MODIFY)
    def stopDownloads(self, fids):
        """Aborts specific downloads.

        :param fids: list of file ids
        :return:
        """
        pyfiles = self.core.files.cachedFiles()
        for pyfile in pyfiles:
            if pyfile.id in fids:
                pyfile.abortDownload()

    @permission(PERMS.MODIFY)
    def restartFailed(self):
        """Restarts all failed failes."""
        self.core.files.restartFailed()

    #############################
    #  Modify Files/Packages
    #############################

    @permission(PERMS.MODIFY)
    def setFilePaused(self, fid, paused):
        pass

    @permission(PERMS.MODIFY)
    def setPackagePaused(self, pid, paused):
        pass

    @permission(PERMS.MODIFY)
    def setPackageFolder(self, pid, path):
        pass

    @permission(PERMS.MODIFY)
    def movePackage(self, pid, root):
        """ Set a new root for specific package. This will also moves the files on disk\
           and will only work when no file is currently downloading.

        :param pid: package id
        :param root: package id of new root
        :raises PackageDoesNotExists: When pid or root is missing
        :return: False if package can't be moved
        """
        return self.core.files.movePackage(pid, root)

    @permission(PERMS.MODIFY)
    def moveFiles(self, fids, pid):
        """Move multiple files to another package. This will move the files on disk and\
        only work when files are not downloading. All files needs to be continuous ordered
        in the current package.

        :param fids: list of file ids
        :param pid: destination package
        :return: False if files can't be moved
        """
        return self.core.files.moveFiles(fids, pid)

    @permission(PERMS.MODIFY)
    def orderPackage(self, pid, position):
        """Set new position for a package.

        :param pid: package id
        :param position: new position, 0 for very beginning
        """
        self.core.files.orderPackage(pid, position)

    @permission(PERMS.MODIFY)
    def orderFiles(self, fids, pid, position):
        """ Set a new position for a bunch of files within a package.
        All files have to be in the same package and must be **continuous**\
        in the package. That means no gaps between them.

        :param fids: list of file ids
        :param pid: package id of parent package
        :param position:  new position: 0 for very beginning
        """
        self.core.files.orderFiles(fids, pid, position)

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

    #############################
    #  User Interaction
    #############################

    @permission(PERMS.INTERACTION)
    def isInteractionWaiting(self, mode):
        """ Check if task is waiting.

        :param mode: binary or'ed output type
        :return: boolean
        """
        return self.core.interactionManager.isTaskWaiting(mode)

    @permission(PERMS.INTERACTION)
    def getInteractionTask(self, mode):
        """Retrieve task for specific mode.

        :param mode: binary or'ed output type
        :return: :class:`InteractionTask`
        """
        task = self.core.interactionManager.getTask(mode)
        return InteractionTask(-1) if  not task else task


    @permission(PERMS.INTERACTION)
    def setInteractionResult(self, iid, result):
        """Set Result for a interaction task. It will be immediately removed from task queue afterwards

        :param iid: interaction id
        :param result: result as string
        """
        task = self.core.interactionManager.getTaskByID(iid)
        if task:
            task.setResult(result)

    @permission(PERMS.INTERACTION)
    def getNotifications(self):
        """List of all available notifcations. They stay in queue for some time, client should\
           save which notifications it already has seen.

        :return: list of :class:`InteractionTask`
        """
        return self.core.interactionManager.getNotifications()

    @permission(PERMS.INTERACTION)
    def getAddonHandler(self):
        pass

    @permission(PERMS.INTERACTION)
    def callAddonHandler(self, plugin, func, pid_or_fid):
        pass

    @permission(PERMS.DOWNLOAD)
    def generateDownloadLink(self, fid, timeout):
        pass

    #############################
    #  Event Handling
    #############################

    @permission(PERMS.STATUS)
    def getEvents(self, uuid):
        """Lists occured events, may be affected to changes in future.

        :param uuid: self assigned string uuid which has to be unique
        :return: list of `Events`
        """
        # TODO
        pass

    #############################
    #  Account Methods
    #############################

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

    #############################
    #  Auth+User Information
    #############################

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

        self.core.log.info(_("User '%s' tried to log in") % username)

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

    def changePassword(self, user, oldpw, newpw):
        """ changes password for specific user """
        return self.core.db.changePassword(user, oldpw, newpw)

    def setUserPermission(self, user, permission, role):
        self.core.db.setPermission(user, permission)
        self.core.db.setRole(user, role)

    #############################
    #  RPC Plugin Methods
    #############################

    @permission(PERMS.INTERACTION)
    def getServices(self):
        """ A dict of available services, these can be defined by addon plugins.

        :return: dict with this style: {"plugin": {"method": "description"}}
        """
        data = {}
        for plugin, funcs in self.core.addonManager.methods.iteritems():
            data[plugin] = funcs

        return data

    @permission(PERMS.INTERACTION)
    def hasService(self, plugin, func):
        pass

    @permission(PERMS.INTERACTION)
    def call(self, plugin, func, arguments):
        """Calls a service (a method in addon plugin).

        :raises: ServiceDoesNotExists, when its not available
        :raises: ServiceException, when a exception was raised
        """
        if not self.hasService(plugin, func):
            raise ServiceDoesNotExists(plugin, func)

        try:
            ret = self.core.addonManager.callRPC(plugin, func, arguments)
            return to_string(ret)
        except Exception, e:
            raise ServiceException(e.message)

    @permission(PERMS.STATUS)
    def getAllInfo(self):
        """Returns all information stored by addon plugins. Values are always strings

        :return: {"plugin": {"name": value } }
        """
        return self.core.addonManager.getAllInfo()

    @permission(PERMS.STATUS)
    def getInfoByPlugin(self, plugin):
        """Returns information stored by a specific plugin.

        :param plugin: pluginname
        :return: dict of attr names mapped to value {"name": value}
        """
        return self.core.addonManager.getInfo(plugin)
