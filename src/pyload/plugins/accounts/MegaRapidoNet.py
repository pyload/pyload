# -*- coding: utf-8 -*-

import re
import time
from datetime import timedelta

from ..base.multi_account import MultiAccount


class MegaRapidoNet(MultiAccount):
    __name__ = "MegaRapidoNet"
    __type__ = "account"
    __version__ = "0.10"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter downloaders to use", "all"),
        ("mh_list", "str", "Downloader list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
    ]

    __description__ = """MegaRapido.net account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Kagenoshin", "kagenoshin@gmx.ch")]

    VALID_UNTIL_PATTERN = r'<\s*?div[^>]*?class\s*?=\s*?[\'"]premium_index[\'"].*?>[^<]*?<[^>]*?b.*?>\s*?TEMPO\s*?PREMIUM.*?<[^>]*?/b.*?>\s*?(\d*)[^\d]*?DIAS[^\d]*?(\d*)[^\d]*?HORAS[^\d]*?(\d*)[^\d]*?MINUTOS[^\d]*?(\d*)[^\d]*?SEGUNDOS'
    USER_ID_PATTERN = r'<\s*?div[^>]*?class\s*?=\s*?["\']checkbox_compartilhar["\'].*?>.*?<\s*?input[^>]*?name\s*?=\s*?["\']usar["\'].*?>.*?<\s*?input[^>]*?name\s*?=\s*?["\']user["\'][^>]*?value\s*?=\s*?["\'](.*?)\s*?["\']'

    def grab_hosters(self, user, password, data):
        hosters = {
            "1fichier": [],  #: leave it there are so many possible addresses?
            "1st-files": ["1st-files.com"],
            "2shared": ["2shared.com"],
            "4shared": ["4shared.com", "4shared-china.com"],
            "asfile": ["http://asfile.com/"],
            "bitshare": ["bitshare.com"],
            "brupload": ["brupload.net"],
            "crocko": ["crocko.com", "easy-share.com"],
            "dailymotion": ["dailymotion.com"],
            "depfile": ["depfile.com"],
            "depositfiles": ["depositfiles.com", "dfiles.eu"],
            "dizzcloud": ["dizzcloud.com"],
            "dl.dropbox": [],
            "extabit": ["extabit.com"],
            "extmatrix": ["extmatrix.com"],
            "facebook": [],
            "file4go": ["file4go.com"],
            "filecloud": ["filecloud.io", "ifile.it", "mihd.net"],
            "filefactory": ["filefactory.com"],
            "fileom": ["fileom.com"],
            "fileparadox": ["fileparadox.in"],
            "filepost": ["filepost.com", "fp.io"],
            "filerio": ["filerio.in", "filerio.com", "filekeen.com"],
            "filesflash": ["filesflash.com"],
            "firedrive": ["firedrive.com", "putlocker.com"],
            "flashx": [],
            "freakshare": ["freakshare.net", "freakshare.com"],
            "gigasize": ["gigasize.com"],
            "hipfile": ["hipfile.com"],
            "junocloud": ["junocloud.me"],
            "letitbit": ["letitbit.net", "shareflare.net"],
            "mediafire": ["mediafire.com"],
            "mega": ["mega.co.nz"],
            "megashares": ["megashares.com"],
            "metacafe": ["metacafe.com"],
            "netload": ["netload.in"],
            "oboom": ["oboom.com"],
            "rapidgator": ["rapidgator.net"],
            "rapidshare": ["rapidshare.com"],
            "rarefile": ["rarefile.net"],
            "ryushare": ["ryushare.com"],
            "sendspace": ["sendspace.com"],
            "turbobit": ["turbobit.net", "unextfiles.com"],
            "uploadable": ["uploadable.ch"],
            "uploadbaz": ["uploadbaz.com"],
            "uploaded": ["uploaded.to", "uploaded.net", "ul.to"],
            "uploadhero": ["uploadhero.com"],
            "uploading": ["uploading.com"],
            "uptobox": ["uptobox.com"],
            "xvideos": ["xvideos.com"],
            "youtube": ["youtube.com"],
        }

        hoster_list = []

        for item in hosters.values():
            hoster_list.extend(item)

        return hoster_list

    def grab_info(self, user, password, data):
        validuntil = None
        trafficleft = None
        premium = False

        html = self.load("http://megarapido.net/gerador")

        validuntil = re.search(self.VALID_UNTIL_PATTERN, html)
        if validuntil:
            #: Hier weitermachen!!! (müssen umbedingt die zeit richtig machen damit! (sollte aber möglich))
            validuntil = (
                time.time()
                + timedelta(hours=int(validuntil.group(1)) * 24).total_seconds()
                + timedelta(hours=int(validuntil.group(2))).total_seconds()
                + timedelta(minutes=int(validuntil.group(3))).total_seconds()
                + int(validuntil.group(4))
            )
            trafficleft = -1
            premium = True

        return {
            "validuntil": validuntil,
            "trafficleft": trafficleft,
            "premium": premium,
        }

    def signin(self, user, password, data):
        self.load("http://megarapido.net/login")
        self.load(
            "http://megarapido.net/painel_user/ajax/logar.php",
            post={"login": user, "senha": password},
        )

        html = self.load("http://megarapido.net/gerador")

        if "sair" not in html.lower():
            self.fail_login()
        else:
            m = re.search(self.USER_ID_PATTERN, html)
            if m is not None:
                data["uid"] = m.group(1)
            else:
                self.fail_login("Couldn't find the user ID")
