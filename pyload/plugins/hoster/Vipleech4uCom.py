# -*- coding: utf-8 -*-

import re

from module.plugins.Hoster import Hoster


class Vipleech4uCom(Hoster):
    __name__ = "Vipleech4uCom"
    __version__ = "0.1"
    __type__ = "hoster"
    __pattern__ = r"http://vipleech4u.com/manager.php"
    __description__ = """Vipleech4u.com hoster plugin"""
    __author_name__ = ("Kagenoshin")
    __author_mail__ = ("kagenoshin@gmx.ch")

    FILENAME_PATTERN = re.compile(r'name\s*?=\s*?["\']filename["\'][^>]*?value\s*?=\s*?["\'](.*?)["\']', re.I)
    HOST_PATTERN = re.compile(r'name\s*?=\s*?["\']host["\'][^>]*?value\s*?=\s*?["\'](.*?)["\']', re.I)
    PATH_PATTERN = re.compile(r'name\s*?=\s*?["\']path["\'][^>]*?value\s*?=\s*?["\'](.*?)["\']', re.I)
    REFERER_PATTERN = re.compile(r'name\s*?=\s*?["\']referer["\'][^>]*?value\s*?=\s*?["\'](.*?)["\']', re.I)
    LINK_PATTERN = re.compile(r'name\s*?=\s*?["\']link["\'][^>]*?value\s*?=\s*?["\'](.*?)["\']', re.I)
    COOKIE_PATTERN = re.compile(r'name\s*?=\s*?["\']cookie["\'][^>]*?value\s*?=\s*?["\'](.*?)["\']', re.I)

    def setup(self):
        self.resumeDownload = self.multiDL = True
        self.chunkLimit = 1

    def process(self, pyfile):
        if not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "vipleech4u.com")
            self.fail("No vipleech4u.com account provided")

        self.logDebug("Old URL: %s" % pyfile.url)

        new_url = pyfile.url

        if re.match(self.__pattern__, new_url):
            self.fail("Can't handle vipleech4u links.")

        #upload the link which has to be loaded
        page = self.load('http://vipleech4u.com/generator.php', post={'links': new_url, 'ddl': 'no'})

        #switch to the manager and see what's happening
        page = self.load('http://vipleech4u.com/unrestrict.php', get={'link': new_url, 'premium_acc': 'on'})

        if re.search(r'You have generated maximum links available to you today', page, re.I):
            self.fail('Daily limit reached.')

        filename = self.FILENAME_PATTERN.search(page)
        host = self.HOST_PATTERN.search(page)
        path = self.PATH_PATTERN.search(page)
        referer = self.REFERER_PATTERN.search(page)
        link = self.LINK_PATTERN.search(page)
        cookie = self.COOKIE_PATTERN.search(page)

        #build the post-dictionary
        post_dict = {}

        if filename:
            post_dict.update({'filename': filename.group(1)})
        if host:
            post_dict.update({'host': host.group(1)})
        if path:
            post_dict.update({'path': path.group(1)})
        if referer:
            post_dict.update({'referer': referer.group(1)})
        if link:
            post_dict.update({'link': link.group(1)})
        if cookie:
            post_dict.update({'cookie': cookie.group(1)})

        if not post_dict:
            self.logDebug('Get an empty post_dict. Strange.')

        self.setWait(5)
        self.wait()
        self.logDebug("Unrestricted URL: " + str(post_dict))

        self.download('http://vipleech4u.com/unrestrict.php', post=post_dict, disposition=True)

        check = self.checkDownload({"bad": "<html"})

        if check == "bad":
            self.retry(24, 150, 'Bad file downloaded')
