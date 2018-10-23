# -*- coding: utf-8 -*-

from pyload.plugins.internal.addon import Addon


class EventMapper(Addon):
    __name__ = "EventMapper"
    __type__ = "addon"
    __version__ = "0.02"
    __status__ = "testing"

    __pyload_version__ = "0.5"

    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Map old events to new events"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    def activate(self, *args):
        self.m.dispatchEvent("activate", *args)

    def exit(self, *args):
        self.m.dispatchEvent("exit", *args)

    def config_changed(self, *args):
        self.m.dispatchEvent("config_changed", *args)

    def all_downloads_finished(self, *args):
        self.m.dispatchEvent("all_downloads_finished", *args)

    def all_downloads_processed(self, *args):
        self.m.dispatchEvent("all_downloads_processed", *args)

    def links_added(self, *args):
        self.m.dispatchEvent("links_added", *args)

    def download_preparing(self, *args):
        self.m.dispatchEvent("download_preparing", *args)

    def download_finished(self, *args):
        self.m.dispatchEvent("download_finished", *args)

    def download_failed(self, *args):
        self.m.dispatchEvent("download_failed", *args)

    def package_deleted(self, *args):
        self.m.dispatchEvent("package_deleted", *args)

    def package_finished(self, *args):
        self.m.dispatchEvent("package_finished", *args)

    def before_reconnect(self, *args):
        self.m.dispatchEvent("before_reconnect", *args)

    def after_reconnect(self, *args):
        self.m.dispatchEvent("after_reconnect", *args)

    def captcha_task(self, *args):
        self.m.dispatchEvent("captcha_task", *args)

    def captcha_correct(self, *args):
        self.m.dispatchEvent("captcha_correct", *args)

    def captcha_invalid(self, *args):
        self.m.dispatchEvent("captcha_invalid", *args)
