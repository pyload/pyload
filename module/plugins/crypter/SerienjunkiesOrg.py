# -*- coding: utf-8 -*-

import random
import re
import inspect

from time import sleep

from BeautifulSoup import BeautifulSoup

from module.plugins.internal.Crypter import Crypter
from module.utils import html_unescape


class SerienjunkiesOrg(Crypter):
    __name__ = "SerienjunkiesOrg"
    __type__ = "crypter"
    __version__ = "0.46"

    __pattern__ = r'http://(?:www\.)?(download\.)?(serienjunkies|dokujunkies)\.org/.+'
    __config__ = [("changeNameSJ", "Packagename;Show;Season;Format;Episode", "Take SJ.org name", "Show"),
                  ("changeNameDJ", "Packagename;Show;Format;Episode", "Take DJ.org name", "Show"),
                  ("randomPreferred", "bool", "Randomize Preferred-List", False),
                  ("hosterListMode", "Only one;Only preferred (One);Only preferred (All);All", "Use for", "All"),
                  ("hosterList", "str", "Preferred Hoster list (comma separated)", ""),
                  ("ignoreList", "str", "Ignored Hoster list (comma separated)", ""),
                  ("use_subfolder", "bool", "Save package to subfolder", True),
                  ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Serienjunkies.org decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("mkaay", "mkaay@mkaay.de"),
                   ("godofdream", "soilfiction@gmail.com")]
    

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
        if self.config.get("changeNameSJ") == "Show":
            found = html_unescape(soup.find("h2").find("a").string.split(' &#8211;')[0])
            if found:
                packageName = found

        nav = soup.find("div", attrs={"id": "scb"})

        package_links = []
        for a in nav.findAll("a"):
            if self.config.get("changeNameSJ") == "Show":
                package_links.append(a['href'])
            else:
                package_links.append(a['href'] + "#hasName")
        if self.config.get("changeNameSJ") == "Show":
            self.packages.append((packageName, package_links, packageName))
        else:
            self.packages.append((self.pyfile.package().name, package_links, self.pyfile.package().name))


    def handleSeason(self, url):
        src = self.getSJSrc(url)
        soup = BeautifulSoup(src)
        post = soup.find("div", attrs={"class": "post-content"})
        ps = post.findAll("p")

        seasonName = html_unescape(soup.find("a", attrs={"rel": "bookmark"}).string).replace("&#8211;", "-")
        groups = {}
        gid = -1
        for p in ps:
            if re.search("<strong>Sprache|<strong>Format", str(p)):
                var = p.findAll("strong")
                opts = {"Sprache": "", "Format": ""}
                for v in var:
                    n = html_unescape(v.string).strip()
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
                if self.config.get("changeNameSJ") == "Episode":
                    self.packages.append((ename, links, ename))
                    links = []
            package = "%s (%s, %s)" % (seasonName, g['opts']['Format'], g['opts']['Sprache'])
            if self.config.get("changeNameSJ") == "Format":
                self.packages.append((package, links, package))
                links = []
        if (self.config.get("changeNameSJ") == "Packagename") or re.search("#hasName", url):
            self.packages.append((self.pyfile.package().name, links, self.pyfile.package().name))
        elif (self.config.get("changeNameSJ") == "Season") or not re.search("#hasName", url):
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
                result = self.captcha.decrypt(str(captchaUrl), input_type="png", ocr=False)
                sinp = form.find(attrs={"name": "s"})

                self.req.lastURL = str(url)
                sj = self.load(str(url), post={'s': sinp['value'], 'c': result, 'action': "Download"})

                soup = BeautifulSoup(sj)
            rawLinks = soup.findAll(attrs={"action": re.compile("^http://download.serienjunkies.org/")})

            if not len(rawLinks) > 0:
                sleep(1)
                self.retry()
                return

            self.captcha.correct()

            links = []
            for link in rawLinks:
                frameUrl = link['action'].replace("/go-", "/frame/go-")
                links.append(self.handleFrame(frameUrl))

            if re.search("#hasName", url) or ((self.config.get("changeNameSJ") == "Packagename") and
                                              (self.config.get("changeNameDJ") == "Packagename")):
                #self.links = links
                self.packages.append((self.pyfile.package().name, links, self.pyfile.package().name))
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
        result = self.captcha.decrypt(str(captchaUrl), ocr=False)
        url = form['action']
        sinp = form.find(attrs={"name": "s"})

        self.req.load(str(url), post={'s': sinp['value'], 'c': result, 'dl.start': "Download"}, cookies=False,
                      just_header=True)
        decrypted = self.req.lastEffectiveURL
        if decrypted == str(url):
            self.retry()
        self.packages.append((self.pyfile.package().name, [decrypted], self.pyfile.package().name))


    def handleFrame(self, url):
        self.req.load(str(url))
        return self.req.lastEffectiveURL


    def handleShowDJ(self, url):
        src = self.getSJSrc(url)
        soup = BeautifulSoup(src)
        post = soup.find("div", attrs={"id": "page_post"})
        ps = post.findAll("p")
        found = html_unescape(soup.find("h2").find("a").string.split(' &#8211;')[0])
        if found:
            seasonName = found

        groups = {}
        gid = -1
        for p in ps:
            if re.search("<strong>Sprache|<strong>Format", str(p)):
                var = p.findAll("strong")
                opts = {"Sprache": "", "Format": ""}
                for v in var:
                    n = html_unescape(v.string).strip()
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
                if self.config.get("changeNameDJ") == "Episode":
                    self.packages.append((ename, links, ename))
                    links = []
            package = "%s (%s, %s)" % (seasonName, g['opts']['Format'], g['opts']['Sprache'])
            if self.config.get("changeNameDJ") == "Format":
                self.packages.append((package, links, package))
                links = []
        if (self.config.get("changeNameDJ") == "Packagename") or re.search("#hasName", url):
            self.packages.append((self.pyfile.package().name, links, self.pyfile.package().name))
        elif (self.config.get("changeNameDJ") == "Show") or not re.search("#hasName", url):
            self.packages.append((seasonName, links, seasonName))


    def handleCategoryDJ(self, url):
        package_links = []
        src = self.getSJSrc(url)
        soup = BeautifulSoup(src)
        content = soup.find("div", attrs={"id": "content"})
        for a in content.findAll("a", attrs={"rel": "bookmark"}):
            package_links.append(a['href'])
        self.packages.append((self.pyfile.package().name, package_links, self.pyfile.package().name))


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
        preferredList = self.config.get("hosterList").strip().lower().replace(
            '|', ',').replace('.', '').replace(';', ',').split(',')
        if (self.config.get("randomPreferred") is True) and (
                self.config.get("hosterListMode") in ["Only one", "Only preferred (One)"]):
            random.shuffle(preferredList)
            # we don't want hosters be read two times
        hosterlist2 = hosterlist.copy()

        for preferred in preferredList:
            for Hoster in hosterlist:
                if preferred == Hoster.lower().replace('.', ''):
                    for Part in hosterlist[Hoster]:
                        self.log_debug("Selected " + Part)
                        result.append(str(Part))
                        del (hosterlist2[Hoster])
                    if self.config.get("hosterListMode") in ["Only one", "Only preferred (One)"]:
                        return result

        ignorelist = self.config.get("ignoreList").strip().lower().replace(
            '|', ',').replace('.', '').replace(';', ',').split(',')
        if self.config.get('hosterListMode') in ["Only one", "All"]:
            for Hoster in hosterlist2:
                if Hoster.strip().lower().replace('.', '') not in ignorelist:
                    for Part in hosterlist2[Hoster]:
                        self.log_debug("Selected2 " + Part)
                        result.append(str(Part))

                    if self.config.get('hosterListMode') == "Only one":
                        return result
        return result
