# -*- coding: utf-8 -*-

import random
import re

from time import sleep

from module.lib.BeautifulSoup import BeautifulSoup

from module.plugins.Crypter import Crypter
from module.unescape import unescape


class SerienjunkiesOrg(Crypter):
    __name__ = "SerienjunkiesOrg"
    __type__ = "crypter"
    __version__ = "0.39"

    __pattern__ = r'http://(?:www\.)?(serienjunkies.org|dokujunkies.org)/.*?'
    __config__ = [("changeNameSJ", "Packagename;Show;Season;Format;Episode", "Take SJ.org name", "Show"),
                  ("changeNameDJ", "Packagename;Show;Format;Episode", "Take DJ.org name", "Show"),
                  ("randomPreferred", "bool", "Randomize Preferred-List", False),
                  ("hosterListMode", "OnlyOne;OnlyPreferred(One);OnlyPreferred(All);All",
                   "Use for hosters (if supported)", "All"),
                  ("hosterList", "str", "Preferred Hoster list (comma separated)",
                   "RapidshareCom,UploadedTo,NetloadIn,FilefactoryCom,FreakshareNet,FilebaseTo,HotfileCom,DepositfilesCom,EasyshareCom,KickloadCom"),
                  ("ignoreList", "str", "Ignored Hoster list (comma separated)", "MegauploadCom")]

    __description__ = """Serienjunkies.org decrypter plugin"""
    __author_name__ = ("mkaay", "godofdream")
    __author_mail__ = ("mkaay@mkaay.de", "soilfiction@gmail.com")


    def setup(self):
        self.multiDL = False

    def getSJSrc(self, url):
        src = self.req.load(str(url))
        if "This website is not available in your country" in src:
            self.fail("Not available in your country")
        if not src.find("Enter Serienjunkies") == -1:
            sleep(1)
            src = self.req.load(str(url))
        return src

    def handleShow(self, url):
        src = self.getSJSrc(url)
        soup = BeautifulSoup(src)
        packageName = self.pyfile.package().name
        if self.getConfig("changeNameSJ") == "Show":
            found = unescape(soup.find("h2").find("a").string.split(' &#8211;')[0])
            if found:
                packageName = found

        nav = soup.find("div", attrs={"id": "scb"})

        package_links = []
        for a in nav.findAll("a"):
            if self.getConfig("changeNameSJ") == "Show":
                package_links.append(a['href'])
            else:
                package_links.append(a['href'] + "#hasName")
        if self.getConfig("changeNameSJ") == "Show":
            self.packages.append((packageName, package_links, packageName))
        else:
            self.core.files.addLinks(package_links, self.pyfile.package().id)

    def handleSeason(self, url):
        src = self.getSJSrc(url)
        soup = BeautifulSoup(src)
        post = soup.find("div", attrs={"class": "post-content"})
        ps = post.findAll("p")

        seasonName = unescape(soup.find("a", attrs={"rel": "bookmark"}).string).replace("&#8211;", "-")
        groups = {}
        gid = -1
        for p in ps:
            if re.search("<strong>Sprache|<strong>Format", str(p)):
                var = p.findAll("strong")
                opts = {"Sprache": "", "Format": ""}
                for v in var:
                    n = unescape(v.string).strip()
                    n = re.sub(r"^([:]?)(.*?)([:]?)$", r'\2', n)
                    if n.strip() not in opts:
                        continue
                    val = v.nextSibling
                    if not val:
                        continue
                    val = val.replace("|", "").strip()
                    val = re.sub(r"^([:]?)(.*?)([:]?)$", r'\2', val)
                    opts[n.strip()] = val.strip()
                gid += 1
                groups[gid] = {}
                groups[gid]['ep'] = {}
                groups[gid]['opts'] = opts
            elif re.search("<strong>Download:", str(p)):
                parts = str(p).split("<br />")
                if re.search("<strong>", parts[0]):
                    ename = re.search('<strong>(.*?)</strong>', parts[0]).group(1).strip().decode("utf-8").replace(
                        "&#8211;", "-")
                    groups[gid]['ep'][ename] = {}
                    parts.remove(parts[0])
                    for part in parts:
                        hostername = re.search(r" \| ([-a-zA-Z0-9]+\.\w+)", part)
                        if hostername:
                            hostername = hostername.group(1)
                            groups[gid]['ep'][ename][hostername] = []
                            links = re.findall('href="(.*?)"', part)
                            for link in links:
                                groups[gid]['ep'][ename][hostername].append(link + "#hasName")

        links = []
        for g in groups.values():
            for ename in g['ep']:
                links.extend(self.getpreferred(g['ep'][ename]))
                if self.getConfig("changeNameSJ") == "Episode":
                    self.packages.append((ename, links, ename))
                    links = []
            package = "%s (%s, %s)" % (seasonName, g['opts']['Format'], g['opts']['Sprache'])
            if self.getConfig("changeNameSJ") == "Format":
                self.packages.append((package, links, package))
                links = []
        if (self.getConfig("changeNameSJ") == "Packagename") or re.search("#hasName", url):
            self.core.files.addLinks(links, self.pyfile.package().id)
        elif (self.getConfig("changeNameSJ") == "Season") or not re.search("#hasName", url):
            self.packages.append((seasonName, links, seasonName))

    def handleEpisode(self, url):
        src = self.getSJSrc(url)
        if not src.find(
                "Du hast das Download-Limit &uuml;berschritten! Bitte versuche es sp&auml;ter nocheinmal.") == -1:
            self.fail(_("Downloadlimit reached"))
        else:
            soup = BeautifulSoup(src)
            form = soup.find("form")
            h1 = soup.find("h1")

            if h1.get("class") == "wrap":
                captchaTag = soup.find(attrs={"src": re.compile("^/secure/")})
                if not captchaTag:
                    sleep(5)
                    self.retry()

                captchaUrl = "http://download.serienjunkies.org" + captchaTag['src']
                result = self.decryptCaptcha(str(captchaUrl), imgtype="png")
                sinp = form.find(attrs={"name": "s"})

                self.req.lastURL = str(url)
                sj = self.load(str(url), post={'s': sinp['value'], 'c': result, 'action': "Download"})

                soup = BeautifulSoup(sj)
            rawLinks = soup.findAll(attrs={"action": re.compile("^http://download.serienjunkies.org/")})

            if not len(rawLinks) > 0:
                sleep(1)
                self.retry()
                return

            self.correctCaptcha()

            links = []
            for link in rawLinks:
                frameUrl = link['action'].replace("/go-", "/frame/go-")
                links.append(self.handleFrame(frameUrl))
            if re.search("#hasName", url) or ((self.getConfig("changeNameSJ") == "Packagename") and
                                              (self.getConfig("changeNameDJ") == "Packagename")):
                self.core.files.addLinks(links, self.pyfile.package().id)
            else:
                if h1.text[2] == "_":
                    eName = h1.text[3:]
                else:
                    eName = h1.text
                self.packages.append((eName, links, eName))

    def handleOldStyleLink(self, url):
        sj = self.req.load(str(url))
        soup = BeautifulSoup(sj)
        form = soup.find("form", attrs={"action": re.compile("^http://serienjunkies.org")})
        captchaTag = form.find(attrs={"src": re.compile("^/safe/secure/")})
        captchaUrl = "http://serienjunkies.org" + captchaTag['src']
        result = self.decryptCaptcha(str(captchaUrl))
        url = form['action']
        sinp = form.find(attrs={"name": "s"})

        self.req.load(str(url), post={'s': sinp['value'], 'c': result, 'dl.start': "Download"}, cookies=False,
                      just_header=True)
        decrypted = self.req.lastEffectiveURL
        if decrypted == str(url):
            self.retry()
        self.core.files.addLinks([decrypted], self.pyfile.package().id)

    def handleFrame(self, url):
        self.req.load(str(url))
        return self.req.lastEffectiveURL

    def handleShowDJ(self, url):
        src = self.getSJSrc(url)
        soup = BeautifulSoup(src)
        post = soup.find("div", attrs={"id": "page_post"})
        ps = post.findAll("p")
        found = unescape(soup.find("h2").find("a").string.split(' &#8211;')[0])
        if found:
            seasonName = found

        groups = {}
        gid = -1
        for p in ps:
            if re.search("<strong>Sprache|<strong>Format", str(p)):
                var = p.findAll("strong")
                opts = {"Sprache": "", "Format": ""}
                for v in var:
                    n = unescape(v.string).strip()
                    n = re.sub(r"^([:]?)(.*?)([:]?)$", r'\2', n)
                    if n.strip() not in opts:
                        continue
                    val = v.nextSibling
                    if not val:
                        continue
                    val = val.replace("|", "").strip()
                    val = re.sub(r"^([:]?)(.*?)([:]?)$", r'\2', val)
                    opts[n.strip()] = val.strip()
                gid += 1
                groups[gid] = {}
                groups[gid]['ep'] = {}
                groups[gid]['opts'] = opts
            elif re.search("<strong>Download:", str(p)):
                parts = str(p).split("<br />")
                if re.search("<strong>", parts[0]):
                    ename = re.search('<strong>(.*?)</strong>', parts[0]).group(1).strip().decode("utf-8").replace(
                        "&#8211;", "-")
                    groups[gid]['ep'][ename] = {}
                    parts.remove(parts[0])
                    for part in parts:
                        hostername = re.search(r" \| ([-a-zA-Z0-9]+\.\w+)", part)
                        if hostername:
                            hostername = hostername.group(1)
                            groups[gid]['ep'][ename][hostername] = []
                            links = re.findall('href="(.*?)"', part)
                            for link in links:
                                groups[gid]['ep'][ename][hostername].append(link + "#hasName")

        links = []
        for g in groups.values():
            for ename in g['ep']:
                links.extend(self.getpreferred(g['ep'][ename]))
                if self.getConfig("changeNameDJ") == "Episode":
                    self.packages.append((ename, links, ename))
                    links = []
            package = "%s (%s, %s)" % (seasonName, g['opts']['Format'], g['opts']['Sprache'])
            if self.getConfig("changeNameDJ") == "Format":
                self.packages.append((package, links, package))
                links = []
        if (self.getConfig("changeNameDJ") == "Packagename") or re.search("#hasName", url):
            self.core.files.addLinks(links, self.pyfile.package().id)
        elif (self.getConfig("changeNameDJ") == "Show") or not re.search("#hasName", url):
            self.packages.append((seasonName, links, seasonName))

    def handleCategoryDJ(self, url):
        package_links = []
        src = self.getSJSrc(url)
        soup = BeautifulSoup(src)
        content = soup.find("div", attrs={"id": "content"})
        for a in content.findAll("a", attrs={"rel": "bookmark"}):
            package_links.append(a['href'])
        self.core.files.addLinks(package_links, self.pyfile.package().id)

    def decrypt(self, pyfile):
        showPattern = re.compile("^http://serienjunkies.org/serie/(.*)/$")
        seasonPattern = re.compile("^http://serienjunkies.org/.*?/(.*)/$")
        episodePattern = re.compile("^http://download.serienjunkies.org/f-.*?.html(#hasName)?$")
        oldStyleLink = re.compile("^http://serienjunkies.org/safe/(.*)$")
        categoryPatternDJ = re.compile("^http://dokujunkies.org/.*?(.*)$")
        showPatternDJ = re.compile(r"^http://dokujunkies.org/.*?/(.*)\.html(#hasName)?$")
        framePattern = re.compile("^http://download.(serienjunkies.org|dokujunkies.org)/frame/go-.*?/$")
        url = pyfile.url
        if framePattern.match(url):
            self.packages.append((pyfile.package().name, [self.handleFrame(url)], pyfile.package().name))
        elif episodePattern.match(url):
            self.handleEpisode(url)
        elif oldStyleLink.match(url):
            self.handleOldStyleLink(url)
        elif showPattern.match(url):
            self.handleShow(url)
        elif showPatternDJ.match(url):
            self.handleShowDJ(url)
        elif seasonPattern.match(url):
            self.handleSeason(url)
        elif categoryPatternDJ.match(url):
            self.handleCategoryDJ(url)

    #selects the preferred hoster, after that selects any hoster (ignoring the one to ignore)
    def getpreferred(self, hosterlist):

        result = []
        preferredList = self.getConfig("hosterList").strip().lower().replace(
            '|', ',').replace('.', '').replace(';', ',').split(',')
        if (self.getConfig("randomPreferred") is True) and (
                self.getConfig("hosterListMode") in ["OnlyOne", "OnlyPreferred(One)"]):
            random.shuffle(preferredList)
            # we don't want hosters be read two times
        hosterlist2 = hosterlist.copy()

        for preferred in preferredList:
            for Hoster in hosterlist:
                if preferred == Hoster.lower().replace('.', ''):
                    for Part in hosterlist[Hoster]:
                        self.logDebug("Selected " + Part)
                        result.append(str(Part))
                        del (hosterlist2[Hoster])
                    if self.getConfig("hosterListMode") in ["OnlyOne", "OnlyPreferred(One)"]:
                        return result

        ignorelist = self.getConfig("ignoreList").strip().lower().replace(
            '|', ',').replace('.', '').replace(';', ',').split(',')
        if self.getConfig('hosterListMode') in ["OnlyOne", "All"]:
            for Hoster in hosterlist2:
                if Hoster.strip().lower().replace('.', '') not in ignorelist:
                    for Part in hosterlist2[Hoster]:
                        self.logDebug("Selected2 " + Part)
                        result.append(str(Part))

                    if self.getConfig('hosterListMode') == "OnlyOne":
                        return result
        return result
