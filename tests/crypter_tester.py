# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import os
from builtins import int
from logging import DEBUG, log

from future import standard_library

from nose.tools import nottest
from pyload.core.plugin.base import Fail
from pyload.utils.convert import accumulate, to_int
from pyload.utils.fs import bufread, lopen
from tests.helper.plugintester import PluginTester
from tests.helper.stubs import Core

standard_library.install_aliases()


class CrypterPluginTester(PluginTester):

    @nottest
    def test_plugin(self, name, url, flag):

        print("{0}: {1}".format(name, url))
        log(DEBUG, "{0}: {1}".format(name, url))

        plugin = self.pyload.pgm.get_plugin_class("crypter", name)
        thd = plugin(self.pyload, None, "")
        self.thread.plugin = thd

        try:
            result = thd._decrypt([url])

            if to_int(flag):
                assert int(flag) == len(result)

        except Exception as e:
            if isinstance(e, Fail) and flag == "fail":
                pass
            else:
                raise


# setup methods

c = Core()

urls = []
flags = {}

crypterlinks = os.path.join(os.path.dirname(__file__), "crypterlinks.txt")
with lopen(crypterlinks) as fp:
    links = (line.strip() for line in bufread(fp, buffering=1))
    for l in links:
        if not l or l.startswith("#"):
            continue
        if l.startswith("http"):
            if "||" in l:
                l, flag = l.split("||")
                flags[l] = flag
            urls.append(l)

h, crypter = c.pgm.parse_urls(urls)
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

        sig = "test_LINK{0:d}".format(i)
        setattr(_testerClass, sig, meta(
            plugin, url, flags.get(url, None), sig))
        print(url)

    locals()[plugin] = _testerClass
    del _testerClass
