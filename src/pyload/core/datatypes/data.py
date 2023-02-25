# -*- coding: utf-8 -*-

from collections.abc import Mapping


class AbstractData(Mapping):
    __slots__ = []

    def __getitem__(self, name):
        return getattr(self, name)

    def __setitem__(self, name, value):
        return setattr(self, name, value)

    def __iter__(self):
        for attr in self.__slots__:
            yield attr

    def __len__(self):
        return len(self.__slots__)


class AccountInfo(AbstractData):
    __slots__ = [
        "validuntil",
        "login",
        "options",
        "valid",
        "trafficleft",
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
        premium=None,
        type=None,
    ):
        self.validuntil = validuntil
        self.login = login
        self.options = options
        self.valid = valid
        self.trafficleft = trafficleft
        self.premium = premium
        self.type = type


class CaptchaTask(AbstractData):
    __slots__ = ["tid", "data", "type", "result_type"]

    def __init__(self, tid=None, data=None, type=None, result_type=None):
        self.tid = tid
        self.data = data
        self.type = type
        self.result_type = result_type


class ConfigItem(AbstractData):
    __slots__ = ["name", "description", "value", "type"]

    def __init__(self, name=None, description=None, value=None, type=None):
        self.name = name
        self.description = description
        self.value = value
        self.type = type


class ConfigSection(AbstractData):
    __slots__ = ["name", "description", "items", "outline"]

    def __init__(self, name=None, description=None, items=None, outline=None):
        self.name = name
        self.description = description
        self.items = items
        self.outline = outline


class DownloadInfo(AbstractData):
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
        "package_id",
        "package_name",
        "plugin",
        "info",  # NOTE: needed by webui, remove in future...
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
        package_id=None,
        package_name=None,
        plugin=None,
        info=None,
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
        self.package_id = package_id
        self.package_name = package_name
        self.plugin = plugin
        self.info = info


class EventInfo(AbstractData):
    __slots__ = ["eventname", "id", "type", "destination"]

    def __init__(self, eventname=None, id=None, type=None, destination=None):
        self.eventname = eventname
        self.id = id
        self.type = type
        self.destination = destination


class FileData(AbstractData):
    __slots__ = [
        "fid",
        "url",
        "name",
        "plugin",
        "size",
        "format_size",
        "status",
        "statusmsg",
        "package_id",
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
        package_id=None,
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
        self.package_id = package_id
        self.error = error
        self.order = order


class InteractionTask(AbstractData):
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


class OnlineCheck(AbstractData):
    __slots__ = ["rid", "data"]

    def __init__(self, rid=None, data=None):
        self.rid = rid
        self.data = data


class OnlineStatus(AbstractData):
    __slots__ = ["name", "plugin", "packagename", "status", "size"]

    def __init__(
        self, name=None, plugin=None, packagename=None, status=None, size=None
    ):
        self.name = name
        self.plugin = plugin
        self.packagename = packagename
        self.status = status
        self.size = size


class PackageData(AbstractData):
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


class ServerStatus(AbstractData):
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


class ServiceCall(AbstractData):
    __slots__ = ["plugin", "func", "arguments", "parse_arguments"]

    def __init__(self, plugin=None, func=None, arguments=None, parse_arguments=None):
        self.plugin = plugin
        self.func = func
        self.arguments = arguments
        self.parse_arguments = parse_arguments


#: Needed by legacy API
class OldUserData(AbstractData):
    __slots__ = ["name", "email", "role", "permission", "template_name"]

    def __init__(
        self, name=None, email=None, role=None, permission=None, template_name=None
    ):
        self.name = name
        self.email = email
        self.role = role
        self.permission = permission
        self.template_name = template_name


class UserData(AbstractData):
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
