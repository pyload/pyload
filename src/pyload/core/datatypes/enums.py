# -*- coding: utf-8 -*-

from enum import IntEnum


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
