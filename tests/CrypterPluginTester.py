# -*- coding: utf-8 -*-

from os.path import dirname, join
from nose.tools import nottest

from logging import log, DEBUG

from helper.Stubs import Core
from helper.PluginTester import PluginTester

from module.plugins.Base import Fail
from module.utils import accumulate, to_int

class CrypterPluginTester(PluginTester):
    @nottest
    def test_plugin(self, name, url, flag):

        print "%s: %s" % (name, url.encode("utf8"))
        log(DEBUG, "%s: %s", name, url.encode("utf8"))

        plugin = self.core.pluginManager.getPluginClass(name)
        p = plugin(self.core, None, "")
        self.thread.plugin = p

        try:
            result = p._decrypt([url])

            if to_int(flag):
                assert to_int(flag) == len(result)

        except Exception, e:
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

h, crypter = c.pluginManager.parseUrls(urls)
plugins = accumulate(crypter)
for plugin, urls in plugins.iteritems():

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

            _test.func_name = sig
            return _test

        sig = "test_LINK%d" % i
        setattr(_testerClass, sig, meta(plugin, url, flags.get(url, None), sig))
        print url

    locals()[plugin] = _testerClass
    del _testerClass
