# -*- coding: utf-8 -*-

from collections.abc import Mapping
from typing import Optional

from pydantic import BaseModel


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


class AccountInfo(BaseModel):
    validuntil: float
    login: str
    options: dict
    valid: bool
    trafficleft: int
    premium: bool
    type: str


class CaptchaTask(BaseModel):
    tid: int
    data: Optional[dict] = None
    type: Optional[str] = None
    result_type: Optional[str] = None


class ConfigItem(BaseModel):
    name: str
    description: str
    value: str
    type: str


class ConfigSection(BaseModel):
    name: str
    description: str
    items: list[ConfigItem]
    outline: Optional[str]


class DownloadInfo(BaseModel):
    fid: int
    name: str
    speed: float
    eta: int
    format_eta: str
    bleft: int
    size: int
    format_size: str
    percent: int
    status: int
    statusmsg: str
    format_wait: str
    wait_until: int
    package_id: int
    package_name: str
    plugin: str
    info: str # NOTE: needed by webui, remove in future...


class EventInfo(BaseModel):
    eventname: str
    id: Optional[str] = None
    type: Optional[int] = None
    destination: Optional[int] = None


class FileData(BaseModel):
    fid: int
    url: str
    name: str
    plugin: str
    size: int
    format_size: str
    status: int
    statusmsg: str
    package_id: int
    error: str
    order: int


class OnlineCheck(BaseModel):
    rid: int
    data: dict


class OnlineStatus(BaseModel):
    name: str
    plugin: str
    packagename: str
    status: int
    size: int


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
