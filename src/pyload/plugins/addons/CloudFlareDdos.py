# -*- coding: utf-8 -*-

import inspect
import re
import urllib.parse

from pyload.core.network.http.exceptions import BadHeader
from pyload.core.utils.misc import eval_js

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.addon import BaseAddon
from ..helpers import parse_html_header


def plugin_id(plugin):
    return "<{plugintype} {pluginname}{id}>".format(
        plugintype=plugin.__type__.upper(),
        pluginname=plugin.__name__,
        id="[{}]".format(plugin.pyfile.id if plugin.pyfile else ""),
    )


def is_simple_plugin(obj):
    return any(
        k.__name__ in ("SimpleDownloader", "SimpleDecrypter")
        for k in inspect.getmro(type(obj))
    )


def get_plugin_last_header(plugin):
    # NOTE: req can be a HTTPRequest or a Browser object
    return plugin.req.http.header if hasattr(plugin.req, "http") else plugin.req.header


class CloudFlare:
    @staticmethod
    def handle_function(addon_plugin, owner_plugin, func_name, orig_func, args):
        addon_plugin.log_debug(
            "Calling {}() of {}".format(func_name, plugin_id(owner_plugin))
        )

        try:
            data = orig_func(*args[0], **args[1])
            addon_plugin.log_debug(f"{func_name}() returned successfully")
            return data

        except BadHeader as exc:
            addon_plugin.log_debug(
                "{}(): got BadHeader exception {}".format(func_name, exc.code)
            )

            header = parse_html_header(get_plugin_last_header(owner_plugin))

            if header.get("server") == "cloudflare":
                if exc.code == 403:
                    data = CloudFlare._solve_cf_security_check(
                        addon_plugin, owner_plugin, exc.content
                    )

                elif exc.code == 503:
                    data = CloudFlare._solve_cf_ddos_challenge(
                        addon_plugin, owner_plugin, exc.content
                    )

                else:
                    addon_plugin.log_warning(
                        addon_plugin._("Unknown CloudFlare response code {}").format(
                            exc.code
                        )
                    )
                    raise

                if data is None:
                    raise exc

                else:
                    return data

            else:
                raise

    @staticmethod
    def _solve_cf_ddos_challenge(addon_plugin, owner_plugin, data):
        try:
            addon_plugin.log_info(
                addon_plugin._("Detected CloudFlare's DDoS protection page")
            )
            # Cloudflare requires a delay before solving the challenge
            owner_plugin.set_wait(5)

            last_url = owner_plugin.req.last_effective_url
            urlp = urllib.parse.urlparse(last_url)
            domain = urlp.netloc
            submit_url = "{}://{}/cdn-cgi/l/chk_jschl".format(urlp.scheme, domain)

            get_params = {}

            try:
                get_params["jschl_vc"] = re.search(
                    r'name="jschl_vc" value="(\w+)"', data
                ).group(1)
                get_params["pass"] = re.search(
                    r'name="pass" value="(.+?)"', data
                ).group(1)

                # Extract the arithmetic operation
                js = re.search(
                    r"setTimeout\(function\(\){\s+(var s,t,o,p,b,r,e,a,k,i,n,g,f.+?\r?\n[\s\S]+?a\.value =.+?)\r?\n",
                    data,
                ).group(1)
                js = re.sub(r"a\.value = (parseInt\(.+?\)).+", r"\1", js)
                js = re.sub(r"\s{3,}[a-z](?: = |\.).+", "", js)
                js = re.sub(r"[\n\\']", "", js)

            except Exception:
                # Something is wrong with the page.
                # This may indicate CloudFlare has changed their anti-bot
                # technique.
                owner_plugin.log_error(
                    addon_plugin._("Unable to parse CloudFlare's DDoS protection page")
                )
                return None  #: Tell the exception handler to re-throw the exception

            # Safely evaluate the Javascript expression
            get_params["jschl_answer"] = str(int(eval_js(js)) + len(domain))

            owner_plugin.wait()  #: Do the actual wait

            return owner_plugin.load(submit_url, get=get_params, ref=last_url)

        except Exception as exc:
            addon_plugin.log_error(exc)
            return None  #: Tell the exception handler to re-throw the exception

    @staticmethod
    def _solve_cf_security_check(addon_plugin, owner_plugin, data):
        try:
            last_url = owner_plugin.req.last_effective_url

            captcha = ReCaptcha(owner_plugin.pyfile)

            captcha_key = captcha.detect_key(data)
            if captcha_key:
                addon_plugin.log_info(
                    addon_plugin._("Detected CloudFlare's security check page")
                )

                response, challenge = captcha.challenge(captcha_key, data)
                return owner_plugin.load(
                    owner_plugin.fixurl("/cdn-cgi/l/chk_captcha"),
                    get={"g-recaptcha-response": response},
                    ref=last_url,
                )

            else:
                addon_plugin.log_warning(
                    addon_plugin._("Got unexpected CloudFlare html page")
                )
                return None  #: Tell the exception handler to re-throw the exception

        except Exception as exc:
            addon_plugin.log_error(exc)
            return None  #: Tell the exception handler to re-throw the exception


class PreloadStub:
    def __init__(self, addon_plugin, owner_plugin):
        self.addon_plugin = addon_plugin
        self.owner_plugin = owner_plugin
        self.old_preload = owner_plugin._preload

    def my_preload(self, *args, **kwargs):
        data = CloudFlare.handle_function(
            self.addon_plugin,
            self.owner_plugin,
            "_preload",
            self.old_preload,
            (args, kwargs),
        )
        if data is not None:
            self.owner_plugin.data = data

    def __repr__(self):
        return "<PreloadStub object at {}>".format(hex(id(self)))


class CloudFlareDdos(BaseAddon):
    __name__ = "CloudFlareDdos"
    __type__ = "addon"
    __version__ = "0.13"
    __status__ = "testing"

    __config__ = [("enabled", "bool", "Activated", False)]

    __description__ = """CloudFlare DDoS protection support"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    def activate(self):
        self.stubs = {}
        self._override_get_url()

    def deactivate(self):
        while len(self.stubs):
            stub = next(iter(self.stubs.values()))
            self._unoverride_preload(stub.owner_plugin)

        self._unoverride_get_url()

    def _unoverride_preload(self, plugin):
        if id(plugin) in self.stubs:
            self.log_debug(f"Unoverriding _preload() for {plugin_id(plugin)}")

            stub = self.stubs.pop(id(plugin))
            stub.owner_plugin._preload = stub.old_preload

        else:
            self.log_warning(
                self._(
                    "No _preload() override found for {}, cannot un-override>"
                ).format(plugin_id(plugin))
            )

    def _override_preload(self, plugin):
        if id(plugin) not in self.stubs:
            stub = PreloadStub(self, plugin)
            self.stubs[id(plugin)] = stub

            self.log_debug(f"Overriding _preload() for {plugin_id(plugin)}")
            plugin._preload = stub.my_preload

        else:
            self.log_warning(
                self._("Already overrided _preload() for {}").format(plugin_id(plugin))
            )

    def _override_get_url(self):
        self.log_debug("Overriding get_url()")

        self.old_get_url = self.pyload.request_factory.get_url
        self.pyload.request_factory.get_url = self.my_get_url

    def _unoverride_get_url(self):
        self.log_debug("Unoverriding get_url()")

        self.pyload.request_factory.get_url = self.old_get_url

    def _find_owner_plugin(self):
        """
        Walk the callstack until we find SimpleDownloader or SimpleDecrypter class Dirty but
        works.
        """
        f = frame = inspect.currentframe()
        try:
            while True:
                if f is None:
                    return None

                elif "self" in f.f_locals and is_simple_plugin(f.f_locals["self"]):
                    return f.f_locals["self"]

                else:
                    f = f.f_back

        finally:
            del frame

    def download_preparing(self, pyfile):
        #: Only SimpleDownloader and SimpleDecrypter based plugins are supported
        if not is_simple_plugin(pyfile.plugin):
            self.log_debug(f"Skipping plugin {plugin_id(pyfile.plugin)}")
            return

        attr = getattr(pyfile.plugin, "_preload", None)
        if not attr and not callable(attr):
            self.log_error(
                self._("{} is missing _preload() function, cannot override!").format(
                    plugin_id(pyfile.plugin)
                )
            )
            return

        self._override_preload(pyfile.plugin)

    def download_processed(self, pyfile):
        if id(pyfile.plugin) in self.stubs:
            self._unoverride_preload(pyfile.plugin)

    def my_get_url(self, *args, **kwargs):
        owner_plugin = self._find_owner_plugin()
        if owner_plugin is None:
            self.log_warning(self._("Owner plugin not found, cannot process"))
            return self.old_get_url(*args, **kwargs)

        else:
            # NOTE: Better use owner_plugin.load() instead of get_url() so cookies are saved and so captcha credits
            # NOTE: Also that way we can use 'owner_plugin.req.header' to get the
            # headers, otherwise we cannot get them
            res = CloudFlare.handle_function(
                self, owner_plugin, "get_url", owner_plugin.load, (args, kwargs)
            )
            if kwargs.get("just_header", False):
                # NOTE: SimpleDownloader/SimpleDecrypter returns a dict while get_url() returns raw headers string,
                # make sure we return a string for get_url('just_header'=True)
                res = get_plugin_last_header(owner_plugin)

            return res
