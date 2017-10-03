# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from abc import ABCMeta
from builtins import object
from enum import IntEnum

from future import standard_library
from future.utils import with_metaclass

standard_library.install_aliases()


class BaseObject(with_metaclass(ABCMeta, object)):

    __slots__ = []

    def __str__(self):
        return '<{0} {1}>'.format(self.__class__.__name__, ', '.join(
            '{0}={1}'.format(k, getattr(self, k)) for k in self.__slots__))


class Conflict(Exception):

    __slots__ = []


class Forbidden(Exception):

    __slots__ = []


class InvalidConfigSection(Exception):

    __slots__ = ['section']

    def __init__(self, section=None):
        super(InvalidConfigSection, self).__init__()
        self.section = section


class ServiceDoesNotExist(Exception):

    __slots__ = ['plugin', 'func']

    def __init__(self, plugin=None, func=None):
        super(ServiceDoesNotExist, self).__init__()
        self.plugin = plugin
        self.func = func


class ServiceException(Exception):

    __slots__ = ['msg']

    def __init__(self, msg=None):
        super(ServiceException, self).__init__()
        self.msg = msg


class Unauthorized(Exception):

    __slots__ = []


class DownloadState(IntEnum):
    All = 0
    Finished = 1
    Unfinished = 2
    Failed = 3
    Unmanaged = 4


class DownloadStatus(IntEnum):
    NA = 0
    Offline = 1
    Online = 2
    Queued = 3
    Paused = 4
    Finished = 5
    Skipped = 6
    Failed = 7
    Starting = 8
    Waiting = 9
    Downloading = 10
    TempOffline = 11
    Aborted = 12
    NotPossible = 13
    Missing = 14
    FileMismatch = 15
    Occupied = 16
    Decrypting = 17
    Processing = 18
    Custom = 19
    Unknown = 20


class InputType(IntEnum):
    NA = 0
    Bool = 1
    Int = 2
    Float = 3
    Octal = 4
    Str = 5
    Bytes = 6
    Size = 7
    File = 8
    Folder = 9
    Password = 10
    Time = 11
    Click = 12
    Address = 13
    Tristate = 14
    StrList = 15


class MediaType(IntEnum):
    All = 0
    Other = 1
    Audio = 2
    Image = 4
    Video = 8
    Document = 16
    Archive = 32
    Executable = 64


class Permission(IntEnum):
    All = 0
    Add = 1
    Delete = 2
    Modify = 4
    Download = 8
    Accounts = 16
    Interaction = 32
    Plugins = 64


class ProgressType(IntEnum):
    All = 0
    Other = 1
    Download = 2
    Decrypting = 4
    LinkCheck = 8
    Addon = 16
    FileOperation = 32


class AccountInfo(BaseObject):

    __slots__ = [
        'aid', 'plugin', 'loginname', 'owner', 'valid', 'validuntil',
        'trafficleft', 'maxtraffic', 'premium', 'activated', 'shared',
        'config']

    def __init__(
            self, aid=None, plugin=None, loginname=None, owner=None,
            valid=None, validuntil=None, trafficleft=None, maxtraffic=None,
            premium=None, activated=None, shared=None, config=None):
        super(AccountInfo, self).__init__()

        self.aid = aid
        self.plugin = plugin
        self.loginname = loginname
        self.owner = owner
        self.valid = valid
        self.validuntil = validuntil
        self.trafficleft = trafficleft
        self.maxtraffic = maxtraffic
        self.premium = premium
        self.activated = activated
        self.shared = shared
        self.config = config


class AddonInfo(BaseObject):

    __slots__ = ['name', 'description', 'value']

    def __init__(self, name=None, description=None, value=None):
        super(AddonInfo, self).__init__()

        self.name = name
        self.description = description
        self.value = value


class AddonService(BaseObject):

    __slots__ = ['__name__', 'func_name', 'label',
                 'description', 'arguments', 'pack', 'media']

    def __init__(self, func_name=None, label=None, description=None,
                 arguments=None, pack=None, media=None):
        super(AddonService, self).__init__()

        self.__name__ = func_name
        self.label = label
        self.description = description
        self.arguments = arguments
        self.pack = pack
        self.media = media


class ConfigHolder(BaseObject):

    __slots__ = ['name', 'label', 'description',
                 'explanation', 'items', 'info']

    def __init__(self, name=None, label=None, description=None,
                 explanation=None, items=None, info=None):
        super(ConfigHolder, self).__init__()

        self.name = name
        self.label = label
        self.description = description
        self.explanation = explanation
        self.items = items
        self.info = info


class ConfigInfo(BaseObject):

    __slots__ = ['name', 'label', 'description',
                 'category', 'user_context', 'activated']

    def __init__(self, name=None, label=None, description=None,
                 category=None, user_context=None, activated=None):
        super(ConfigInfo, self).__init__()

        self.name = name
        self.label = label
        self.description = description
        self.category = category
        self.user_context = user_context
        self.activated = activated


class ConfigItem(BaseObject):

    __slots__ = ['name', 'label', 'description', 'input', 'value']

    def __init__(self, name=None, label=None,
                 description=None, input=None, value=None):
        super(ConfigItem, self).__init__()

        self.name = name
        self.label = label
        self.description = description
        self.input = input
        self.value = value


class DownloadInfo(BaseObject):

    __slots__ = ['url', 'plugin', 'hash', 'status', 'statusmsg', 'error']

    def __init__(self, url=None, plugin=None, hash=None,
                 status=None, statusmsg=None, error=None):
        super(DownloadInfo, self).__init__()

        self.url = url
        self.plugin = plugin
        self.hash = hash
        self.status = status
        self.statusmsg = statusmsg
        self.error = error


class DownloadProgress(BaseObject):
    __slots__ = ['fid', 'pid', 'speed', 'conn', 'status']

    def __init__(self, fid=None, pid=None, speed=None, conn=None, status=None):
        super(DownloadProgress, self).__init__()

        self.fid = fid
        self.pid = pid
        self.speed = speed
        self.conn = conn
        self.status = status


class EventInfo(BaseObject):

    __slots__ = ['eventname', 'event_args']

    def __init__(self, eventname=None, event_args=None):
        super(EventInfo, self).__init__()
        self.eventname = eventname
        self.event_args = event_args


class Input(BaseObject):

    __slots__ = ['type', 'default', 'data']

    def __init__(self, type_=None, default=None, data=None):
        super(Input, self).__init__()
        self.type = type_
        self.default = default
        self.data = data


class LinkStatus(BaseObject):

    __slots__ = ['url', 'name', 'size', 'status', 'plugin', 'hash']

    def __init__(self, url=None, name=None, size=None,
                 status=None, plugin=None, hash=None):
        super(LinkStatus, self).__init__()

        self.url = url
        self.name = name
        self.size = size
        self.status = status
        self.plugin = plugin
        self.hash = hash


class ProgressInfo(BaseObject):

    __slots__ = ['plugin', 'name', 'statusmsg', 'eta',
                 'done', 'total', 'owner', 'type', 'download']

    def __init__(self, plugin=None, name=None, statusmsg=None, eta=None,
                 done=None, total=None, owner=None, type_=None, download=None):
        super(ProgressInfo, self).__init__()

        self.plugin = plugin
        self.name = name
        self.statusmsg = statusmsg
        self.eta = eta
        self.done = done
        self.total = total
        self.owner = owner
        self.type = type_
        self.download = download


class StatusInfo(BaseObject):

    __slots__ = [
        'speed', 'linkstotal', 'linksqueue', 'sizetotal', 'sizequeue',
        'notifications', 'paused', 'download', 'reconnect', 'quota']

    def __init__(self, speed=None, linkstotal=None, linksqueue=None,
                 sizetotal=None, sizequeue=None, notifications=None,
                 paused=None, download=None, reconnect=None, quota=None):
        super(StatusInfo, self).__init__()

        self.speed = speed
        self.linkstotal = linkstotal
        self.linksqueue = linksqueue
        self.sizetotal = sizetotal
        self.sizequeue = sizequeue
        self.notifications = notifications
        self.paused = paused
        self.download = download
        self.reconnect = reconnect
        self.quota = quota


class TreeCollection(BaseObject):

    __slots__ = ['root', 'files', 'packages']

    def __init__(self, root=None, files=None, packages=None):
        super(TreeCollection, self).__init__()

        self.root = root
        self.files = files
        self.packages = packages
