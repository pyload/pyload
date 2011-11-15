# -*- coding: utf-8 -*-

import re
from time import sleep

from module.plugins.Crypter import Crypter
from module.lib.BeautifulSoup import BeautifulSoup
from module.unescape import unescape

class SerienjunkiesOrg(Crypter):
    __name__ = "SerienjunkiesOrg"
    __type__ = "container"
    __pattern__ = r"http://.*?serienjunkies.org/.*?"
    __version__ = "0.31"
    __config__ = [("preferredHoster", "str", "preferred hoster",
                   "RapidshareCom,UploadedTo,NetloadIn,FilefactoryCom,FreakshareNet,FilebaseTo,MegauploadCom,HotfileCom,DepositfilesCom,EasyshareCom,KickloadCom")
        ,
        ("changeName", "bool", "Take SJ.org episode name", "True")]
    __description__ = """serienjunkies.org Container Plugin"""
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")

    def setup(self):
        self.hosterMap = {
            "rc": "RapidshareCom",
            "ff": "FilefactoryCom",
            "ut": "UploadedTo",
            "ul": "UploadedTo",
            "nl": "NetloadIn",
            "fs": "FreakshareNet",
            "fb": "FilebaseTo",
            "mu": "MegauploadCom",
            "hf": "HotfileCom",
            "df": "DepositfilesCom",
            "es": "EasyshareCom",
            "kl": "KickloadCom",
            "fc": "FilesonicCom",
            }
        self.hosterMapReverse = dict((v, k) for k, v in self.hosterMap.iteritems())

        self.multiDL = False
        self.limitDL = 4

    def getSJSrc(self, url):
        src = self.req.load(str(url))
        if not src.find("Enter Serienjunkies") == -1:
            sleep(1)
            src = self.req.load(str(url))
        return src

    def handleShow(self, url):
        src = self.getSJSrc(url)
        soup = BeautifulSoup(src)
        nav = soup.find("div", attrs={"id": "scb"})
        for a in nav.findAll("a"):
            self.packages.append((unescape(a.text), [a["href"]], unescape(a.text)))

    def handleSeason(self, url):
        src = self.getSJSrc(url)
        soup = BeautifulSoup(src)
        post = soup.find("div", attrs={"class": "post-content"})
        ps = post.findAll("p")
        hosterPattern = re.compile("^http://download\.serienjunkies\.org/f-.*?/([rcfultns]{2})_.*?\.html$")
        preferredHoster = self.getConfig("preferredHoster").split(",")
        self.log.debug("Preferred hoster: %s" % ", ".join(preferredHoster))
        groups = {}
        gid = -1
        seasonName = unescape(soup.find("a", attrs={"rel": "bookmark"}).string)
        for p in ps:
            if re.search("<strong>Dauer|<strong>Sprache|<strong>Format", str(p)):
                var = p.findAll("strong")
                opts = {"Dauer": "", "Uploader": "", "Sprache": "", "Format": "", u"Größe": ""}
                for v in var:
                    n = unescape(v.string)
                    n = n.strip()
                    n = re.sub(r"^([:]?)(.*?)([:]?)$", r'\2', n)
                    if n.strip() not in opts:
                        continue
                    val = v.nextSibling
                    if not val:
                        continue
                    val = val.encode("utf-8")
                    val = unescape(val)
                    val = val.replace("|", "").strip()
                    val = val.strip()
                    val = re.sub(r"^([:]?)(.*?)([:]?)$", r'\2', val)
                    opts[n.strip()] = val.strip()
                gid += 1
                groups[gid] = {}
                groups[gid]["ep"] = []
                groups[gid]["opts"] = opts
            elif re.search("<strong>Download:", str(p)):
                links1 = p.findAll("a", attrs={"href": hosterPattern})
                links2 = p.findAll("a", attrs={"href": re.compile("^http://serienjunkies.org/safe/.*$")})
                for link in links1 + links2:
                    groups[gid]["ep"].append(link["href"])
        for g in groups.values():
            links = []
            linklist = g["ep"]
            package = "%s (%s, %s)" % (seasonName, g["opts"]["Format"], g["opts"]["Sprache"])
            linkgroups = {}
            for link in linklist:
                key = re.sub("^http://download\.serienjunkies\.org/f-.*?/(.{2})_", "", link)
                if key not in linkgroups:
                    linkgroups[key] = []
                linkgroups[key].append(link)
            for group in linkgroups.values():
                for pHoster in preferredHoster:
                    hmatch = False
                    for link in group:
                        m = hosterPattern.match(link)
                        if m:
                            if pHoster == self.hosterMap[m.group(1)]:
                                links.append(link)
                                hmatch = True
                                break
                    if hmatch:
                        break
            self.packages.append((package, links, package))

    def handleEpisode(self, url):
        src = self.getSJSrc(url)
        if not src.find(
            "Du hast das Download-Limit &uuml;berschritten! Bitte versuche es sp&auml;ter nocheinmal.") == -1:
            self.fail(_("Downloadlimit reached"))
        else:
            soup = BeautifulSoup(src)
            form = soup.find("form")
            h1 = soup.find("h1")
            packageName = h1.text
            if h1.get("class") == "wrap":
                captchaTag = soup.find(attrs={"src": re.compile("^/secure/")})
                if not captchaTag:
                    sleep(1)
                    self.retry()

                captchaUrl = "http://download.serienjunkies.org" + captchaTag["src"]
                result = self.decryptCaptcha(str(captchaUrl), imgtype="png")
                sinp = form.find(attrs={"name": "s"})

                self.req.lastURL = str(url)
                sj = self.load(str(url), post={'s': sinp["value"], 'c': result, 'action': "Download"})

                soup = BeautifulSoup(sj)
            rawLinks = soup.findAll(attrs={"action": re.compile("^http://download.serienjunkies.org/")})

            if not len(rawLinks) > 0:
                sleep(1)
                self.retry()
                return

            self.correctCaptcha()

            links = []
            for link in rawLinks:
                frameUrl = link["action"].replace("/go-", "/frame/go-")
                links.append(self.handleFrame(frameUrl))

            # thx gartd6oDLobo
            if not self.getConfig("changeName"):
                packageName = self.pyfile.package().name

            self.packages.append((packageName, links, packageName))

    def handleOldStyleLink(self, url):
        sj = self.req.load(str(url))
        soup = BeautifulSoup(sj)
        form = soup.find("form", attrs={"action": re.compile("^http://serienjunkies.org")})
        captchaTag = form.find(attrs={"src": re.compile("^/safe/secure/")})
        captchaUrl = "http://serienjunkies.org" + captchaTag["src"]
        result = self.decryptCaptcha(str(captchaUrl))
        url = form["action"]
        sinp = form.find(attrs={"name": "s"})

        self.req.load(str(url), post={'s': sinp["value"], 'c': result, 'dl.start': "Download"}, cookies=False,
            just_header=True)
        decrypted = self.req.lastEffectiveURL
        if decrypted == str(url):
            self.retry()
        self.packages.append((self.pyfile.package().name, [decrypted], self.pyfile.package().folder))

    def handleFrame(self, url):
        self.req.load(str(url))
        return self.req.lastEffectiveURL

    def decrypt(self, pyfile):
        showPattern = re.compile("^http://serienjunkies.org/serie/(.*)/$")
        seasonPattern = re.compile("^http://serienjunkies.org/.*?/(.*)/$")
        episodePattern = re.compile("^http://download.serienjunkies.org/f-.*?.html$")
        oldStyleLink = re.compile("^http://serienjunkies.org/safe/(.*)$")
        framePattern = re.compile("^http://download.serienjunkies.org/frame/go-.*?/$")
        url = pyfile.url
        if framePattern.match(url):
            self.packages.append((self.pyfile.package().name, [self.handleFrame(url)], self.pyfile.package().name))
        elif episodePattern.match(url):
            self.handleEpisode(url)
        elif oldStyleLink.match(url):
            self.handleOldStyleLink(url)
        elif showPattern.match(url):
            self.handleShow(url)
        elif seasonPattern.match(url):
            self.handleSeason(url)
