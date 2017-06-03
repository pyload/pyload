# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import os
import shutil
import time
from builtins import str
from hashlib import md5
from logging import DEBUG, log

from future import standard_library

from nose.tools import nottest
from pyload.core.datatype import File
from pyload.core.datatype.file import statusmap
from pyload.core.plugin.base import Fail
from pyload.utils.convert import accumulate
from pyload.utils.fs import lopen, remove
from tests.helper.parser import parse_config
from tests.helper.plugintester import PluginTester
from tests.helper.stubs import Core

standard_library.install_aliases()


DL_DIR = "Storage"


class HosterPluginTester(PluginTester):
    files = {}

    def setUp(self):
        PluginTester.setUp(self)
        for fname in self.files:
            path = os.path.join(DL_DIR, fname)
            remove(path, trash=True, ignore_errors=True)

        # folder for reports
        report = os.path.join(self.__class__.__name__)
        if not os.path.exists(report):
            return None
        for fname in os.listdir(report):
            path = os.path.join(report, fname)
            remove(path, trash=True)

    @nottest
    def test_plugin(self, name, url, status):
        # Print to stdout to see whats going on
        print("{0}: {1}, {2}".format(name, url, status))
        log(DEBUG, "{0}: {1}, {2}".format(name, url, status))

        # url and plugin should be only important thing
        file = File(self.pyload, -1, url, url, 0, 0,
                    0, 0, url, name, "", 0, 0, 0, 0)
        file.init_plugin()

        self.thread.file = file
        self.thread.plugin = file.plugin

        try:
            a = time.time()
            file.plugin.preprocessing(self.thread)

            log(DEBUG, "downloading took {0:d}s".format(time.time() - a))
            log(DEBUG, "size {0:d} KiB".format(file.size >> 10))

            if status == "offline":
                raise Exception("No offline Exception raised")

            if file.name not in self.files:
                raise Exception(
                    "Filename {0} not recognized".format(file.name))

            hash = md5()
            path = os.path.join(DL_DIR, file.name)

            if not os.path.exists(path):
                raise Exception("File {0} does not exists".format(file.name))

            with lopen(path, mode='rb') as fp:
                while True:
                    buf = fp.read(4096)
                    if not buf:
                        break
                    hash.update(buf)

            if hash.hexdigest() != self.files[file.name]:
                log(DEBUG, "Hash is {0}".format(hash.hexdigest()))

                size = os.stat(fp.name).st_size
                if size < 10 << 20:  # 10MB
                    # Copy for debug report
                    log(DEBUG, "Downloaded file copied to report")
                    shutil.move(fp.name, os.path.join(plugin, fp.name))

                raise Exception("Hash does not match")

        except Exception as e:
            if isinstance(e, Fail) and status == "failed":
                pass
            elif isinstance(e, Fail) and status == "offline" and str(e) == "offline":
                pass
            else:
                raise


# setup methods
c = Core()

hosterlinks = os.path.join(os.path.dirname(__file__), "hosterlinks.txt")
sections = parse_config(hosterlinks)

for link in sections['files']:
    name, hash = link.rsplit(" ", 1)
    HosterPluginTester.files[name] = str(hash)

del sections['files']

urls = []
status = {}

for k, v in sections.items():
    if k not in statusmap:
        print("Unknown status {0}".format(k))
    for url in v:
        urls.append(url)
        status[url] = k

hoster, c = c.pgm.parse_urls(urls)

plugins = accumulate(hoster)
for plugin, urls in plugins.items():
    # closure functions to retain local scope
    def meta_class(plugin):
        class _testerClass(HosterPluginTester):
            pass
        _testerClass.__name__ = plugin
        return _testerClass

    _testerClass = meta_class(plugin)

    for i, url in enumerate(urls):
        def meta(__plugin, url, status, sig):
            def _test(self):
                self.test_plugin(__plugin, url, status)

            _test.__name__ = sig
            return _test

        tmp_status = status.get(url)
        if tmp_status != "online":
            sig = "test_LINK{0:d}_{1}".format(i, tmp_status)
        else:
            sig = "test_LINK{0:d}".format(i)

        # set test method
        setattr(_testerClass, sig, meta(plugin, url, tmp_status, sig))

    # register class
    locals()[plugin] = _testerClass
    # remove from locals, or tested twice
    del _testerClass
