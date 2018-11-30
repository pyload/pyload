# -*- coding: utf-8 -*-

import inspect
import re
import urlparse

from module.network.HTTPRequest import BadHeader

from ..captcha.ReCaptcha import ReCaptcha
from ..internal.Addon import Addon
from ..internal.misc import parse_html_header


def plugin_id(plugin):
    return ("<%(plugintype)s %(pluginname)s%(id)s>" %
            {'plugintype': plugin.__type__.upper(),
             'pluginname': plugin.__name__,
             'id': "[%s]" % plugin.pyfile.id if plugin.pyfile else ""})


def is_simple_plugin(obj):
    return any(k.__name__ in ("SimpleHoster", "SimpleCrypter")
               for k in inspect.getmro(type(obj)))


def get_plugin_last_header(plugin):
    # @NOTE: req can be a HTTPRequest or a Browser object
    return plugin.req.http.header if hasattr(plugin.req, "http") else plugin.req.header


class CloudFlare(object):

    @staticmethod
    def handle_function(addon_plugin, owner_plugin, func_name, orig_func, args):
        addon_plugin.log_debug("Calling %s() of %s" % (func_name, plugin_id(owner_plugin)))

        try:
            data = orig_func(*args[0], **args[1])
            addon_plugin.log_debug("%s() returned successfully" % func_name)
            return data

        except BadHeader, e:
            addon_plugin.log_debug("%s(): got BadHeader exception %s" % (func_name, e.code))

            header = parse_html_header(e.header)

            if header.get('server') == "cloudflare":
                if e.code == 403:
                    data = CloudFlare._solve_cf_security_check(addon_plugin, owner_plugin, e.content)

                elif e.code == 503:
                    for _i in range(3):
                        try:
                            data = CloudFlare._solve_cf_ddos_challenge(addon_plugin, owner_plugin, e.content)
                            break

                        except BadHeader, e:  #: Possibly we got another ddos challenge
                            addon_plugin.log_debug("%s(): got BadHeader exception %s" % (func_name, e.code))

                            header = parse_html_header(e.header)

                            if e.code == 503 and header.get('server') == "cloudflare":
                                continue  #: Yes, it's a ddos challenge again..

                            else:
                                data = None  # Tell the exception handler to re-throw the exception
                                break

                    else:
                        addon_plugin.log_debug("%s(): Max solve retries reached" % func_name)
                        data = None  # Tell the exception handler to re-throw the exception

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
    def _solve_cf_ddos_challenge(addon_plugin, owner_plugin, data):
        try:
            addon_plugin.log_info(_("Detected CloudFlare's DDoS protection page"))
            # Cloudflare requires a delay before solving the challenge
            owner_plugin.set_wait(5)

            last_url = owner_plugin.req.lastEffectiveURL
            urlp = urlparse.urlparse(last_url)
            domain = urlp.netloc
            submit_url = "%s://%s/cdn-cgi/l/chk_jschl" % (urlp.scheme, domain)

            get_params = {}

            try:
                get_params['jschl_vc'] = re.search(r'name="jschl_vc" value="(\w+)"', data).group(1)
                get_params['pass'] = re.search(r'name="pass" value="(.+?)"', data).group(1)

                # Extract the arithmetic operation
                js = re.search(r'setTimeout\(function\(\){\s+(var s,t,o,p,b,r,e,a,k,i,n,g,f.+?\r?\n[\s\S]+?a\.value =.+?)\r?\n',
                               data).group(1)
                js = re.sub(r'a\.value = (.+ \+ t\.length).+', r'\1', js)
                js = re.sub(r'\s{3,}[a-z](?: = |\.).+', "", js).replace("t.length", str(len(domain)))
                js = re.sub(r"[\n\\']", "", js)

            except Exception:
                # Something is wrong with the page.
                # This may indicate CloudFlare has changed their anti-bot
                # technique.
                owner_plugin.log_error(_("Unable to parse CloudFlare's DDoS protection page"))
                return None  # Tell the exception handler to re-throw the exception

            if "toFixed" not in js:
                owner_plugin.log_error(_("Unable to parse CloudFlare's DDoS protection page"))
                return None  # Tell the exception handler to re-throw the exception

            # Safely evaluate the Javascript expression
            res = owner_plugin.js.eval(js)

            get_params['jschl_answer'] = str(float(res))

            owner_plugin.wait()  # Do the actual wait

            return owner_plugin.load(submit_url,
                                     get=get_params,
                                     ref=last_url)

        except BadHeader, e:
            raise e  #: Huston, we have a BadHeader!

        except Exception, e:
            addon_plugin.log_error(e)
            return None  # Tell the exception handler to re-throw the exception

    @staticmethod
    def _solve_cf_security_check(addon_plugin, owner_plugin, data):
        try:
            last_url = owner_plugin.req.lastEffectiveURL

            captcha = ReCaptcha(owner_plugin.pyfile)

            captcha_key = captcha.detect_key(data)
            if captcha_key:
                addon_plugin.log_info(_("Detected CloudFlare's security check page"))

                response, challenge = captcha.challenge(captcha_key, data)
                return owner_plugin.load(owner_plugin.fixurl("/cdn-cgi/l/chk_captcha"),
                                         get={'g-recaptcha-response': response},
                                         ref=last_url)

            else:
                addon_plugin.log_warning(_("Got unexpected CloudFlare html page"))
                return None  # Tell the exception handler to re-throw the exception

        except Exception, e:
            addon_plugin.log_error(e)
            return None  # Tell the exception handler to re-throw the exception


class PreloadStub(object):

    def __init__(self, addon_plugin, owner_plugin):
        self.addon_plugin = addon_plugin
        self.owner_plugin = owner_plugin
        self.old_preload = owner_plugin._preload

    def my_preload(self, *args, **kwargs):
        data = CloudFlare.handle_function(self.addon_plugin, self.owner_plugin, "_preload", self.old_preload, (args, kwargs))
        if data is not None:
            self.owner_plugin.data = data

    def __repr__(self):
        return "<PreloadStub object at %s>" % hex(id(self))


class CloudFlareDdos(Addon):
    __name__ = "CloudFlareDdos"
    __type__ = "hook"
    __version__ = "0.15"
    __status__ = "testing"

    __config__ = [("activated", "bool", "Activated", False)]

    __description__ = """CloudFlare DDoS protection support"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    def activate(self):
        self.stubs = {}
        self._override_get_url()

    def deactivate(self):
        while len(self.stubs):
            stub = next(self.stubs.itervalues())
            self._unoverride_preload(stub.owner_plugin)

        self._unoverride_get_url()

    def _unoverride_preload(self, plugin):
        if id(plugin) in self.stubs:
            self.log_debug("Unoverriding _preload() for %s" % plugin_id(plugin))

            stub = self.stubs.pop(id(plugin))
            stub.owner_plugin._preload = stub.old_preload

        else:
            self.log_warning(_("No _preload() override found for %s, cannot un-override>") %
                plugin_id(plugin))

    def _override_preload(self, plugin):
        if id(plugin) not in self.stubs:
            stub = PreloadStub(self, plugin)
            self.stubs[id(plugin)] = stub

            self.log_debug("Overriding _preload() for %s" % plugin_id(plugin))
            plugin._preload = stub.my_preload

        else:
            self.log_warning(_("Already overrided _preload() for %s") % plugin_id(plugin))

    def _override_get_url(self):
        self.log_debug("Overriding get_url()")

        self.old_get_url = self.pyload.requestFactory.getURL
        self.pyload.requestFactory.getURL = self.my_get_url

    def _unoverride_get_url(self):
        self.log_debug("Unoverriding get_url()")

        self.pyload.requestFactory.getURL = self.old_get_url

    def _find_owner_plugin(self):
        """
        Walk the callstack until we find SimpleHoster or SimpleCrypter class
        Dirty but works.
        """
        f = frame = inspect.currentframe()
        try:
            while True:
                if f is None:
                    return None

                elif 'self' in f.f_locals and is_simple_plugin(f.f_locals['self']):
                    return f.f_locals['self']

                else:
                    f = f.f_back

        finally:
            del frame

    def download_preparing(self, pyfile):
        #: Only SimpleHoster and SimpleCrypter based plugins are supported
        if not is_simple_plugin(pyfile.plugin):
            self.log_debug("Skipping plugin %s" % plugin_id(pyfile.plugin))
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
        owner_plugin = self._find_owner_plugin()
        if owner_plugin is None:
            self.log_warning(_("Owner plugin not found, cannot process"))
            return self.old_get_url(*args, **kwargs)

        else:
            #@NOTE: Better use owner_plugin.load() instead of get_url() so cookies are saved and so captcha credits
            #@NOTE: Also that way we can use 'owner_plugin.req.header' to get the headers, otherwise we cannot get them
            res = CloudFlare.handle_function(self, owner_plugin, "get_url", owner_plugin.load, (args, kwargs))
            if kwargs.get('just_header', False):
                # @NOTE: SimpleHoster/SimpleCrypter returns a dict while get_url() returns raw headers string,
                # make sure we return a string for get_url('just_header'=True)
                res = get_plugin_last_header(owner_plugin)

            return res
