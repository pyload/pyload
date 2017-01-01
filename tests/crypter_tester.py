# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
from os.path import dirname, join
from nose.tools import nottest

from logging import log, DEBUG

from tests.helper.stubs import Core
from tests.helper.plugintester import PluginTester

from pyload.plugins.base import Fail
from pyload.utils import accumulate, to_int


class CrypterPluginTester(PluginTester):
    @nottest
    def test_plugin(self, name, url, flag):

        print("{}: {}".format(name, url.encode("utf8")))
        log(DEBUG, "{}: {}".format(name, url.encode("utf8")))

        plugin = self.pyload.pluginmanager.getPluginClass("crypter", name)
        p = plugin(self.pyload, None, "")
        self.thread.plugin = p

        try:
            result = p._decrypt([url])

            if to_int(flag):
                assert to_int(flag) == len(result)

        except Exception as e:
            if isinstance(e, Fail) and flag == "fail":
                pass
            else:
                raise


# setup methods

c = Core()

f = open(join(dirname(__file__), "crypterlinks.txt"))
links = [x.strip() for x in f.readlines()]
urls = []
flags = {}

for l in links:
    if not l or l.startswith("#"): continue
    if l.startswith("http"):
        if "||" in l:
            l, flag = l.split("||")
            flags[l] = flag

        urls.append(l)

h, crypter = c.pluginmanager.parseUrls(urls)
plugins = accumulate(crypter)
for plugin, urls in plugins.items():

    def meta_class(plugin):
        class _testerClass(CrypterPluginTester):
            pass
        _testerClass.__name__ = plugin
        return _testerClass

    _testerClass = meta_class(plugin)

    for i, url in enumerate(urls):
        def meta(plugin, url, flag, sig):
            def _test(self):
                self.test_plugin(plugin, url, flag)

            _test.__name__ = sig
            return _test

        sig = "test_LINK{:d}".format(i)
        setattr(_testerClass, sig, meta(plugin, url, flags.get(url, None), sig))
        print(url)

    locals()[plugin] = _testerClass
    del _testerClass
