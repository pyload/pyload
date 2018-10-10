# -*- coding: utf-8 -*-

from ..internal.Addon import Addon


class EventMapper(Addon):
    __name__ = "EventMapper"
    __type__ = "hook"
    __version__ = "0.02"
    __status__ = "testing"

    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Map old events to new events"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    def activate(self, *args):
        self.manager.dispatchEvent("activate", *args)

    def exit(self, *args):
        self.manager.dispatchEvent("exit", *args)

    def config_changed(self, *args):
        self.manager.dispatchEvent("config_changed", *args)

    def all_downloads_finished(self, *args):
        self.manager.dispatchEvent("all_downloads_finished", *args)

    def all_downloads_processed(self, *args):
        self.manager.dispatchEvent("all_downloads_processed", *args)

    def links_added(self, *args):
        self.manager.dispatchEvent("links_added", *args)

    def download_preparing(self, *args):
        self.manager.dispatchEvent("download_preparing", *args)

    def download_finished(self, *args):
        self.manager.dispatchEvent("download_finished", *args)

    def download_failed(self, *args):
        self.manager.dispatchEvent("download_failed", *args)

    def package_deleted(self, *args):
        self.manager.dispatchEvent("package_deleted", *args)

    def package_finished(self, *args):
        self.manager.dispatchEvent("package_finished", *args)

    def before_reconnect(self, *args):
        self.manager.dispatchEvent("before_reconnect", *args)

    def after_reconnect(self, *args):
        self.manager.dispatchEvent("after_reconnect", *args)

    def captcha_task(self, *args):
        self.manager.dispatchEvent("captcha_task", *args)

    def captcha_correct(self, *args):
        self.manager.dispatchEvent("captcha_correct", *args)

    def captcha_invalid(self, *args):
        self.manager.dispatchEvent("captcha_invalid", *args)
