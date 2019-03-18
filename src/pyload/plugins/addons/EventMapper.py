# -*- coding: utf-8 -*-

from ..base.addon import BaseAddon


class EventMapper(BaseAddon):
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
        self.m.dispatch_event("activate", *args)

    def exit(self, *args):
        self.m.dispatch_event("exit", *args)

    def config_changed(self, *args):
        self.m.dispatch_event("config_changed", *args)

    def all_downloads_finished(self, *args):
        self.m.dispatch_event("all_downloads_finished", *args)

    def all_downloads_processed(self, *args):
        self.m.dispatch_event("all_downloads_processed", *args)

    def links_added(self, *args):
        self.m.dispatch_event("links_added", *args)

    def download_preparing(self, *args):
        self.m.dispatch_event("download_preparing", *args)

    def download_finished(self, *args):
        self.m.dispatch_event("download_finished", *args)

    def download_failed(self, *args):
        self.m.dispatch_event("download_failed", *args)

    def package_deleted(self, *args):
        self.m.dispatch_event("package_deleted", *args)

    def package_finished(self, *args):
        self.m.dispatch_event("package_finished", *args)

    def before_reconnect(self, *args):
        self.m.dispatch_event("before_reconnect", *args)

    def after_reconnect(self, *args):
        self.m.dispatch_event("after_reconnect", *args)

    def captcha_task(self, *args):
        self.m.dispatch_event("captcha_task", *args)

    def captcha_correct(self, *args):
        self.m.dispatch_event("captcha_correct", *args)

    def captcha_invalid(self, *args):
        self.m.dispatch_event("captcha_invalid", *args)
