# -*- coding: utf-8 -*-

import re
import urlparse
import time

from module.plugins.internal.Addon import Addon
from module.plugins.internal.SimpleHoster import SimpleHoster
from module.plugins.internal.misc import parse_html_header
from module.network.HTTPRequest import BadHeader
from module.plugins.captcha.ReCaptcha import ReCaptcha

def plugin_id(plugin):
    return ("<%(plugintype)s %(pluginname)s[%(id)s]>" %
            {'plugintype': plugin.__type__.upper(),
             'pluginname': plugin.__name__,
             'id'        : plugin.pyfile.id})


class PreloadStub(object):
    def __init__(self, addon_plugin, hoster_plugin):
        self.addon_plugin = addon_plugin
        self.hoster_plugin = hoster_plugin
        self.old_preload = hoster_plugin._preload


    def my_preload(self, *args, **kwargs):
        self.addon_plugin.log_debug(_("Calling _preload() of %s") % plugin_id(self.hoster_plugin))

        try:
            data = self.old_preload(*args, **kwargs)
            self.addon_plugin.log_debug(_("_preload() returned successfully"))
            return data

        except BadHeader, e:
            self.addon_plugin.log_debug("_preload(): got BadHeader exception %s" % e.code)
            header = parse_html_header(self.hoster_plugin.req.http.header if hasattr(self.hoster_plugin.req, "http")
                                       else self.hoster_plugin.req.header)  # @NOTE: req can be a HTTPRequest or a Browser object

            if header.get('server') == "cloudflare-nginx":
                if e.code == 403:
                    data = self._solve_cf_security_check(e.content)

                elif e.code == 503:
                    data = self._solve_cf_ddos_challenge(e.content)

                else:
                    self.addon_plugin.log_warning(_("Unknown CloudFlare response code %s") % e.code)
                    raise

                if data is None:
                    raise e
                else:
                    self.hoster_plugin.data =  data

            else:
                raise

    def _solve_cf_ddos_challenge(self, data):
        self.addon_plugin.info("Detected CloudFlare's DDoS protection page")
        time.sleep(5)  # Cloudflare requires a delay before solving the challenge

        urlp = urlparse.urlparse(self.hoster_plugin.pyfile.url)
        domain = urlp.netloc
        post_url = "%s://%s/cdn-cgi/l/chk_jschl" % (urlp.scheme, domain)

        post_data = {}

        try:
            post_data['jschl_vc'] = re.search(r'name="jschl_vc" value="(\w+)"', data).group(1)
            post_data['pass'] = re.search(r'name="pass" value="(.+?)"', data).group(1)

            # Extract the arithmetic operation
            js = re.search(r'setTimeout\(function\(\){\s+(var s,t,o,p,b,r,e,a,k,i,n,g,f.+?\r?\n[\s\S]+?a\.value =.+?)\r?\n', data).group(1)
            js = re.sub(r'a\.value = (parseInt\(.+?\)).+', r'\1', js)
            js = re.sub(r'\s{3,}[a-z](?: = |\.).+', "", js)
            js = re.sub(r"[\n\\']", "", js)
            js = js.replace('return', '')


        except Exception:
            # Something is wrong with the page.
            # This may indicate CloudFlare has changed their anti-bot technique.
            self.hoster_plugin.log_error(_("Unable to parse CloudFlare's DDoS protection page"))
            return None  # Tell the exception handler to re-throw the exception

        # Safely evaluate the Javascript expression
        post_data['jschl_answer'] = str(int(self.hoster_plugin.js.eval(js)) + len(domain))
        self.addon_plugin.log_debug("post_data: %s" % post_data)
        return self.hoster_plugin.load(post_data,
                                       post=post_data,
                                       ref=self.hoster_plugin.pyfile.url)


    def _solve_cf_security_check(self, data):
        captcha = ReCaptcha(self.hoster_plugin.pyfile)

        captcha_key = captcha.detect_key(data)
        if captcha_key:
            self.addon_plugin.info("Detected CloudFlare's security check page")
            response, challenge = captcha.challenge(captcha_key, data)
            return  self.hoster_plugin.load(self.hoster_plugin.fixurl("/cdn-cgi/l/chk_captcha"),
                                           get={'g-recaptcha-response': response},
                                           ref=self.hoster_plugin.pyfile.url)

        else:
            self.addon_plugin.log_warning(_("Got unexpected CloudFlare html page"))
            return None  # Tell the exception handler to re-throw the exception


    def __repr__(self):
        return "<PreloadStub object at %s>" % hex(id(self))


class CloudFlareDdos(Addon):
    __name__    = "CloudFlareDdos"
    __type__    = "hook"
    __version__ = "0.01"
    __status__  = "testing"

    __config__ = [("activated", "bool", "Activated" , False)]

    __description__ = """CloudFlare DDoS protection support"""
    __license__     = "GPLv3"
    __authors__     = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]


    def activate(self):
        self.stubs = {}


    def deactivate(self):
        while len(self.stubs):
            self._unoverride_preload(self.stubs.itervalues().next())


    def _unoverride_preload(self, plugin):
        if id(plugin) in self.stubs:
            self.log_debug(_("Unoverriding _preload() for %s") % plugin_id(plugin))

            stub = self.stubs.pop(id(plugin))
            stub.hoster_plugin._preload = stub.old_preload

        else:
            self.log_warning(_("No _preload() override found for %s, cannot un-override>") % plugin_id(plugin))


    def _override_preload(self, plugin):
        if id(plugin) not in self.stubs:
            self.log_debug(_("Overriding _preload() for%s") % plugin_id(plugin))

            stub = PreloadStub(self, plugin)
            self.stubs[id(plugin)] = stub
            plugin._preload = stub.my_preload

        else:
            self.log_warning(_("Already overrided _preload() for %s") % plugin_id(plugin))


    def download_preparing(self, pyfile):
        if not isinstance(pyfile.plugin, SimpleHoster):  #: Only SimpleHoster based plugins are supported
            self.log_debug(_("Skipping plugin %s") % plugin_id(pyfile.plugin))
            return

        else:
            attr = getattr(pyfile.plugin, "_preload", None)
            if not attr or not callable(attr):
                self.log_error(_("%s is missing _preload() function, cannot override!") % plugin_id(pyfile.plugin))
                return

        self._override_preload(pyfile.plugin)


    def download_processed(self, pyfile):
        if id(pyfile.plugin) in self.stubs:
            self._unoverride_preload(pyfile.plugin)
