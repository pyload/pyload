# -*- coding: utf-8 -*-


class FileDoesNotExists(Exception):
    __slots__ = ["fid"]

    def __init__(self, fid=None):
        self.fid = fid


class PackageDoesNotExists(Exception):
    __slots__ = ["pid"]

    def __init__(self, pid=None):
        self.pid = pid


class ServiceDoesNotExists(Exception):
    __slots__ = ["plugin", "func"]

    def __init__(self, plugin=None, func=None):
        self.plugin = plugin
        self.func = func


class ServiceException(Exception):
    __slots__ = ["msg"]

    def __init__(self, msg=None):
        self.msg = msg
