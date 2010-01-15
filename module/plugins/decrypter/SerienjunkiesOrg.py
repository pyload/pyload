# -*- coding: utf-8 -*-

import re

from module.Plugin import Plugin
from module.BeautifulSoup import BeautifulSoup
from module.unescape import unescape

class SerienjunkiesOrg(Plugin):
    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "SerienjunkiesOrg"
        props['type'] = "container"
        props['pattern'] = r"http://.*?serienjunkies.org/.*?"
        props['version'] = "0.2"
        props['description'] = """serienjunkies.org Container Plugin"""
        props['author_name'] = ("mkaay")
        props['author_mail'] = ("mkaay@mkaay.de")
        self.props = props
        self.parent = parent
        self.html = None
        self.multi_dl = False
        
        self.hosterMap = {
            "rc": "RapidshareCom",
            "ff": "FilefactoryCom",
            "ut": "UploadedTo",
            "ul": "UploadedTo",
            "nl": "NetloadIn",
            "rs": "RapidshareDe"
        }
        self.hosterMapReverse = dict((v,k) for k, v in self.hosterMap.iteritems())
        episodePattern = re.compile("^http://download.serienjunkies.org/f-.*?.html$")
        oldStyleLink = re.compile("^http://serienjunkies.org/safe/(.*)$")
        if episodePattern.match(self.parent.url) or oldStyleLink.match(self.parent.url):
            self.decryptNow = False
        else:
            self.decryptNow = True
    
    def prepare(self, thread):
        pyfile = self.parent

        self.want_reconnect = False

        pyfile.status.exists = self.file_exists()

        if not pyfile.status.exists:
            raise Exception, "File not found"
            return False

        pyfile.status.filename = self.get_file_name()
            
        pyfile.status.waituntil = self.time_plus_wait
        pyfile.status.url = self.get_file_url()
        pyfile.status.want_reconnect = self.want_reconnect

        thread.wait(self.parent)
        
        return True
    
    def getSJSrc(self, url):
        src = self.req.load(str(url))
        if not src.find("Enter Serienjunkies") == -1:
            src = self.req.load(str(url))
        return src
    
    def file_exists(self):
        return True
    
    def handleSeason(self, url):
        src = self.getSJSrc(url)
        soup = BeautifulSoup(src)
        post = soup.find("div", attrs={"class": "post-content"})
        ps = post.findAll("p")
        hosterPattern = re.compile("^http://download\.serienjunkies\.org/f-.*?/([rcfultns]{2})_.*?\.html$")
        preferredHoster = self.get_config("preferredHoster").split(",")
        self.logger.debug("Preferred hoster: %s" % ", ".join(preferredHoster))
        groups = {}
        gid = -1
        seasonName = soup.find("a", attrs={"rel":"bookmark"}).string
        for p in ps:
            if re.search("<strong>Dauer|<strong>Sprache|<strong>Format", str(p)):
                var = p.findAll("strong")
                opts = {"Dauer": "", "Uploader": "", "Sprache": "", "Format": "", u"Größe": ""}
                for v in var:
                    n = unescape(v.string)
                    val = v.nextSibling
                    val = val.encode("utf-8")
                    val = unescape(val)
                    val = val.replace("|", "").strip()
                    n = n.strip()
                    n = re.sub(r"^([:]?)(.*?)([:]?)$", r'\2', n)
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
        packages = {}
        for g in groups.values():
            links = []
            linklist = g["ep"]
            package = "%s (%s, %s)" % (seasonName, g["opts"]["Format"], g["opts"]["Sprache"])
            linkgroups = {}
            for link in linklist:
                key = re.sub("^http://download\.serienjunkies\.org/f-.*?/([rcfultns]{2})_", "", link)
                if not linkgroups.has_key(key):
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
            packages[package] = links
        return packages
    
    def handleEpisode(self, url):
        if not self.parent.core.isGUIConnected():
            raise CaptchaError
        for i in range(3):
            src = self.getSJSrc(url)
            if not src.find("Du hast das Download-Limit &uuml;berschritten! Bitte versuche es sp&auml;ter nocheinmal.") == -1:
                self.logger.info("Downloadlimit reached")
                return False
            else:
                soup = BeautifulSoup(src)
                form = soup.find("form")
                captchaTag = soup.find(attrs={"src":re.compile("^/secure/")})
                captchaUrl = "http://download.serienjunkies.org"+captchaTag["src"]
                captchaData = self.req.load(str(captchaUrl))
                result = self.waitForCaptcha(captchaData, "png")
                url = "http://download.serienjunkies.org"+form["action"]
                sinp = form.find(attrs={"name":"s"})
                
                sj = self.req.load(str(url), post={'s': sinp["value"], 'c': result, 'action': "Download"})
                
                soup = BeautifulSoup(sj)
                rawLinks = soup.findAll(attrs={"action": re.compile("^http://download.serienjunkies.org/")})
                
                if not len(rawLinks) > 0:
                    continue
                
                links = []
                for link in rawLinks:
                    frameUrl = link["action"].replace("/go-", "/frame/go-")
                    links.append(self.handleFrame(frameUrl))
                return links
    
    def handleOldStyleLink(self, url):
        if not self.parent.core.isGUIConnected():
            raise CaptchaError
        for i in range(3):
            sj = self.req.load(str(url))
            soup = BeautifulSoup(sj)
            form = soup.find("form", attrs={"action":re.compile("^http://serienjunkies.org")})
            captchaTag = form.find(attrs={"src":re.compile("^/safe/secure/")})
            captchaUrl = "http://serienjunkies.org"+captchaTag["src"]
            captchaData = self.req.load(str(captchaUrl))
            result = self.waitForCaptcha(captchaData, "png")
            url = form["action"]
            sinp = form.find(attrs={"name":"s"})
            
            self.req.load(str(url), post={'s': sinp["value"], 'c': result, 'dl.start': "Download"}, cookies=False, just_header=True)
            decrypted = self.req.lastEffectiveURL
            if decrypted == str(url):
                continue
            return [decrypted]
        return False
    
    def handleFrame(self, url):
        self.req.load(str(url), cookies=False, just_header=True)
        return self.req.lastEffectiveURL
    
    def proceed(self, url, location):
        links = False
        episodePattern = re.compile("^http://download.serienjunkies.org/f-.*?.html$")
        oldStyleLink = re.compile("^http://serienjunkies.org/safe/(.*)$")
        framePattern = re.compile("^http://download.serienjunkies.org/frame/go-.*?/$")
        seasonPattern = re.compile("^http://serienjunkies.org/\?p=.*?$")
        if framePattern.match(url):
            links = [self.handleFrame(url)]
        elif episodePattern.match(url):
            links = self.handleEpisode(url)
        elif oldStyleLink.match(url):
            links = self.handleOldStyleLink(url)
        elif seasonPattern.match(url):
            links = self.handleSeason(url)
        self.links = links
