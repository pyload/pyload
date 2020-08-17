# -*- coding: utf-8 -*-
import re

from ..base.decrypter import BaseDecrypter


class SexuriaCom(BaseDecrypter):
    __name__ = "SexuriaCom"
    __type__ = "decrypter"
    __version__ = "0.15"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?sexuria\.com/(v1/)?(Pornos_Kostenlos_.+?_(\d+)\.html|dl_links_\d+_\d+\.html|id=\d+\&part=\d+\&link=\d+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_subfolder", "bool", "Save package to subfolder", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
    ]

    __description__ = """Sexuria.com decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("NETHead", "NETHead.AT.gmx.DOT.net")]

    #: Constants
    PATTERN_SUPPORTED_CRYPT = (
        r"http://(www\.)?sexuria\.com/(v1/)?Pornos_Kostenlos_.+?_(\d+)\.html"
    )
    PATTERN_SUPPORTED_MAIN = (
        r"http://(www\.)?sexuria\.com/(v1/)?dl_links_\d+_(?P<ID>\d+)\.html"
    )
    PATTERN_SUPPORTED_REDIRECT = (
        r"http://(www\.)?sexuria\.com/out\.php\?id=(?P<ID>\d+)\&part=\d+\&link=\d+"
    )
    PATTERN_TITLE = r"<title> - (?P<TITLE>.*) Sexuria - Kostenlose Pornos - Rapidshare XXX Porn</title>"
    PATTERN_PASSWORD = (
        r'<strong>Passwort: </strong></div></td>.*?bgcolor="#EFEFEF">(?P<PWD>.*?)</td>'
    )
    PATTERN_DL_LINK_PAGE = r'"(dl_links_\d+_\d+\.html)"'
    PATTERN_REDIRECT_LINKS = r'disabled\'" href="(.*)" id'
    LIST_PWDIGNORE = ["Kein Passwort", "-"]

    def decrypt(self, pyfile):
        #: Init
        self.pyfile = pyfile
        self.package = pyfile.package()

        #: Decrypt and add links
        pack_name, self.urls, folder_name, pack_pwd = self.decrypt_links(
            self.pyfile.url
        )
        if pack_pwd:
            self.pyfile.package().password = pack_pwd
        self.packages = [(pack_name, self.urls, folder_name)]

    def decrypt_links(self, url):
        linklist = []
        name = self.package.name
        folder = self.package.folder
        password = None

        if re.match(self.PATTERN_SUPPORTED_MAIN, url, re.I):
            #: Processing main page
            html = self.load(url)
            links = re.findall(self.PATTERN_DL_LINK_PAGE, html, re.I)
            for link in links:
                linklist.append("http://sexuria.com/v1/" + link)

        elif re.match(self.PATTERN_SUPPORTED_REDIRECT, url, re.I):
            #: Processing direct redirect link (out.php), redirecting to main page
            id = re.search(self.PATTERN_SUPPORTED_REDIRECT, url, re.I).group("ID")
            if id:
                linklist.append(
                    "http://sexuria.com/v1/Pornos_Kostenlos_liebe_{}.html".format(id)
                )

        elif re.match(self.PATTERN_SUPPORTED_CRYPT, url, re.I):
            #: Extract info from main file
            id = re.search(self.PATTERN_SUPPORTED_CRYPT, url, re.I).group("ID")
            html = self.load(
                "http://sexuria.com/v1/Pornos_Kostenlos_info_{}.html".format(id)
            )
            #: Webpage title / Package name
            titledata = re.search(self.PATTERN_TITLE, html, re.I)
            if not titledata:
                self.log_warning("No title data found, has site changed?")
            else:
                title = titledata.group("TITLE").strip()
                if title:
                    name = folder = title
                    self.log_debug(
                        "Package info found, name [{}] and folder [{}]".format(
                            name, folder
                        )
                    )
            #: Password
            pwddata = re.search(self.PATTERN_PASSWORD, html, re.I | re.S)
            if not pwddata:
                self.log_warning("No password data found, has site changed?")
            else:
                pwd = pwddata.group("PWD").strip()
                if pwd and pwd not in self.LIST_PWDIGNORE:
                    password = pwd
                    self.log_debug(f"Package info found, password [{password}]")

            #: Process links (dl_link)
            html = self.load(url)
            links = re.findall(self.PATTERN_REDIRECT_LINKS, html, re.I)
            if not links:
                self.log_error(self._("Broken for link: {}").format(link))
            else:
                for link in links:
                    link = link.replace(
                        "http://sexuria.com/", "http://www.sexuria.com/"
                    )
                    finallink = self.load(link, just_header=True)["url"]
                    if not finallink or "sexuria.com/" in finallink:
                        self.log_error(self._("Broken for link: {}").format(link))
                    else:
                        linklist.append(finallink)

        #: Log result
        if not linklist:
            self.fail(self._("Unable to extract links (maybe plugin out of date?)"))
        else:
            for i, link in enumerate(linklist):
                self.log_debug(
                    "Supported link {}/{}: {}".format(i + 1, len(linklist), link)
                )

        #: All done, return to caller
        return name, linklist, folder, password
