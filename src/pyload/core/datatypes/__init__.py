# -*- coding: utf-8 -*-
#      ____________
#   _ /       |    \ ___________ _ _______________ _ ___ _______________
#  /  |    ___/    |   _ __ _  _| |   ___  __ _ __| |   \\    ___  ___ _\
# /   \___/  ______/  | '_ \ || | |__/ _ \/ _` / _` |    \\  / _ \/ _ `/ \
# \       |   o|      | .__/\_, |____\___/\__,_\__,_|    // /_//_/\_, /  /
#  \______\    /______|_|___|__/________________________//______ /___/__/
#          \  /
#           \/


from collections.abc import Mapping
from enum import IntEnum


class BaseObject(Mapping):
    __slots__ = []

    def __getitem__(self, key):
        return getattr(self, key)

    def __iter__(self):
        for attr in self.__slots__:
            yield attr

    def __len__(self):
        return len(self.__slots__)


class Destination(IntEnum):
    COLLECTOR = 0
    QUEUE = 1


class DownloadStatus(IntEnum):
    ABORTED = 9
    CUSTOM = 11
    DECRYPTING = 10
    DOWNLOADING = 12
    FAILED = 8
    FINISHED = 0
    OFFLINE = 1
    ONLINE = 2
    PROCESSING = 13
    QUEUED = 3
    SKIPPED = 4
    STARTING = 7
    TEMPOFFLINE = 6
    UNKNOWN = 14
    WAITING = 5


class ElementType(IntEnum):
    FILE = 1
    PACKAGE = 0


class Input(IntEnum):
    BOOL = 4
    CHOICE = 6
    CLICK = 5
    LIST = 8
    MULTIPLE = 7
    NONE = 0
    PASSWORD = 3
    TABLE = 9
    TEXT = 1
    TEXTBOX = 2


class Output(IntEnum):
    CAPTCHA = 1
    NOTIFICATION = 4
    QUESTION = 2


class AccountInfo(BaseObject):
    __slots__ = [
        "validuntil",
        "login",
        "options",
        "valid",
        "trafficleft",
        "maxtraffic",
        "premium",
        "type",
    ]

    def __init__(
        self,
        validuntil=None,
        login=None,
        options=None,
        valid=None,
        trafficleft=None,
        maxtraffic=None,
        premium=None,
        type=None,
    ):
        self.validuntil = validuntil
        self.login = login
        self.options = options
        self.valid = valid
        self.trafficleft = trafficleft
        self.maxtraffic = maxtraffic
        self.premium = premium
        self.type = type


class CaptchaTask(BaseObject):
    __slots__ = ["tid", "data", "type", "resultType"]

    def __init__(self, tid=None, data=None, type=None, resultType=None):
        self.tid = tid
        self.data = data
        self.type = type
        self.resultType = resultType


class ConfigItem(BaseObject):
    __slots__ = ["name", "description", "value", "type"]

    def __init__(self, name=None, description=None, value=None, type=None):
        self.name = name
        self.description = description
        self.value = value
        self.type = type


class ConfigSection(BaseObject):
    __slots__ = ["name", "description", "items", "outline"]

    def __init__(self, name=None, description=None, items=None, outline=None):
        self.name = name
        self.description = description
        self.items = items
        self.outline = outline


class DownloadInfo(BaseObject):
    __slots__ = [
        "fid",
        "name",
        "speed",
        "eta",
        "format_eta",
        "bleft",
        "size",
        "format_size",
        "percent",
        "status",
        "statusmsg",
        "format_wait",
        "wait_until",
        "packageID",
        "packageName",
        "plugin",
    ]

    def __init__(
        self,
        fid=None,
        name=None,
        speed=None,
        eta=None,
        format_eta=None,
        bleft=None,
        size=None,
        format_size=None,
        percent=None,
        status=None,
        statusmsg=None,
        format_wait=None,
        wait_until=None,
        packageID=None,
        packageName=None,
        plugin=None,
    ):
        self.fid = fid
        self.name = name
        self.speed = speed
        self.eta = eta
        self.format_eta = format_eta
        self.bleft = bleft
        self.size = size
        self.format_size = format_size
        self.percent = percent
        self.status = status
        self.statusmsg = statusmsg
        self.format_wait = format_wait
        self.wait_until = wait_until
        self.packageID = packageID
        self.packageName = packageName
        self.plugin = plugin


class EventInfo(BaseObject):
    __slots__ = ["eventname", "id", "type", "destination"]

    def __init__(self, eventname=None, id=None, type=None, destination=None):
        self.eventname = eventname
        self.id = id
        self.type = type
        self.destination = destination


class FileData(BaseObject):
    __slots__ = [
        "fid",
        "url",
        "name",
        "plugin",
        "size",
        "format_size",
        "status",
        "statusmsg",
        "packageID",
        "error",
        "order",
    ]

    def __init__(
        self,
        fid=None,
        url=None,
        name=None,
        plugin=None,
        size=None,
        format_size=None,
        status=None,
        statusmsg=None,
        packageID=None,
        error=None,
        order=None,
    ):
        self.fid = fid
        self.url = url
        self.name = name
        self.plugin = plugin
        self.size = size
        self.format_size = format_size
        self.status = status
        self.statusmsg = statusmsg
        self.packageID = packageID
        self.error = error
        self.order = order


class FileDoesNotExists(Exception):
    __slots__ = ["fid"]

    def __init__(self, fid=None):
        self.fid = fid


class InteractionTask(BaseObject):
    __slots__ = [
        "iid",
        "input",
        "structure",
        "preset",
        "output",
        "data",
        "title",
        "description",
        "plugin",
    ]

    def __init__(
        self,
        iid=None,
        input=None,
        structure=None,
        preset=None,
        output=None,
        data=None,
        title=None,
        description=None,
        plugin=None,
    ):
        self.iid = iid
        self.input = input
        self.structure = structure
        self.preset = preset
        self.output = output
        self.data = data
        self.title = title
        self.description = description
        self.plugin = plugin


class OnlineCheck(BaseObject):
    __slots__ = ["rid", "data"]

    def __init__(self, rid=None, data=None):
        self.rid = rid
        self.data = data


class OnlineStatus(BaseObject):
    __slots__ = ["name", "plugin", "packagename", "status", "size"]

    def __init__(
        self, name=None, plugin=None, packagename=None, status=None, size=None
    ):
        self.name = name
        self.plugin = plugin
        self.packagename = packagename
        self.status = status
        self.size = size


class PackageData(BaseObject):
    __slots__ = [
        "pid",
        "name",
        "folder",
        "site",
        "password",
        "dest",
        "order",
        "linksdone",
        "sizedone",
        "sizetotal",
        "linkstotal",
        "links",
        "fids",
    ]

    def __init__(
        self,
        pid=None,
        name=None,
        folder=None,
        site=None,
        password=None,
        dest=None,
        order=None,
        linksdone=None,
        sizedone=None,
        sizetotal=None,
        linkstotal=None,
        links=None,
        fids=None,
    ):
        self.pid = pid
        self.name = name
        self.folder = folder
        self.site = site
        self.password = password
        self.dest = dest
        self.order = order
        self.linksdone = linksdone
        self.sizedone = sizedone
        self.sizetotal = sizetotal
        self.linkstotal = linkstotal
        self.links = links
        self.fids = fids


class PackageDoesNotExists(Exception):
    __slots__ = ["pid"]

    def __init__(self, pid=None):
        self.pid = pid


class ServerStatus(BaseObject):
    __slots__ = [
        "pause",
        "active",
        "queue",
        "total",
        "speed",
        "download",
        "reconnect",
        "captcha",
    ]

    def __init__(
        self,
        pause=None,
        active=None,
        queue=None,
        total=None,
        speed=None,
        download=None,
        reconnect=None,
        captcha=None,
    ):
        self.pause = pause
        self.active = active
        self.queue = queue
        self.total = total
        self.speed = speed
        self.download = download
        self.reconnect = reconnect
        self.captcha = captcha


class ServiceCall(BaseObject):
    __slots__ = ["plugin", "func", "arguments", "parseArguments"]

    def __init__(self, plugin=None, func=None, arguments=None, parseArguments=None):
        self.plugin = plugin
        self.func = func
        self.arguments = arguments
        self.parseArguments = parseArguments


class ServiceDoesNotExists(Exception):
    __slots__ = ["plugin", "func"]

    def __init__(self, plugin=None, func=None):
        self.plugin = plugin
        self.func = func


class ServiceException(Exception):
    __slots__ = ["msg"]

    def __init__(self, msg=None):
        self.msg = msg


#: Needed by legacy API
class OldUserData(BaseObject):
    __slots__ = ["name", "email", "role", "permission", "templateName"]

    def __init__(
        self, name=None, email=None, role=None, permission=None, templateName=None
    ):
        self.name = name
        self.email = email
        self.role = role
        self.permission = permission
        self.templateName = templateName
        
        
class UserData(BaseObject):
    __slots__ = ["id", "name", "email", "role", "permission", "template"]

    def __init__(
        self, id=None, name=None, email=None, role=None, permission=None, template=None
    ):
        self.id = id
        self.name = name
        self.email = email
        self.role = role
        self.permission = permission
        self.template = template
        