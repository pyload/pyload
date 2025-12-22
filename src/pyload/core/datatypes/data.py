# -*- coding: utf-8 -*-

from typing import Optional, Any

from pydantic import BaseModel, Field

from pyload.core.datatypes.enums import DownloadStatus
from pyload.core.datatypes.json_schema_extras import FLOAT_JSON_SCHEMA
from pyload.core.datatypes.json_schema_extras import INT64_JSON_SCHEMA
from pyload.core.datatypes.json_schema_extras import OPTIONAL_FLOAT_JSON_SCHEMA
from pyload.core.datatypes.json_schema_extras import OPTIONAL_INT64_JSON_SCHEMA


class AccountInfo(BaseModel):
    validuntil: Optional[float] = Field(default=None, json_schema_extra=OPTIONAL_FLOAT_JSON_SCHEMA)
    login: str
    options: dict
    valid: bool
    trafficleft: Optional[int] = Field(default=None, json_schema_extra=OPTIONAL_INT64_JSON_SCHEMA)
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
    speed: int = Field(json_schema_extra=INT64_JSON_SCHEMA)
    eta: int
    format_eta: str
    bleft: int = Field(json_schema_extra=INT64_JSON_SCHEMA)
    size: int = Field(json_schema_extra=INT64_JSON_SCHEMA)
    format_size: str
    percent: int
    status: DownloadStatus
    statusmsg: str
    format_wait: str
    wait_until: float = Field(json_schema_extra=FLOAT_JSON_SCHEMA)
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
    size: int = Field(json_schema_extra=INT64_JSON_SCHEMA)
    format_size: str
    status: DownloadStatus
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
    size: int = Field(json_schema_extra=INT64_JSON_SCHEMA)


class PackageData(BaseModel):
    pid: int
    name: str
    folder: str
    site: str
    password: str
    dest: int
    order: int
    linksdone: Optional[int] = None
    sizedone: Optional[int] = Field(default=None, json_schema_extra=OPTIONAL_INT64_JSON_SCHEMA)
    sizetotal: Optional[int] = Field(default=None, json_schema_extra=OPTIONAL_INT64_JSON_SCHEMA)
    linkstotal: Optional[int] = None
    links: Optional[list[FileData]] = None
    fids: Optional[list[int]] = None


class ServerStatus(BaseModel):
    pause: bool
    active: int
    queue: int
    total: int
    speed: int = Field(json_schema_extra=INT64_JSON_SCHEMA)
    download: bool
    reconnect: bool
    captcha: bool
    proxy: bool


class ServiceCall(BaseModel):
    plugin: str
    func: str
    arguments: Optional[list[Any]]
    parse_arguments: bool


#: Needed by legacy API
class OldUserData(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[int] = None
    permission: Optional[int] = None
    template_name: Optional[str] = None


class UserData(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[int] = None
    permission: Optional[int] = None
    template: Optional[str] = None
