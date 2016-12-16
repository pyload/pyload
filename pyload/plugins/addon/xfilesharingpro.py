# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import re

from pyload.plugins.hook import Hook


class XFileSharingPro(Hook):
    __name__ = "XFileSharingPro"
    __version__ = "0.09"
    __type__ = "hook"
    __config__ = [("activated", "bool", "Activated", True),
                  ("loadDefault", "bool", "Include default (built-in) hoster list", True),
                  ("includeList", "str", "Include hosters (comma separated)", ""),
                  ("excludeList", "str", "Exclude hosters (comma separated)", "")]
    __description__ = """XFileSharingPro hook plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    def core_ready(self):
        self.load_pattern()

    def load_pattern(self):
        hosterList = self.get_config_set('includeList')
        excludeList = self.get_config_set('excludeList')

        if self.get_config('loadDefault'):
            hosterList |= set((
                #WORKING HOSTERS:
                "aieshare.com", "asixfiles.com", "banashare.com", "cyberlocker.ch", "eyesfile.co", "eyesfile.com",
                "fileband.com", "filedwon.com", "filedownloads.org", "hipfile.com", "kingsupload.com", "mlfat4arab.com",
                "netuploaded.com", "odsiebie.pl", "q4share.com", "ravishare.com", "uptobox.com", "verzend.be",
                "xvidstage.com", "thefile.me", "sharesix.com", "hostingbulk.com",
                #NOT TESTED:
                "bebasupload.com", "boosterking.com", "divxme.com", "filevelocity.com", "glumbouploads.com",
                "grupload.com", "heftyfile.com", "host4desi.com", "laoupload.com", "linkzhost.com", "movreel.com",
                "rockdizfile.com", "limfile.com", "share76.com", "sharebeast.com", "sharehut.com", "sharerun.com",
                "shareswift.com", "sharingonline.com", "6ybh-upload.com", "skipfile.com", "spaadyshare.com",
                "space4file.com", "uploadbaz.com", "uploadc.com", "uploaddot.com", "uploadfloor.com", "uploadic.com",
                "uploadville.com", "vidbull.com", "zalaa.com", "zomgupload.com", "kupload.org", "movbay.org",
                "multishare.org", "omegave.org", "toucansharing.org", "uflinq.org", "banicrazy.info", "flowhot.info",
                "upbrasil.info", "shareyourfilez.biz", "bzlink.us", "cloudcache.cc", "fileserver.cc", "farshare.to",
                "filemaze.ws", "filehost.ws", "filestock.ru", "moidisk.ru", "4up.im", "100shared.com", "sharesix.com",
                "thefile.me", "filenuke.com", "sharerepo.com", "mightyupload.com",
                #WRONG FILE NAME:
                "sendmyway.com", "upchi.co.il",
                #NOT WORKING:
                "amonshare.com", "imageporter.com", "file4safe.com",
                #DOWN OR BROKEN:
                "ddlanime.com", "fileforth.com", "loombo.com", "goldfile.eu", "putshare.com"
            ))

        hosterList -= (excludeList)
        hosterList -= set(('',))

        if not hosterList:
            self.unload()
            return

        regexp = r"http://(?:[^/]*\.)?(%s)/\w{12}" % ("|".join(sorted(hosterList)).replace('.', '\.'))
        #self.log_debug(regexp)

        dict = self.pyload.pluginmanager.hosterPlugins['XFileSharingPro']
        dict["pattern"] = regexp
        dict["re"] = re.compile(regexp)
        self.log_debug("Pattern loaded - handling %d hosters" % len(hosterList))

    def get_config_set(self, option):
        s = self.get_config(option).lower().replace('|', ',').replace(';', ',')
        return set([x.strip() for x in s.split(',')])

    def unload(self):
        dict = self.pyload.pluginmanager.hosterPlugins['XFileSharingPro']
        dict["pattern"] = r"^unmatchable$"
        dict["re"] = re.compile(r"^unmatchable$")
