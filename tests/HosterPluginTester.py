# -*- coding: utf-8 -*-

from os import remove
from os.path import dirname
from logging import log, DEBUG
from hashlib import md5
from time import time

from nose.tools import nottest

from helper.Stubs import Core
from helper.PluginTester import PluginTester

from module.PyFile import PyFile
from module.plugins.Base import Fail
from module.utils import accumulate
from module.utils.fs import save_join, join, exists

DL_DIR = join("Downloads", "tmp")

class HosterPluginTester(PluginTester):

    files = {}

    def setUp(self):
        PluginTester.setUp(self)
        for f in self.files:
            pass
            if exists(join(DL_DIR, f)): remove(join(DL_DIR, f))

    @nottest
    def test_plugin(self, name, url, flag):

        # Print to stdout to see whats going on
        print "%s: %s" % (name, url)
        log(DEBUG, "%s: %s", name, url)

        # url and plugin should be only important thing
        pyfile = PyFile(self.core, -1, url, url, 0, 0, "", name, 0, 0)
        pyfile.initPlugin()

        self.thread.pyfile = pyfile
        self.thread.plugin = pyfile.plugin

        try:
            a = time()
            pyfile.plugin.preprocessing(self.thread)


            log(DEBUG, "downloading took %ds" % (time()-a))
            log(DEBUG, "size %d kb" % (pyfile.size / 1024))

            if pyfile.name not in self.files:
                raise Exception("Filename %s wrong." % pyfile.name)

            if not exists(save_join(DL_DIR, pyfile.name)):
                raise Exception("File %s does not exists." % pyfile.name)

            hash = md5()
            f = open(save_join(DL_DIR, pyfile.name))
            while True:
                buf = f.read(4096)
                if not buf: break
                hash.update(buf)

            if hash.hexdigest() != self.files[pyfile.name]:
                raise Exception("Hash does not match.")



        except Exception, e:
            if isinstance(e, Fail) and flag == "fail":
                pass
            elif isinstance(e, Fail) and flag == "offline" and e.message == "offline":
                pass
            else:
                raise


# setup methods

c = Core()

f = open(join(dirname(__file__), "hosterlinks.txt"))
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

    elif len(l.split(" ")) == 2:
        name, hash = l.split(" ")
        HosterPluginTester.files[name] = hash


hoster, c = c.pluginManager.parseUrls(urls)

plugins = accumulate(hoster)
for plugin, urls in plugins.iteritems():

    for i, url in enumerate(urls):


        def meta(plugin, url, flag, sig):
            def _test(self):
                self.test_plugin(plugin, url, flag)

            _test.func_name = sig
            return _test

        sig = "test_%s_LINK%d" % (plugin, i)
        setattr(HosterPluginTester, sig, meta(plugin, url, flags.get(url, None), sig))