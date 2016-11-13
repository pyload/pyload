# -*- coding: utf-8 -*-

import inspect
import re
import urlparse
import time

from module.plugins.internal.Addon import Addon
from module.plugins.internal.SimpleHoster import SimpleHoster
from module.plugins.internal.misc import parse_html_header
from module.network.HTTPRequest import BadHeader
from module.plugins.captcha.ReCaptcha import ReCaptcha

def plugin_id(plugin):
    return ("<%(plugintype)s %(pluginname)s%(id)s>" %
            {'plugintype': plugin.__type__.upper(),
             'pluginname': plugin.__name__,
             'id'        : "[%s]" % plugin.pyfile.id if plugin.pyfile else ""})



class CloudFlare(object):
    @staticmethod
    def handle_function(addon_plugin, hoster_plugin, func_name, orig_func, args):
        addon_plugin.log_debug(_("Calling %s() of %s") % (func_name, plugin_id(hoster_plugin)))

        try:
            data = orig_func(*args[0], **args[1])
            addon_plugin.log_debug(_("%s() returned successfully") % func_name)
            return data

        except BadHeader, e:
            addon_plugin.log_debug(_("%s(): got BadHeader exception %s") % (func_name, e.code))

            header = parse_html_header(hoster_plugin.req.http.header if hasattr(hoster_plugin.req, "http")
                                       else hoster_plugin.req.header)  # @NOTE: req can be a HTTPRequest or a Browser object

            if header.get('server') == "cloudflare-nginx":
                if e.code == 403:
                    data = CloudFlare._solve_cf_security_check(addon_plugin, hoster_plugin, e.content)

                elif e.code == 503:
                    data = CloudFlare._solve_cf_ddos_challenge(addon_plugin, hoster_plugin, e.content)

                else:
                    addon_plugin.log_warning(_("Unknown CloudFlare response code %s") % e.code)
                    raise

                if data is None:
                    raise e

                else:
                    return data

            else:
                raise


    @staticmethod
    def _solve_cf_ddos_challenge(addon_plugin, hoster_plugin, data):
        addon_plugin.info(_("Detected CloudFlare's DDoS protection page"))
        time.sleep(5)  # Cloudflare requires a delay before solving the challenge

        last_url = hoster_plugin.req.lastEffectiveURL
        urlp = urlparse.urlparse(hoster_plugin.pyfile.url)
        domain = urlp.netloc
        post_url = "%s://%s/cdn-cgi/l/chk_jschl" % (urlp.scheme, domain)

        post_data = {}

        try:
            post_data['jschl_vc'] = re.search(r'name="jschl_vc" value="(\w+)"', data).group(1)
            post_data['pass'] = re.search(r'name="pass" value="(.+?)"', data).group(1)

            # Extract the arithmetic operation
            js = re.search(r'setTimeout\(function\(\){\s+(var s,t,o,p,b,r,e,a,k,i,n,g,f.+?\r?\n[\s\S]+?a\.value =.+?)\r?\n',
                           data).group(1)
            js = re.sub(r'a\.value = (parseInt\(.+?\)).+', r'\1', js)
            js = re.sub(r'\s{3,}[a-z](?: = |\.).+', "", js)
            js = re.sub(r"[\n\\']", "", js)
            js = js.replace('return', '')


        except Exception:
            # Something is wrong with the page.
            # This may indicate CloudFlare has changed their anti-bot technique.
            hoster_plugin.log_error(_("Unable to parse CloudFlare's DDoS protection page"))
            return None  # Tell the exception handler to re-throw the exception

        # Safely evaluate the Javascript expression
        post_data['jschl_answer'] = str(int(hoster_plugin.js.eval(js)) + len(domain))
        return hoster_plugin.load(post_data,
                                  post=post_data,
                                  ref=last_url)


    @staticmethod
    def _solve_cf_security_check(addon_plugin, hoster_plugin,data):
        last_url = hoster_plugin.req.lastEffectiveURL

        captcha = ReCaptcha(hoster_plugin.pyfile)

        captcha_key = captcha.detect_key(data)
        if captcha_key:
            addon_plugin.log_info(_("Detected CloudFlare's security check page"))
            response, challenge = captcha.challenge(captcha_key, data)
            return hoster_plugin.load(hoster_plugin.fixurl("/cdn-cgi/l/chk_captcha"),
                                           get={'g-recaptcha-response': response},
                                           ref=last_url)

        else:
            addon_plugin.log_warning(_("Got unexpected CloudFlare html page"))
            return None  # Tell the exception handler to re-throw the exception


class PreloadStub(object):
    def __init__(self, addon_plugin, hoster_plugin):
        self.addon_plugin = addon_plugin
        self.hoster_plugin = hoster_plugin
        self.old_preload = hoster_plugin._preload


    def my_preload(self, *args, **kwargs):
        data = CloudFlare.handle_function(self.addon_plugin, self.hoster_plugin, "_preload", self.old_preload, (args, kwargs))
        self.hoster_plugin.data = data


    def __repr__(self):
        return "<PreloadStub object at %s>" % hex(id(self))


class CloudFlareDdos(Addon):
    __name__    = "CloudFlareDdos"
    __type__    = "hook"
    __version__ = "0.02"
    __status__  = "testing"

    __config__ = [("activated", "bool", "Activated" , False)]

    __description__ = """CloudFlare DDoS protection support"""
    __license__     = "GPLv3"
    __authors__     = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]


    def activate(self):
        self.stubs = {}
        self._override_get_url()


    def deactivate(self):
        while len(self.stubs):
            stub = self.stubs.itervalues().next()
            self._unoverride_preload(stub.hoster_plugin)

        self._unoverride_get_url()


    def _unoverride_preload(self, plugin):
        if id(plugin) in self.stubs:
            self.log_debug(_("Unoverriding _preload() for %s") % plugin_id(plugin))

            stub = self.stubs.pop(id(plugin))
            stub.hoster_plugin._preload = stub.old_preload

        else:
            self.log_warning(_("No _preload() override found for %s, cannot un-override>") % plugin_id(plugin))


    def _override_preload(self, plugin):
        if id(plugin) not in self.stubs:
            stub = PreloadStub(self, plugin)
            self.stubs[id(plugin)] = stub

            self.log_debug(_("Overriding _preload() for %s") % plugin_id(plugin))
            plugin._preload = stub.my_preload

        else:
            self.log_warning(_("Already overrided _preload() for %s") % plugin_id(plugin))


    def _override_get_url(self):
        self.log_debug(_("Overriding get_url()"))

        self.old_get_url = self.pyload.requestFactory.getURL
        self.pyload.requestFactory.getURL = self.my_get_url


    def _unoverride_get_url(self):
        self.log_debug(_("Unoverriding get_url()"))

        self.pyload.requestFactory.getURL = self.old_get_url


    def _find_account_plugin(self):
        """
        Walk the callstack until we find SimpleHoster class
        Dirty but works.
        """
        f = frame = inspect.currentframe()
        while True:
            if f is None:
                return  None

            elif 'self' in f.f_locals and isinstance(f.f_locals['self'], SimpleHoster):
                return f.f_locals['self']

            else:
                f = f.f_back

        del frame


    def download_preparing(self, pyfile):
        if not isinstance(pyfile.plugin, SimpleHoster):  #: Only SimpleHoster based plugins are supported
            self.log_debug(_("Skipping plugin %s") % plugin_id(pyfile.plugin))
            return

        attr = getattr(pyfile.plugin, "_preload", None)
        if not attr and not callable(attr):
            self.log_error(_("%s is missing _preload() function, cannot override!") % plugin_id(pyfile.plugin))
            return

        self._override_preload(pyfile.plugin)


    def download_processed(self, pyfile):
        if id(pyfile.plugin) in self.stubs:
            self._unoverride_preload(pyfile.plugin)


    def my_get_url(self, *args, **kwargs):
        hotser_plugin = self._find_account_plugin()
        if hotser_plugin is None:
            return self.old_get_url(*args, **kwargs)

        else:
            #@NOTE: Better use hotser_plugin.load() instead of get_url() so cookies are saved and so captcha credits
            #@NOTE: Also that way we can use 'hotser_plugin.req.header' to get the headers, otherwise we cannot get them
            return CloudFlare.handle_function(self, hotser_plugin, "get_url", hotser_plugin.load, (args, kwargs))
