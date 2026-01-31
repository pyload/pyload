# -*- coding: utf-8 -*-
#       ____________
#   ___/       |    \_____________ _                 _ ___
#  /        ___/    |    _ __ _  _| |   ___  __ _ __| |   \
# /    \___/  ______/   | '_ \ || | |__/ _ \/ _` / _` |    \
# \            ◯ |      | .__/\_, |____\___/\__,_\__,_|    /
#  \_______\    /_______|_|   |__/________________________/
#           \  /
#            \/

import os
import re
import time
from enum import IntFlag
from typing import Any, Callable, Optional

from pyload import PKGDIR

from ..datatypes.data import (
    AccountInfo, CaptchaTask, ConfigItem, ConfigSection, DownloadInfo, EventInfo, FileData, OldUserData, OnlineCheck,
    OnlineStatus, PackageData, ServerStatus, ServiceCall, UserData)
from ..datatypes.enums import Destination, ElementType
from ..datatypes.exceptions import FileDoesNotExists, PackageDoesNotExists, ServiceDoesNotExists, ServiceException
from ..datatypes.pyfile import PyFile
from ..log_factory import LogFactory
from ..network.request_factory import get_url
from ..utils import fs, seconds
from ..utils.old.packagetools import parse_names

# contains function names mapped to their permissions
# unlisted functions are for admins only
perm_map = {}

# contains function names mapped to their legacy name
legacy_map = {}

# contains function names mapped to their allowed HTTP method (e.g., 'GET', 'POST', 'PUT', 'DELETE')
method_map = {}


RE_URLMATCH = re.compile(
    r"(?:https?|ftps?|xdcc|sftp):(?://|\\\\)+[\w\-._~:/?#\[\]@!$&'()*+,;=]*|magnet:\?.+",
    re.IGNORECASE,
)


class Perms(IntFlag):
    ANY = 0  #: requires no permission, but login
    ADD = 1  #: can add packages
    DELETE = 2  #: can delete packages
    STATUS = 4  #: see and change server status
    LIST = 16  #: see queue and collector
    MODIFY = 32  #: modify some attribute of downloads
    DOWNLOAD = 64  #: can download from webinterface
    SETTINGS = 128  #: can access settings
    ACCOUNTS = 256  #: can access accounts
    LOGS = 512  #: can see server logs


class Role(IntFlag):
    ADMIN = 0  #: admin has all permissions implicit
    USER = 1


# decorator only called on init, never initialized, so has no effect on runtime
def permission(bits: Perms) -> Callable:
    class Wrapper:
        def __new__(cls, func, *args, **kwargs):
            perm_map[func.__name__] = bits
            return func

    return Wrapper


def legacy(legacy_name: str) -> Callable:
    class Wrapper:
        def __new__(cls, func, *args, **kwargs):
            legacy_map[func.__name__] = legacy_name
            return func

    return Wrapper


def http_method(method_type: str) -> Callable:
    class Wrapper:
        def __new__(cls, func, *args, **kwargs):
            method_map[func.__name__] = method_type.upper()
            return func

    return Wrapper


# Convenience aliases for common methods
get = http_method('GET')
post = http_method('POST')
put = http_method('PUT')
delete = http_method('DELETE')


def has_permission(user_perms: Perms, required_perms: Perms):
    # bitwise or perms before if needed
    return required_perms == (user_perms & required_perms)


class Api:
    """
    **pyLoads API**

    This is accessible either internal via core.api.

    see openapi.json for information about data structures and what methods are usable with rpc.

    Most methods requires specific permissions, please look at the source code if you need to know.\
    These can be configured via webinterface.
    Admin user have all permissions, and are the only ones who can access the methods with no specific permission.
    """

    # API VERSION
    __version__ = 1

    def __new__(cls, core):
        obj = super(Api, cls).__new__(cls)

        # add methods specified by the @legacy decorator,
        # set legacy method permissions according to the @permissions decorator
        # and also set the correct allowed HTTP method for the legacy function
        for func_name, legacy_name in legacy_map.items():
            func = getattr(obj, func_name)
            setattr(obj, legacy_name, func)

            permissions = perm_map.get(func_name)
            if permissions is not None:
                perm_map[legacy_name] = permissions

            allowed_method = method_map.get(func_name)
            if allowed_method is not None:
                method_map[legacy_name] = allowed_method

        return obj

    def __init__(self, core):
        self.pyload = core
        self._ = core._

    def _required_http_method_for_api(self, func_name: str) -> Optional[str]:
        """
        Get the allowed HTTP method for an API method

        :param func_name: the name of the API method
        :return: allowed HTTP method (e.g., 'GET', 'POST', 'PUT', 'DELETE') for the API method or None
        """
        return method_map.get(func_name)

    def _convert_py_file(self, p) -> FileData:
        f = FileData(
            fid=p["id"],
            url=p["url"],
            name=p["name"],
            plugin=p["plugin"],
            size=p["size"],
            format_size=p["format_size"],
            status=p["status"],
            statusmsg=p["statusmsg"],
            package_id=p["package"],
            error=p["error"],
            order=p["order"]
        )
        return f

    def _convert_config_format(self, c) -> dict[str, ConfigSection]:
        sections = {}
        for section_name, sub in c.items():
            items = []
            for key, data in sub.items():
                if key in ("desc", "outline"):
                    continue
                item = ConfigItem(name=key,
                                  description=data["desc"],
                                  value=str(data["value"]),
                                  type=data["type"])
                items.append(item)
            section = ConfigSection(name=section_name,
                                    description=sub["desc"],
                                    items=items,
                                    outline=sub.get("outline"))
            sections[section_name] = section

        return sections

    @legacy("getConfigValue")
    @permission(Perms.SETTINGS)
    @get
    def get_config_value(self, category: str, option: str, section: str = "core") -> Any:
        """
        Retrieve config value.

        :param category: name of category, or plugin
        :param option: config option
        :param section: 'plugin' or 'core'
        :return: config value
        """
        if section == "core":
            value = self.pyload.config[category][option]
        else:
            value = self.pyload.config.get_plugin(category, option)
        return value

    @legacy("setConfigValue")
    @permission(Perms.SETTINGS)
    @post
    def set_config_value(self, category: str, option: str, value: Any, section: str = "core") -> None:
        """
        Set new config value.

        :param category:
        :param option:
        :param value: new config value
        :param section: 'plugin' or 'core
        """
        self.pyload.addon_manager.dispatch_event(
            "config_changed", category, option, value, section
        )

        if section == "core":
            if category == "general" and option == "storage_folder":
                # Forbid setting the download folder inside dangerous locations
                correct_case = lambda x: x.lower() if os.name == "nt" else x
                directories = [
                    correct_case(os.path.join(os.path.realpath(d), ""))
                    for d in [value, PKGDIR, self.pyload.userdir]
                ]
                if any(directories[0].startswith(d) for d in directories[1:]):
                    return

            self.pyload.config.set(category, option, value)

            if category == "download" and option in (
                "limit_speed",
                "max_speed",
            ):  #: not such a nice method to update the limit
                self.pyload.request_factory.update_bucket()

        elif section == "plugin":
            self.pyload.config.set_plugin(category, option, value)

    @legacy("getConfig")
    @permission(Perms.SETTINGS)
    @get
    def get_config(self) -> dict[str, ConfigSection]:
        """
        Retrieves complete config of core.

        :return: dict of section name to `ConfigSection`
        """
        return self._convert_config_format(self.pyload.config.config)

    @legacy("getConfigDict")
    @get
    def get_config_dict(self) -> dict[Any, Any]:
        """
        Retrieves complete config in dict format, not for RPC.

        :return: dict
        """
        return self.pyload.config.config

    @legacy("getPluginConfig")
    @permission(Perms.SETTINGS)
    @get
    def get_plugin_config(self) -> dict[str, ConfigSection]:
        """
        Retrieves complete config for all plugins.

        :return: dict of section name to `ConfigSection`
        """
        return self._convert_config_format(self.pyload.config.plugin)

    @legacy("getPluginConfigDict")
    @permission(Perms.SETTINGS)
    @get
    def get_plugin_config_dict(self) -> dict[Any, Any]:
        """
        Plugin config as dict, not for RPC.

        :return: dict
        """
        return self.pyload.config.plugin

    @legacy("pauseServer")
    @permission(Perms.STATUS)
    @post
    def pause_server(self) -> None:
        """
        Pause server: It won't start any new downloads, but nothing gets aborted.
        """
        self.pyload.thread_manager.pause = True

    @legacy("unpauseServer")
    @permission(Perms.STATUS)
    @post
    def unpause_server(self) -> None:
        """
        Unpause server: New Downloads will be started.
        """
        self.pyload.thread_manager.pause = False

    @legacy("togglePause")
    @permission(Perms.STATUS)
    @post
    def toggle_pause(self) -> bool:
        """
        Toggle pause state.

        :return: new pause state
        """
        self.pyload.thread_manager.pause ^= True
        return self.pyload.thread_manager.pause

    @legacy("toggleReconnect")
    @permission(Perms.STATUS)
    @post
    def toggle_reconnect(self) -> bool:
        """
        Toggle reconnect activation.

        :return: new reconnect state
        """
        self.pyload.config.toggle("reconnect", "enabled")
        return self.pyload.config.get("reconnect", "enabled")

    @permission(Perms.STATUS)
    @post
    def toggle_proxy(self) -> bool:
        """
        Toggle proxy activation.

        :return: new proxy state
        """
        self.pyload.config.toggle("proxy", "enabled")
        return self.pyload.config.get("proxy", "enabled")

    @legacy("statusServer")
    @permission(Perms.LIST)
    @get
    def status_server(self) -> ServerStatus:
        """
        Some general information about the current status of pyLoad.

        :return: `ServerStatus`
        """
        server_status = ServerStatus(
            pause=self.pyload.thread_manager.pause,
            active=len(self.pyload.thread_manager.processing_ids()),
            queue=self.pyload.files.get_queue_count(),
            total=self.pyload.files.get_file_count(),
            speed=0,
            download=not self.pyload.thread_manager.pause and self.is_time_download(),
            reconnect=self.pyload.config.get("reconnect", "enabled") and self.is_time_reconnect(),
            captcha=self.is_captcha_waiting(),
            proxy=self.pyload.config.get("proxy", "enabled"),
        )

        for pyfile in [
            x.active
            for x in self.pyload.thread_manager.threads
            if x.active and isinstance(x.active, PyFile)
        ]:
            server_status.speed += pyfile.get_speed()  #: bytes/s

        return server_status

    @legacy("freeSpace")
    @permission(Perms.STATUS)
    @get
    def free_space(self) -> int:
        """
        Available free space at download directory in bytes.
        """
        return fs.free_space(self.pyload.config.get("general", "storage_folder"))

    @legacy("getServerVersion")
    @permission(Perms.ANY)
    @get
    def get_server_version(self) -> str:
        """
        pyLoad Core version.
        """
        return self.pyload.version

    @post
    def kill(self) -> None:
        """
        Clean way to quit pyLoad.
        """
        self.pyload._do_exit = True

    @post
    def restart(self) -> None:
        """
        Restart pyload core.
        """
        self.pyload._do_restart = True

    @legacy("getLog")
    @permission(Perms.LOGS)
    @get
    def get_log(self, offset: int = 0) -> list[str]:
        """
        Returns most recent log entries.

        :param offset: line offset
        :return: List of log entries
        """
        filelog_folder = self.pyload.config.get("log", "filelog_folder")
        if not filelog_folder:
            filelog_folder = os.path.join(self.pyload.userdir, "logs")

        path = os.path.join(filelog_folder, "pyload" + LogFactory.FILE_EXTENSION)
        try:
            with open(path) as fh:
                lines = fh.readlines()
            if offset >= len(lines):
                return []
            return lines[offset:]
        except Exception:
            return ["No log available"]

    @legacy("isTimeDownload")
    @permission(Perms.STATUS)
    @get
    def is_time_download(self) -> bool:
        """
        Checks if pyload will start new downloads according to time in config.

        :return: bool
        """
        start = self.pyload.config.get("download", "start_time").split(":")
        end = self.pyload.config.get("download", "end_time").split(":")
        return seconds.compare(start, end)

    @legacy("isTimeReconnect")
    @permission(Perms.STATUS)
    @get
    def is_time_reconnect(self) -> bool:
        """
        Checks if pyload will try to make a reconnect.

        :return: bool
        """
        start = self.pyload.config.get("reconnect", "start_time").split(":")
        end = self.pyload.config.get("reconnect", "end_time").split(":")
        return seconds.compare(start, end) and self.pyload.config.get(
            "reconnect", "enabled"
        )

    @legacy("statusDownloads")
    @permission(Perms.LIST)
    @get
    def status_downloads(self) -> list[DownloadInfo]:
        """
        Status of all currently running downloads.

        :return: list of `DownloadInfo`
        """
        data = []
        for pyfile in self.pyload.thread_manager.get_active_files():
            if not isinstance(pyfile, PyFile):
                continue

            data.append(
                DownloadInfo(
                    fid=pyfile.id,
                    name=pyfile.name,
                    speed=pyfile.get_speed(),
                    eta=pyfile.get_eta(),
                    format_eta=pyfile.format_eta(),
                    bleft=pyfile.get_bytes_left(),
                    size=pyfile.get_size(),
                    format_size=pyfile.format_size(),
                    percent=pyfile.get_percent(),
                    status=pyfile.status,
                    statusmsg=pyfile.get_status_name(),
                    format_wait=pyfile.format_wait(),
                    wait_until=pyfile.wait_until,
                    package_id=pyfile.packageid,
                    package_name=pyfile.package().name,
                    plugin=pyfile.pluginname,
                    info=""
                )
            )

        return data

    @legacy("addPackage")
    @permission(Perms.ADD)
    @post
    def add_package(self, name: str, links: list[str], dest: Destination = Destination.QUEUE) -> int:
        """
        Adds a package, with links to desired destination.

        :param name: name of the new package
        :param links: list of urls
        :param dest: `Destination`
        :return: package id of the new package
        """
        if self.pyload.config.get("general", "folder_per_package"):
            folder = name
        else:
            folder = ""

        folder = (
            folder.replace("http://", "")
            .replace("https://", "")
            .replace("../", "_")
            .replace("..\\", "_")
            .replace(":", "")
            .replace("/", "_")
            .replace("\\", "_")
            .replace("\r", "_")
            .replace("\n", "_")
        )

        sanitized_name = name.replace("\n", "\\n").replace("\r", "\\r")
        package_id = self.pyload.files.add_package(sanitized_name, folder, Destination(dest))

        self.pyload.files.add_links(links, package_id)

        self.pyload.log.info(
            self._("Added package {name} containing {count:d} links").format(
                name=sanitized_name, count=len(links)
            )
        )

        self.pyload.files.save()

        return package_id

    @legacy("parseURLs")
    @permission(Perms.ADD)
    @post
    def parse_urls(self, html: Optional[str] = None, url: Optional[str] = None) -> dict[str, list[str]]:
        """
        Parses html content or any arbitrary text for links and returns result of
        `check_urls`

        :param html: html source
        :param url: url to load html source from
        :return:
        """
        urls = set()

        if html:
            urls.update(RE_URLMATCH.findall(html))

        if url:
            page = get_url(url)
            urls.update(RE_URLMATCH.findall(page))

        return self.check_urls(list(urls))

    @legacy("checkURLs")
    @permission(Perms.ADD)
    @post
    def check_urls(self, urls: list[str]) -> dict[str, list[str]]:
        """
        Gets urls and returns pluginname mapped to list of matched urls.

        :param urls:
        :return: {plugin: urls}
        """
        data = self.pyload.plugin_manager.parse_urls(urls)
        plugins = {}

        for url, plugin in data:
            if plugin in plugins:
                plugins[plugin].append(url)
            else:
                plugins[plugin] = [url]

        return plugins

    @legacy("checkOnlineStatus")
    @permission(Perms.ADD)
    @post
    def check_online_status(self, urls: list[str]) -> OnlineCheck:
        """
        Initiates online status check.

        :param urls:
        :return: initial set of data as `OnlineCheck` instance containing the result id
        """
        data = self.pyload.plugin_manager.parse_urls(urls)

        rid = self.pyload.thread_manager.create_result_thread(data, False)

        tmp = [
            (url, (url, OnlineStatus(name=url,
                                     plugin=pluginname,
                                     packagename="unknown",
                                     status=3,
                                     size=0)))
            for url, pluginname in data
        ]
        data = parse_names(tmp)
        result = {}

        for k, v in data.items():
            for url, status in v:
                status.packagename = k
                result[url] = status

        return OnlineCheck(rid=rid, data=result)

    @legacy("checkOnlineStatusContainer")
    @permission(Perms.ADD)
    @post
    def check_online_status_container(self, urls: list[str], container: str, data: bytes) -> OnlineCheck:
        """
        checks online status of urls and a submitted container file.

        :param urls: list of urls
        :param container: container file name
        :param data: file content
        :return: online check
        """
        with open(
            os.path.join(
                self.pyload.config.get("general", "storage_folder"), "tmp_" + container
            ),
            "wb",
        ) as th:
            th.write(data)

        return self.check_online_status(urls + [th.name])

    @legacy("pollResults")
    @permission(Perms.ADD)
    @get
    def poll_results(self, rid: int) -> OnlineCheck:
        """
        Polls the result available for ResultID.

        :param rid: `ResultID`
        :return: `OnlineCheck`, if rid is -1 then no more data available
        """
        result = self.pyload.thread_manager.get_info_result(rid)

        if "ALL_INFO_FETCHED" in result:
            del result["ALL_INFO_FETCHED"]
            return OnlineCheck(rid=-1, data=result)
        else:
            return OnlineCheck(rid=rid, data=result)

    @legacy("generatePackages")
    @permission(Perms.ADD)
    @post
    def generate_packages(self, links: list[str]) -> dict[str, list[str]]:
        """
        Parses links, generates packages names from urls.

        :param links: list of urls
        :return: package names mapped to urls
        """
        result = parse_names((x, x) for x in links)
        return result

    @legacy("generateAndAddPackages")
    @permission(Perms.ADD)
    @post
    def generate_and_add_packages(self, links: list[str], dest: Destination = Destination.COLLECTOR) -> list[int]:
        """
        Generates and add packages.

        :param links: list of urls
        :param dest: `Destination`
        :return: list of package ids
        """
        return [
            self.add_package(name, urls, dest)
            for name, urls in self.generate_packages(links).items()
        ]

    @legacy("checkAndAddPackages")
    @permission(Perms.ADD)
    @post
    def check_and_add_packages(self, links: list[str], dest: Destination = Destination.COLLECTOR) -> None:
        """
        Checks online status, retrieves names, and will add packages.
        Because of these packages are not added immediately, only for internal use.

        :param links: list of urls
        :param dest: `Destination`
        :return: None
        """
        data = self.pyload.plugin_manager.parse_urls(links)
        self.pyload.thread_manager.create_result_thread(data, True)

    @legacy("getPackageData")
    @permission(Perms.LIST)
    @get
    def get_package_data(self, package_id: int) -> PackageData:
        """
        Returns complete information about package, and included files.

        :param package_id: package id
        :return: `PackageData` with .links attribute
        """
        data = self.pyload.files.get_package_data(int(package_id))

        if not data:
            raise PackageDoesNotExists(package_id)

        pdata = PackageData(
            pid=data["id"],
            name=data["name"],
            folder=data["folder"],
            site=data["site"],
            password=data["password"],
            dest=data["queue"],
            order=data["order"],
            links=[self._convert_py_file(x) for x in data["links"].values()],
        )

        return pdata

    @legacy("getPackageInfo")
    @permission(Perms.LIST)
    @get
    def get_package_info(self, package_id: int) -> PackageData:
        """
        Returns information about package, without detailed information about containing
        files.

        :param package_id: package id
        :return: `PackageData` with .fid attribute
        """
        data = self.pyload.files.get_package_data(int(package_id))

        if not data:
            raise PackageDoesNotExists(package_id)

        pdata = PackageData(
            pid=data["id"],
            name=data["name"],
            folder=data["folder"],
            site=data["site"],
            password=data["password"],
            dest=data["queue"],
            order=data["order"],
            fids=[int(x) for x in data["links"]],
        )

        return pdata

    @legacy("getFileData")
    @permission(Perms.LIST)
    @get
    def get_file_data(self, file_id: int) -> FileData:
        """
        Get complete information about a specific file.

        :param file_id: file id
        :return: `FileData`
        """
        info = self.pyload.files.get_file_data(int(file_id))
        if not info:
            raise FileDoesNotExists(file_id)

        fileinfo = list(info.values())[0]
        fdata = self._convert_py_file(fileinfo)
        return fdata

    @legacy("deleteFiles")
    @permission(Perms.DELETE)
    @post
    def delete_files(self, file_ids: list[int]) -> None:
        """
        Deletes several file entries from pyload.

        :param file_ids: list of file ids
        """
        for file_id in file_ids:
            self.pyload.files.delete_link(int(file_id))

        self.pyload.files.save()

    @legacy("deletePackages")
    @permission(Perms.DELETE)
    @post
    def delete_packages(self, package_ids: list[int]) -> None:
        """
        Deletes packages and containing links.

        :param package_ids: list of package ids
        """
        for package_id in package_ids:
            self.pyload.files.delete_package(int(package_id))

        self.pyload.files.save()

    @legacy("getQueue")
    @permission(Perms.LIST)
    @get
    def get_queue(self) -> list[PackageData]:
        """
        Returns info about queue and packages, **not** about files, see `get_queue_data`
        or `get_package_data` instead.

        :return: list of `PackageData`
        """
        return [
            PackageData(
                pid=pack["id"],
                name=pack["name"],
                folder=pack["folder"],
                site=pack["site"],
                password=pack["password"],
                dest=pack["queue"],
                order=pack["order"],
                linksdone=pack["linksdone"],
                sizedone=pack["sizedone"],
                sizetotal=pack["sizetotal"],
                linkstotal=pack["linkstotal"],
            )
            for pack in self.pyload.files.get_info_data(Destination.QUEUE).values()
        ]

    @legacy("getQueueData")
    @permission(Perms.LIST)
    @get
    def get_queue_data(self) -> list[PackageData]:
        """
        Return complete data about everything in queue, this is very expensive use it
        sparely.
        See `get_queue` for alternative.

        :return: list of `PackageData`
        """
        return [
            PackageData(
                pid=pack["id"],
                name=pack["name"],
                folder=pack["folder"],
                site=pack["site"],
                password=pack["password"],
                dest=pack["queue"],
                order=pack["order"],
                linksdone=pack["linksdone"],
                sizedone=pack["sizedone"],
                sizetotal=pack["sizetotal"],
                links=[self._convert_py_file(x) for x in pack["links"].values()],
            )
            for pack in self.pyload.files.get_complete_data(Destination.QUEUE).values()
        ]

    @legacy("getCollector")
    @permission(Perms.LIST)
    @get
    def get_collector(self) -> list[PackageData]:
        """
        same as `get_queue` for collector.

        :return: list of `PackageData`
        """
        return [
            PackageData(
                pid=pack["id"],
                name=pack["name"],
                folder=pack["folder"],
                site=pack["site"],
                password=pack["password"],
                dest=pack["queue"],
                order=pack["order"],
                linksdone=pack["linksdone"],
                sizedone=pack["sizedone"],
                sizetotal=pack["sizetotal"],
                linkstotal=pack["linkstotal"],
            )
            for pack in self.pyload.files.get_info_data(Destination.COLLECTOR).values()
        ]

    @legacy("getCollectorData")
    @permission(Perms.LIST)
    @get
    def get_collector_data(self) -> list[PackageData]:
        """
        same as `get_queue_data` for collector.

        :return: list of `PackageData`
        """
        return [
            PackageData(
                pid=pack["id"],
                name=pack["name"],
                folder=pack["folder"],
                site=pack["site"],
                password=pack["password"],
                dest=pack["queue"],
                order=pack["order"],
                linksdone=pack["linksdone"],
                sizedone=pack["sizedone"],
                sizetotal=pack["sizetotal"],
                links=[self._convert_py_file(x) for x in pack["links"].values()],
            )
            for pack in self.pyload.files.get_complete_data(
                Destination.COLLECTOR
            ).values()
        ]

    @legacy("addFiles")
    @permission(Perms.ADD)
    @post
    def add_files(self, package_id: int, links: list[str]) -> None:
        """
        Adds files to specific package.

        :param package_id: package id
        :param links: list of urls
        """
        self.pyload.files.add_links(links, int(package_id))

        self.pyload.log.info(
            self._("Added {count:d} links to package #{package:d} ").format(
                count=len(links), package=package_id
            )
        )
        self.pyload.files.save()

    @legacy("pushToQueue")
    @permission(Perms.MODIFY)
    @post
    def push_to_queue(self, package_id: int) -> None:
        """
        Moves package from Collector to Queue.

        :param package_id: package id
        """
        self.pyload.files.set_package_location(package_id, Destination.QUEUE)

    @legacy("pullFromQueue")
    @permission(Perms.MODIFY)
    @post
    def pull_from_queue(self, package_id: int) -> None:
        """
        Moves package from Queue to Collector.

        :param package_id: package id
        """
        self.pyload.files.set_package_location(package_id, Destination.COLLECTOR)

    @legacy("restartPackage")
    @permission(Perms.MODIFY)
    @post
    def restart_package(self, package_id: int) -> None:
        """
        Restarts a package, resets every containing files.

        :param package_id: package id
        """
        self.pyload.files.restart_package(int(package_id))

    @legacy("restartFile")
    @permission(Perms.MODIFY)
    @post
    def restart_file(self, file_id: int) -> None:
        """
        Resets file status, so it will be downloaded again.

        :param file_id:  file id
        """
        self.pyload.files.restart_file(int(file_id))

    @legacy("recheckPackage")
    @permission(Perms.MODIFY)
    @post
    def recheck_package(self, package_id: int) -> None:
        """
        Probes online status of all files in a package, also a default action when
        package is added.

        :param package_id:
        :return:
        """
        self.pyload.files.recheck_package(int(package_id))

    @legacy("stopAllDownloads")
    @permission(Perms.MODIFY)
    @post
    def stop_all_downloads(self) -> None:
        """
        Aborts all running downloads.
        """
        pyfiles = list(self.pyload.files.cache.values())
        for pyfile in pyfiles:
            pyfile.abort_download()

    @legacy("stopDownloads")
    @permission(Perms.MODIFY)
    @post
    def stop_downloads(self, file_ids: list[int]) -> None:
        """
        Aborts specific downloads.

        :param file_ids: list of file ids
        :return:
        """
        pyfiles = list(self.pyload.files.cache.values())
        for pyfile in pyfiles:
            if pyfile.id in file_ids:
                pyfile.abort_download()

    @legacy("setPackageName")
    @permission(Perms.MODIFY)
    @post
    def set_package_name(self, package_id: int, name: str) -> None:
        """
        Renames a package.

        :param package_id: package id
        :param name: new package name
        """
        pack = self.pyload.files.get_package(package_id)
        pack.name = name
        pack.sync()

    @legacy("movePackage")
    @permission(Perms.MODIFY)
    @post
    def move_package(self, destination: Destination, package_id: int) -> None:
        """
        Set a new package location.

        :param destination: `Destination`
        :param package_id: package id
        """
        try:
            dest = Destination(destination)
        except ValueError:
            pass
        else:
            self.pyload.files.set_package_location(package_id, dest)

    @legacy("moveFiles")
    @permission(Perms.MODIFY)
    @post
    def move_files(self, file_ids: list[int], package_id: int) -> None:
        """
        Move multiple files to another package.

        :param file_ids: list of file ids
        :param package_id: destination package
        :return:
        """
        # TODO: implement
        pass

    @legacy("uploadContainer")
    @permission(Perms.ADD)
    @post
    def upload_container(self, filename: str, data: bytes) -> None:
        """
        Uploads and adds a container file to pyLoad.

        :param filename: file name - extension is important, so it can correctly decrypt
        :param data: file content
        """
        with open(
            os.path.join(
                self.pyload.config.get("general", "storage_folder"), "tmp_" + filename
            ),
            "wb",
        ) as th:
            th.write(data)

        self.add_package(th.name, [th.name], Destination.COLLECTOR)

    @legacy("orderPackage")
    @permission(Perms.MODIFY)
    @post
    def order_package(self, package_id: int, position: int) -> None:
        """
        Gives a package a new position.

        :param package_id: package id
        :param position:
        """
        self.pyload.files.reorder_package(package_id, position)

    @legacy("orderFile")
    @permission(Perms.MODIFY)
    @post
    def order_file(self, file_id: int, position: int) -> None:
        """
        Gives a new position to a file within its package.

        :param file_id: file id
        :param position:
        """
        self.pyload.files.reorder_file(file_id, position)

    @legacy("setPackageData")
    @permission(Perms.MODIFY)
    @post
    def set_package_data(self, package_id: int, data: dict[str, Any]) -> None:
        """
        Allows to modify several package attributes.

        :param package_id: package id
        :param data: dict that maps attribute to desired value
        """
        p = self.pyload.files.get_package(package_id)
        if not p:
            raise PackageDoesNotExists(package_id)

        for key, value in data.items():
            if key == "id":
                continue
            setattr(p, key, value)

        p.sync()
        self.pyload.files.save()

    @legacy("deleteFinished")
    @permission(Perms.DELETE)
    @post
    def delete_finished(self) -> list[int]:
        """
        Deletes all finished files and completely finished packages.

        :return: list of deleted package ids
        """
        return self.pyload.files.delete_finished_links()

    @legacy("restartFailed")
    @permission(Perms.MODIFY)
    @post
    def restart_failed(self) -> None:
        """
        Restarts all failed failes.
        """
        self.pyload.files.restart_failed()

    @legacy("getPackageOrder")
    @permission(Perms.LIST)
    @get
    def get_package_order(self, destination: Destination) -> dict[int, int]:
        """
        Returns information about package order.

        :param destination: `Destination`
        :return: dict mapping order to package id
        """
        packages = self.pyload.files.get_info_data(Destination(destination))
        order = {}

        for package_id in packages:
            pack = self.pyload.files.get_package_data(int(package_id))
            while pack["order"] in order.keys():  #: just in case
                pack["order"] += 1
            order[pack["order"]] = pack["id"]
        return order

    @legacy("getFileOrder")
    @permission(Perms.LIST)
    @get
    def get_file_order(self, package_id: int) -> dict[int, int]:
        """
        Information about file order within package.

        :param package_id:
        :return: dict mapping order to file id
        """
        raw_data = self.pyload.files.get_package_data(int(package_id))
        order = {}
        for file_id, pyfile in raw_data["links"].items():
            while pyfile["order"] in order.keys():  #: just in case
                pyfile["order"] += 1
            order[pyfile["order"]] = pyfile["id"]
        return order

    @legacy("isCaptchaWaiting")
    @permission(Perms.STATUS)
    @get
    def is_captcha_waiting(self) -> bool:
        """
        Indicates whether a captcha task is available.

        :return: bool
        """
        self.pyload.last_client_connected = time.time()
        task = self.pyload.captcha_manager.get_task()
        return task is not None

    @legacy("getCaptchaTask")
    @permission(Perms.STATUS)
    @get
    def get_captcha_task(self, exclusive: bool = False) -> CaptchaTask:
        """
        Returns a captcha task.

        :param exclusive: unused
        :return: `CaptchaTask`
        """
        self.pyload.last_client_connected = time.time()
        task = self.pyload.captcha_manager.get_task()
        if task:
            task.set_waiting_for_user(exclusive=exclusive)
            captcha_data, captcha_type, result_type = task.get_captcha()
            t = CaptchaTask(tid=int(task.id),
                            data=captcha_data,
                            type=captcha_type,
                            result_type=result_type)
            return t
        else:
            return CaptchaTask(tid=-1)

    @legacy("getCaptchaTaskStatus")
    @permission(Perms.STATUS)
    @get
    def get_captcha_task_status(self, tid: int) -> str:
        """
        Get information about captcha task.

        :param tid: task id
        :return: string
        """
        self.pyload.last_client_connected = time.time()
        t = self.pyload.captcha_manager.get_task_by_id(tid)
        return t.get_status() if t else ""

    @legacy("setCaptchaResult")
    @permission(Perms.STATUS)
    @post
    def set_captcha_result(self, tid: int, result: str) -> None:
        """
        Set result for a captcha task.

        :param tid: task id
        :param result: captcha result
        """
        self.pyload.last_client_connected = time.time()
        task = self.pyload.captcha_manager.get_task_by_id(tid)
        if task:
            task.set_result(result)
            self.pyload.captcha_manager.remove_task(task)

    @legacy("getEvents")
    @permission(Perms.STATUS)
    @get
    def get_events(self, uuid: str) -> list[EventInfo]:
        """
        Lists occurred events, may be affected to changes in the future.

        :param uuid:
        :return: list of `EventInfo`
        """
        events = self.pyload.event_manager.get_events(uuid)
        new_events = []

        def conv_dest(d):
            return (Destination.QUEUE if d == "queue" else Destination.COLLECTOR).value

        for e in events:
            event = EventInfo(eventname=e[0])
            if e[0] in ("update", "remove", "insert"):
                event.id = e[3]
                event.type = (
                    ElementType.PACKAGE if e[2] == "pack" else ElementType.FILE
                ).value
                event.destination = conv_dest(e[1])
            elif e[0] == "order":
                if e[1]:
                    event.id = e[1]
                    event.type = (
                        ElementType.PACKAGE if e[2] == "pack" else ElementType.FILE
                    )
                    event.destination = conv_dest(e[3])
            elif e[0] == "reload":
                event.destination = conv_dest(e[1])
            new_events.append(event)
        return new_events

    @legacy("getAccounts")
    @permission(Perms.ACCOUNTS)
    @get
    def get_accounts(self, refresh: bool) -> list[AccountInfo]:
        """
        Get information about all entered accounts.

        :param refresh: reload account info
        :return: list of `AccountInfo`
        """
        accs = self.pyload.account_manager.get_account_infos(False, refresh)
        accounts = []
        for group in accs.values():
            accounts.extend(
                [
                    AccountInfo(
                        validuntil=acc["validuntil"],
                        login=acc["login"],
                        options=acc["options"],
                        valid=acc["valid"],
                        trafficleft=acc["trafficleft"],
                        premium=acc["premium"],
                        type=acc["type"],
                    )
                    for acc in group
                ]
            )
        return accounts

    @legacy("getAccountTypes")
    @permission(Perms.ANY)
    @get
    def get_account_types(self) -> list[str]:
        """
        All available account types.

        :return: list
        """
        return list(self.pyload.account_manager.accounts.keys())

    @legacy("updateAccount")
    @permission(Perms.ACCOUNTS)
    @post
    def update_account(self, plugin: str, account: str, password: Optional[str] = None, options: Optional[dict[str, Any]] = None) -> None:
        """
        Changes pw/options for specific account.
        """
        options = options or {}
        self.pyload.account_manager.update_account(plugin, account, password, options)

    @legacy("removeAccount")
    @permission(Perms.ACCOUNTS)
    @post
    def remove_account(self, plugin: str, account: str) -> None:
        """
        Remove account from pyload.

        :param plugin: pluginname
        :param account: accountname
        """
        self.pyload.account_manager.remove_account(plugin, account)

    @legacy("checkAuth")
    @get
    def check_auth(self, username: str, password: str) -> dict[str, Any]:
        """
        Check authentication and returns details.

        :param username:
        :param password:
        :return: dict with info, empty when login is incorrect
        """
        return self.pyload.db.check_auth(username, password)

    @get
    def user_exists(self, username: str) -> bool:
        """
        Check if a user actually exists in the database.

        :param username:
        :return: boolean
        """
        return self.pyload.db.user_exists(username)

    @legacy("isAuthorized")
    @post
    def is_authorized(self, func_name: str, userdata: dict[str, Any]) -> bool:
        """
        checks if the user is authorized for specific method.

        :param func_name: function name
        :param userdata: dictionary of user data
        :return: boolean
        """
        if userdata["role"] == Role.ADMIN:
            return True
        elif func_name in perm_map and has_permission(userdata["permission"], perm_map[func_name]):
            return True
        else:
            return False

    @permission(Perms.SETTINGS)
    @get
    def get_userdir(self) -> str:
        return os.path.realpath(self.pyload.userdir)

    @permission(Perms.SETTINGS)
    @get
    def get_cachedir(self) -> str:
        return os.path.realpath(self.pyload.tempdir)

    #: Old API
    @permission(Perms.ANY)
    @get
    def getUserData(self, username: str, password: str) -> OldUserData:
        """
        similar to `check_auth` but returns UserData type.
        """
        user = self.check_auth(username, password)
        if user:
            return OldUserData(
                name=user["name"],
                email=user["email"],
                role=user["role"],
                permission=user["permission"],
                template_name=user["template"],
            )
        else:
            return OldUserData()

    @permission(Perms.ANY)
    @get
    def get_userdata(self, username: str, password: str) -> UserData:
        """
        similar to `check_auth` but returns UserData pe.
        """
        user = self.check_auth(username, password)
        if user:
            return UserData(
                id=user["id"],
                name=user["name"],
                email=user["email"],
                role=user["role"],
                permission=user["permission"],
                template=user["template"],
            )
        else:
            return UserData()

    #: Old API
    @get
    def getAllUserData(self) -> dict[str, OldUserData]:
        """
        returns all known user and info.
        """
        res = {}
        for user_id, data in self.pyload.db.get_all_user_data().items():
            res[data["name"]] = OldUserData(
                name=data["name"],
                email=data["email"],
                role=data["role"],
                permission=data["permission"],
                template_name=data["template"],
            )

        return res

    @get
    def get_all_userdata(self) -> dict[int, UserData]:
        """
        returns all known user and info.
        """
        res = {}
        for user_id, data in self.pyload.db.get_all_user_data().items():
            res[user_id] = UserData(
                id=user_id,
                name=data["name"],
                email=data["email"],
                role=data["role"],
                permission=data["permission"],
                template=data["template"],
            )
        return res

    @legacy("getServices")
    @permission(Perms.STATUS)
    @get
    def get_services(self) -> dict[str, dict[str, str]]:
        """
        A dict of available services, these can be defined by addon plugins.

        :return: dict with this style: {"plugin": {"method": "description"}}
        """
        data = {}
        for plugin, funcs in self.pyload.addon_manager.rpc_methods.items():
            data[plugin] = funcs

        return data

    @legacy("hasService")
    @permission(Perms.STATUS)
    @get
    def has_service(self, plugin: str, func_name: str) -> bool:
        """
        Checks whether a service is available.

        :param plugin:
        :param func_name:
        :return: bool
        """
        cont = self.pyload.addon_manager.rpc_methods
        return plugin in cont and func_name in cont[plugin]

    @permission(Perms.STATUS)
    @post
    def service_call(self, service_name: str, arguments: Optional[list[Any]], parse_arguments: bool = False) -> str:
        """
        Calls a service (a method in addon plugin).

        :param service_name:
        :param arguments:
        :param parse_arguments:
        :return: result
        :raises: ServiceDoesNotExists, when it's not available
        :raises: ServiceException, when an exception was raised
        """
        try:
            plugin, func = service_name.split(".")
        except ValueError:
            raise ServiceDoesNotExists()

        info = ServiceCall(
            plugin=plugin,
            func=func,
            arguments=arguments,
            parse_arguments=parse_arguments
        )
        return self._call(info)

    @permission(Perms.STATUS)
    def _call(self, info: ServiceCall) -> str:
        """
        Calls a service (a method in addon plugin).

        :param info: `ServiceCall`
        :return: result
        :raises: ServiceDoesNotExists, when it's not available
        :raises: ServiceException, when an exception was raised
        """
        plugin = info.plugin
        func = info.func
        args = info.arguments
        parse = info.parse_arguments

        if not self.has_service(plugin, func):
            raise ServiceDoesNotExists(plugin, func)

        try:
            ret = self.pyload.addon_manager.call_rpc(plugin, func, args, parse)
            return str(ret)
        except Exception as exc:
            raise ServiceException(exc)

    @legacy("getAllInfo")
    @permission(Perms.STATUS)
    @get
    def get_all_info(self) -> dict[str, dict[str, str]]:
        """
        Returns all information stored by addon plugins. Values are always strings.

        :return: {"plugin": {"name": value } }
        """
        return self.pyload.addon_manager.get_all_info()

    @legacy("getInfoByPlugin")
    @permission(Perms.STATUS)
    @get
    def get_info_by_plugin(self, plugin: str) -> dict[str, str]:
        """
        Returns information stored by a specific plugin.

        :param plugin: pluginname
        :return: dict of attr names mapped to value {"name": value}
        """
        return self.pyload.addon_manager.get_info(plugin)

    @post
    def add_user(self, user: str, newpw: str, role: int = 0, perms: int = 0) -> bool:
        """
        creates new user login.
        """
        return self.pyload.db.add_user(user, newpw, role, perms)

    @post
    def remove_user(self, user: str) -> bool:
        """
        deletes a user login.
        """
        self.pyload.db.remove_user(user)
        # TODO: fix db method to return bool
        return True

    @legacy("changePassword")
    @post
    def change_password(self, user: str, oldpw: str, newpw: str) -> bool:
        """
        changes password for specific user.
        """
        return self.pyload.db.change_password(user, oldpw, newpw)

    @legacy("setUserPermission")
    @post
    def set_user_permission(self, user: str, permission: int, role: int) -> None:
        self.pyload.db.set_permission(user, permission)
        self.pyload.db.set_role(user, role)
