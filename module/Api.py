#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#   Copyright(c) 2008-2012 pyLoad Team
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

import re
from os.path import join, isabs
from itertools import chain
from functools import partial
from new import code
from dis import opmap

from remote.ttypes import *

from utils import compare_time, to_string, bits_set, get_index
from utils.fs import free_space
from common.packagetools import parseNames
from network.RequestFactory import getURL

# contains function names mapped to their permissions
# unlisted functions are for admins only
perm_map = {}

# store which methods needs user context
user_context = {}

# decorator only called on init, never initialized, so has no effect on runtime
def RequirePerm(bits):
    class _Dec(object):
        def __new__(cls, func, *args, **kwargs):
            perm_map[func.__name__] = bits
            return func

    return _Dec

# we will byte-hacking the method to add user as keyword argument
class UserContext(object):
    """Decorator to mark methods that require a specific user"""

    def __new__(cls, f, *args, **kwargs):
        fc = f.func_code

        try:
            i = get_index(fc.co_names, "user")
        except ValueError: # functions does not uses user, so no need to modify
            return f

        user_context[f.__name__] = True
        new_names = tuple([x for x in fc.co_names if f != "user"])
        new_varnames = tuple([x for x in fc.co_varnames] + ["user"])
        new_code = fc.co_code

        # subtract 1 from higher LOAD_GLOBAL
        for x in range(i + 1, len(fc.co_names)):
            new_code = new_code.replace(chr(opmap['LOAD_GLOBAL']) + chr(x), chr(opmap['LOAD_GLOBAL']) + chr(x - 1))

        # load argument instead of global
        new_code = new_code.replace(chr(opmap['LOAD_GLOBAL']) + chr(i), chr(opmap['LOAD_FAST']) + chr(fc.co_argcount))

        new_fc = code(fc.co_argcount + 1, fc.co_nlocals + 1, fc.co_stacksize, fc.co_flags, new_code, fc.co_consts,
            new_names, new_varnames, fc.co_filename, fc.co_name, fc.co_firstlineno, fc.co_lnotab, fc.co_freevars,
            fc.co_cellvars)

        f.func_code = new_fc

        # None as default argument for user
        if f.func_defaults:
            f.func_defaults = tuple([x for x in f.func_defaults] + [None])
        else:
            f.func_defaults = (None,)

        return f

urlmatcher = re.compile(r"((https?|ftps?|xdcc|sftp):((//)|(\\\\))+[\w\d:#@%/;$()~_?\+\-=\\\.&]*)", re.IGNORECASE)


stateMap = {
    DownloadState.All: frozenset(getattr(DownloadStatus, x) for x in dir(DownloadStatus) if not x.startswith("_")),
    DownloadState.Finished : frozenset((DownloadStatus.Finished, DownloadStatus.Skipped)),
    DownloadState.Unfinished : None, # set below
    DownloadState.Failed : frozenset((DownloadStatus.Failed, DownloadStatus.TempOffline, DownloadStatus.Aborted)),
    DownloadState.Unmanaged: None, #TODO
}

stateMap[DownloadState.Unfinished] =  frozenset(stateMap[DownloadState.All].difference(stateMap[DownloadState.Finished]))

def state_string(state):
    return ",".join(str(x) for x in stateMap[state])

def has_permission(userPermission, Permission):
    return bits_set(Permission, userPermission)

from datatypes.User import User

class UserApi(object):
    """  Proxy object for api that provides all methods in user context """

    def __init__(self, api, user):
        self.api = api
        self._user = user

    def __getattr__(self, item):
        f = self.api.__getattribute__(item)
        if f.func_name in user_context:
            return partial(f, user=self._user)

        return f

    @property
    def user(self):
        return self._user

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
        self.user_apis = {}


    def withUserContext(self, uid):
        """ Returns a proxy version of the api, to call method in user context

        :param uid: user or userData instance or uid
        :return: :class:`UserApi`
        """
        if isinstance(uid, User):
            uid = uid.uid

        if uid not in self.user_apis:
            user = self.core.db.getUserData(uid=uid)
            if not user: #TODO: anonymous user?
                return None

            self.user_apis[uid] = UserApi(self, User.fromUserData(self, user))

        return self.user_apis[uid]

    ##########################
    #  Server Status
    ##########################

    @RequirePerm(Permission.All)
    def getServerVersion(self):
        """pyLoad Core version """
        return self.core.version

    @RequirePerm(Permission.All)
    def getWSAddress(self):
        """Gets and address for the websocket based on configuration"""
        # TODO

    @RequirePerm(Permission.All)
    def getServerStatus(self):
        """Some general information about the current status of pyLoad.

        :return: `ServerStatus`
        """
        serverStatus = ServerStatus(self.core.files.getQueueCount(), self.core.files.getFileCount(), 0,
            not self.core.threadManager.pause and self.isTimeDownload(), self.core.threadManager.pause,
            self.core.config['reconnect']['activated'] and self.isTimeReconnect())

        for pyfile in self.core.threadManager.getActiveDownloads():
            serverStatus.speed += pyfile.getSpeed() #bytes/s

        return serverStatus

    @RequirePerm(Permission.All)
    def getProgressInfo(self):
        """ Status of all currently running tasks

        :return: list of `ProgressInfo`
        """
        pass

    def pauseServer(self):
        """Pause server: It won't start any new downloads, but nothing gets aborted."""
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

    def freeSpace(self):
        """Available free space at download directory in bytes"""
        return free_space(self.core.config["general"]["download_folder"])


    def stop(self):
        """Clean way to quit pyLoad"""
        self.core.do_kill = True

    def restart(self):
        """Restart pyload core"""
        self.core.do_restart = True

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

    @RequirePerm(Permission.All)
    def isTimeDownload(self):
        """Checks if pyload will start new downloads according to time in config.

        :return: bool
        """
        start = self.core.config['downloadTime']['start'].split(":")
        end = self.core.config['downloadTime']['end'].split(":")
        return compare_time(start, end)

    @RequirePerm(Permission.All)
    def isTimeReconnect(self):
        """Checks if pyload will try to make a reconnect

        :return: bool
        """
        start = self.core.config['reconnect']['startTime'].split(":")
        end = self.core.config['reconnect']['endTime'].split(":")
        return compare_time(start, end) and self.core.config["reconnect"]["activated"]

    ##########################
    #  Configuration
    ##########################

    def getConfigValue(self, section, option):
        """Retrieve config value.

        :param section: name of category, or plugin
        :param option: config option
        :return: config value as string
        """
        value = self.core.config.get(section, option)
        return to_string(value)

    def setConfigValue(self, section, option, value):
        """Set new config value.

        :param section:
        :param option:
        :param value: new config value
        """
        if option in ("limit_speed", "max_speed"): #not so nice to update the limit
            self.core.requestFactory.updateBucket()

        self.core.config.set(section, option, value)

    def getConfig(self):
        """Retrieves complete config of core.

        :return: map of `ConfigHolder`
        """
        # TODO
        return dict([(section, ConfigHolder(section, data.name, data.description, data.long_desc, [
        ConfigItem(option, d.name, d.description, d.type, to_string(d.default),
            to_string(self.core.config.get(section, option))) for
        option, d in data.config.iteritems()])) for
                                                section, data in self.core.config.getBaseSections()])


    def getConfigRef(self):
        """Config instance, not for RPC"""
        return self.core.config

    def getGlobalPlugins(self):
        """All global plugins/addons, only admin can use this

        :return: list of `ConfigInfo`
        """
        pass

    @UserContext
    @RequirePerm(Permission.Plugins)
    def getUserPlugins(self):
        """List of plugins every user can configure for himself

        :return: list of `ConfigInfo`
        """
        pass

    @UserContext
    @RequirePerm(Permission.Plugins)
    def configurePlugin(self, plugin):
        """Get complete config options for an plugin

        :param plugin: Name of the plugin to configure
        :return: :class:`ConfigHolder`
        """

        pass

    @UserContext
    @RequirePerm(Permission.Plugins)
    def saveConfig(self, config):
        """Used to save a configuration, core config can only be saved by admins

        :param config: :class:`ConfigHolder
        """
        pass

    @UserContext
    @RequirePerm(Permission.Plugins)
    def deleteConfig(self, plugin):
        """Deletes modified config

        :param plugin: plugin name
        :return:
        """
        pass

    @RequirePerm(Permission.Plugins)
    def setConfigHandler(self, plugin, iid, value):
        pass

    ##########################
    #  Download Preparing
    ##########################

    @RequirePerm(Permission.Add)
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


    @RequirePerm(Permission.Add)
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

    @RequirePerm(Permission.Add)
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

    @RequirePerm(Permission.Add)
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

    @RequirePerm(Permission.Add)
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


    @RequirePerm(Permission.Add)
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

    @RequirePerm(Permission.Add)
    def generateAndAddPackages(self, links, paused=False):
        """Generates and add packages

        :param links: list of urls
        :param paused: paused package
        :return: list of package ids
        """
        return [self.addPackageP(name, urls, "", paused) for name, urls
                in self.generatePackages(links).iteritems()]

    @RequirePerm(Permission.Add)
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


    @RequirePerm(Permission.Add)
    def addPackage(self, name, links, password=""):
        """Convenient method to add a package to the top-level and for adding links.

        :return: package id
        """
        return self.addPackageChild(name, links, password, -1, False)

    @RequirePerm(Permission.Add)
    def addPackageP(self, name, links, password, paused):
        """ Same as above with additional paused attribute. """
        return self.addPackageChild(name, links, password, -1, paused)

    @RequirePerm(Permission.Add)
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

    @RequirePerm(Permission.Add)
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

    @RequirePerm(Permission.Add)
    def uploadContainer(self, filename, data):
        """Uploads and adds a container file to pyLoad.

        :param filename: filename, extension is important so it can correctly decrypted
        :param data: file content
        """
        th = open(join(self.core.config["general"]["download_folder"], "tmp_" + filename), "wb")
        th.write(str(data))
        th.close()

        return self.addPackage(th.name, [th.name])

    @RequirePerm(Permission.Delete)
    def deleteFiles(self, fids):
        """Deletes several file entries from pyload.

        :param fids: list of file ids
        """
        for fid in fids:
            self.core.files.deleteFile(fid)

        self.core.files.save()

    @RequirePerm(Permission.Delete)
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

    @RequirePerm(Permission.All)
    def getCollector(self):
        pass

    @RequirePerm(Permission.Add)
    def addToCollector(self, links):
        pass

    @RequirePerm(Permission.Add)
    def addFromCollector(self, name, new_name):
        pass

    @RequirePerm(Permission.Delete)
    def deleteCollPack(self, name):
        pass

    @RequirePerm(Permission.Add)
    def renameCollPack(self, name, new_name):
        pass

    @RequirePerm(Permission.Delete)
    def deleteCollLink(self, url):
        pass

    #############################
    #  File Information retrieval
    #############################

    @RequirePerm(Permission.All)
    def getAllFiles(self):
        """ same as `getFileTree` for toplevel root and full tree"""
        return self.getFileTree(-1, True)

    @RequirePerm(Permission.All)
    def getFilteredFiles(self, state):
        """ same as `getFilteredFileTree` for toplevel root and full tree"""
        return self.getFilteredFileTree(-1, state, True)

    @RequirePerm(Permission.All)
    def getFileTree(self, pid, full):
        """ Retrieve data for specific package. full=True will retrieve all data available
            and can result in greater delays.

        :param pid: package id
        :param full: go down the complete tree or only the first layer
        :return: :class:`TreeCollection`
        """
        return self.core.files.getTree(pid, full, DownloadState.All)

    @RequirePerm(Permission.All)
    def getFilteredFileTree(self, pid, full, state):
        """ Same as `getFileTree` but only contains files with specific download state.

        :param pid: package id
        :param full: go down the complete tree or only the first layer
        :param state: :class:`DownloadState`, the attributes used for filtering
        :return: :class:`TreeCollection`
        """
        return self.core.files.getTree(pid, full, state)

    @RequirePerm(Permission.All)
    def getPackageContent(self, pid):
        """  Only retrieve content of a specific package. see `getFileTree`"""
        return self.getFileTree(pid, False)

    @RequirePerm(Permission.All)
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

    @RequirePerm(Permission.All)
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

    @RequirePerm(Permission.All)
    def findFiles(self, pattern):
        pass

    #############################
    #  Modify Downloads
    #############################

    @RequirePerm(Permission.Modify)
    def restartPackage(self, pid):
        """Restarts a package, resets every containing files.

        :param pid: package id
        """
        self.core.files.restartPackage(pid)

    @RequirePerm(Permission.Modify)
    def restartFile(self, fid):
        """Resets file status, so it will be downloaded again.

        :param fid: file id
        """
        self.core.files.restartFile(fid)

    @RequirePerm(Permission.Modify)
    def recheckPackage(self, pid):
        """Check online status of all files in a package, also a default action when package is added. """
        self.core.files.reCheckPackage(pid)

    @RequirePerm(Permission.Modify)
    def restartFailed(self):
        """Restarts all failed failes."""
        self.core.files.restartFailed()

    @RequirePerm(Permission.Modify)
    def stopAllDownloads(self):
        """Aborts all running downloads."""

        pyfiles = self.core.files.cachedFiles()
        for pyfile in pyfiles:
            pyfile.abortDownload()

    @RequirePerm(Permission.Modify)
    def stopDownloads(self, fids):
        """Aborts specific downloads.

        :param fids: list of file ids
        :return:
        """
        pyfiles = self.core.files.cachedFiles()
        for pyfile in pyfiles:
            if pyfile.id in fids:
                pyfile.abortDownload()

    #############################
    #  Modify Files/Packages
    #############################

    @RequirePerm(Permission.Modify)
    def setPackagePaused(self, pid, paused):
        pass

    @RequirePerm(Permission.Modify)
    def setPackageFolder(self, pid, path):
        pass

    @RequirePerm(Permission.Modify)
    def movePackage(self, pid, root):
        """ Set a new root for specific package. This will also moves the files on disk\
           and will only work when no file is currently downloading.

        :param pid: package id
        :param root: package id of new root
        :raises PackageDoesNotExists: When pid or root is missing
        :return: False if package can't be moved
        """
        return self.core.files.movePackage(pid, root)

    @RequirePerm(Permission.Modify)
    def moveFiles(self, fids, pid):
        """Move multiple files to another package. This will move the files on disk and\
        only work when files are not downloading. All files needs to be continuous ordered
        in the current package.

        :param fids: list of file ids
        :param pid: destination package
        :return: False if files can't be moved
        """
        return self.core.files.moveFiles(fids, pid)

    @RequirePerm(Permission.Modify)
    def orderPackage(self, pid, position):
        """Set new position for a package.

        :param pid: package id
        :param position: new position, 0 for very beginning
        """
        self.core.files.orderPackage(pid, position)

    @RequirePerm(Permission.Modify)
    def orderFiles(self, fids, pid, position):
        """ Set a new position for a bunch of files within a package.
        All files have to be in the same package and must be **continuous**\
        in the package. That means no gaps between them.

        :param fids: list of file ids
        :param pid: package id of parent package
        :param position:  new position: 0 for very beginning
        """
        self.core.files.orderFiles(fids, pid, position)

    @RequirePerm(Permission.Modify)
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

    @RequirePerm(Permission.Interaction)
    def isInteractionWaiting(self, mode):
        """ Check if task is waiting.

        :param mode: binary or'ed output type
        :return: boolean
        """
        return self.core.interactionManager.isTaskWaiting(mode)

    @RequirePerm(Permission.Interaction)
    def getInteractionTask(self, mode):
        """Retrieve task for specific mode.

        :param mode: binary or'ed output type
        :return: :class:`InteractionTask`
        """
        task = self.core.interactionManager.getTask(mode)
        return InteractionTask(-1) if  not task else task


    @RequirePerm(Permission.Interaction)
    def setInteractionResult(self, iid, result):
        """Set Result for a interaction task. It will be immediately removed from task queue afterwards

        :param iid: interaction id
        :param result: result as string
        """
        task = self.core.interactionManager.getTaskByID(iid)
        if task:
            task.setResult(result)

    @RequirePerm(Permission.Interaction)
    def getNotifications(self):
        """List of all available notifcations. They stay in queue for some time, client should\
           save which notifications it already has seen.

        :return: list of :class:`InteractionTask`
        """
        return self.core.interactionManager.getNotifications()

    @RequirePerm(Permission.Interaction)
    def getAddonHandler(self):
        pass

    @RequirePerm(Permission.Interaction)
    def callAddonHandler(self, plugin, func, pid_or_fid):
        pass

    @RequirePerm(Permission.Download)
    def generateDownloadLink(self, fid, timeout):
        pass

    #############################
    #  Event Handling
    #############################

    def getEvents(self, uuid):
        """Lists occurred events, may be affected to changes in future.

        :param uuid: self assigned string uuid which has to be unique
        :return: list of `Events`
        """
        # TODO: permissions?
        # TODO
        pass

    #############################
    #  Account Methods
    #############################

    @RequirePerm(Permission.Accounts)
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

    @RequirePerm(Permission.All)
    def getAccountTypes(self):
        """All available account types.

        :return: string list
        """
        return self.core.pluginManager.getPlugins("accounts").keys()

    @RequirePerm(Permission.Accounts)
    def updateAccount(self, plugin, account, password=None, options={}):
        """Changes pw/options for specific account."""
        self.core.accountManager.updateAccount(plugin, account, password, options)

    @RequirePerm(Permission.Accounts)
    def removeAccount(self, plugin, account):
        """Remove account from pyload.

        :param plugin: pluginname
        :param account: accountname
        """
        self.core.accountManager.removeAccount(plugin, account)

    #############################
    #  Auth+User Information
    #############################

    # TODO

    @RequirePerm(Permission.All)
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

        self.core.log.info(_("User '%s' tried to log in") % username)

        return self.core.db.checkAuth(username, password)

    def isAuthorized(self, func, user):
        """checks if the user is authorized for specific method

        :param func: function name
        :param user: `User`
        :return: boolean
        """
        if user.isAdmin():
            return True
        elif func in perm_map and user.hasPermission(perm_map[func]):
            return True
        else:
            return False

    # TODO
    @RequirePerm(Permission.All)
    def getUserData(self, username, password):
        """similar to `checkAuth` but returns UserData thrift type """
        user = self.checkAuth(username, password)
        if not user:
            raise UserDoesNotExists(username)

        return user.toUserData()

    def getAllUserData(self):
        """returns all known user and info"""
        return self.core.db.getAllUserData()

    def changePassword(self, username, oldpw, newpw):
        """ changes password for specific user """
        return self.core.db.changePassword(username, oldpw, newpw)

    def setUserPermission(self, user, permission, role):
        self.core.db.setPermission(user, permission)
        self.core.db.setRole(user, role)

    #############################
    #  RPC Plugin Methods
    #############################

    # TODO: obsolete

    @RequirePerm(Permission.Interaction)
    def getServices(self):
        """ A dict of available services, these can be defined by addon plugins.

        :return: dict with this style: {"plugin": {"method": "description"}}
        """
        data = {}
        for plugin, funcs in self.core.addonManager.methods.iteritems():
            data[plugin] = funcs

        return data

    @RequirePerm(Permission.Interaction)
    def hasService(self, plugin, func):
        pass

    @RequirePerm(Permission.Interaction)
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


    #TODO: permissions
    def getAllInfo(self):
        """Returns all information stored by addon plugins. Values are always strings

        :return: {"plugin": {"name": value } }
        """
        return self.core.addonManager.getAllInfo()

    def getInfoByPlugin(self, plugin):
        """Returns information stored by a specific plugin.

        :param plugin: pluginname
        :return: dict of attr names mapped to value {"name": value}
        """
        return self.core.addonManager.getInfo(plugin)
