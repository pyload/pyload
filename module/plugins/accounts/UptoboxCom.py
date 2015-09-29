# -*- coding: utf-8 -*-

from module.plugins.internal.XFSAccount import XFSAccount


class UptoboxCom(XFSAccount):
    __name__    = "UptoboxCom"
    __type__    = "account"
    __version__ = "0.13"
    __status__  = "testing"

    __description__ = """Uptobox.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("benbox69", "dev@tollet.me")]


    PLUGIN_DOMAIN = "uptobox.com"
    PLUGIN_URL    = "https://uptobox.com/"
    LOGIN_URL     = "https://login.uptobox.com/logarithme/"
