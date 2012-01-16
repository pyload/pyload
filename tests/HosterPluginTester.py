# -*- coding: utf-8 -*-

from os.path import dirname
from logging import log, DEBUG
from hashlib import md5
from time import time
from shutil import move
import codecs

from nose.tools import nottest

from helper.Stubs import Core
from helper.PluginTester import PluginTester

from module.PyFile import PyFile
from module.plugins.Base import Fail
from module.utils import accumulate
from module.utils.fs import save_join, join, exists, listdir, remove, stat, fs_encode

DL_DIR = join("Downloads", "tmp")

class HosterPluginTester(PluginTester):
    files = {}

    def setUp(self):
        PluginTester.setUp(self)
        for f in self.files:
            if exists(save_join(DL_DIR, f)): remove(save_join(DL_DIR, f))

        # folder for reports
        report = join("tmp", self.__class__.__name__)
        if exists(report):
            for f in listdir(report):
                remove(join(report, f))


    @nottest
    def test_plugin(self, name, url, flag):
        # Print to stdout to see whats going on
        print "%s: %s, %s" % (name, url, flag)
        log(DEBUG, "%s: %s, %s", name, url, flag)

        # url and plugin should be only important thing
        pyfile = PyFile(self.core, -1, url, url, 0, 0, "", name, 0, 0)
        pyfile.initPlugin()

        self.thread.pyfile = pyfile
        self.thread.plugin = pyfile.plugin

        try:
            a = time()
            pyfile.plugin.preprocessing(self.thread)

            log(DEBUG, "downloading took %ds" % (time() - a))
            log(DEBUG, "size %d kb" % (pyfile.size / 1024))

            if flag == "offline":
                raise Exception("No offline Exception raised.")

            if pyfile.name not in self.files:
                raise Exception("Filename %s not recognized." % pyfile.name)

            if not exists(save_join(DL_DIR, pyfile.name)):
                raise Exception("File %s does not exists." % pyfile.name)

            hash = md5()
            f = open(save_join(DL_DIR, pyfile.name), "rb")
            while True:
                buf = f.read(4096)
                if not buf: break
                hash.update(buf)
            f.close()

            if hash.hexdigest() != self.files[pyfile.name]:
                log(DEBUG, "Hash is %s" % hash.hexdigest())
                
                size = stat(f.name).st_size
                if size < 1024 * 1024 * 10: # 10MB
                    # Copy for debug report
                    move(fs_encode(f.name), fs_encode(join("tmp", plugin, f.name)))

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

# decode everything as unicode
f = codecs.open(join(dirname(__file__), "hosterlinks.txt"), "r", "utf_8")
links = [x.strip() for x in f.readlines()]
urls = []
flags = {}

for l in links:
    if not l or l.startswith("#"): continue
    if l.startswith("http"):
        if "||" in l:
            l, flag = l.split("||")
            flags[l] = str(flag.strip())
        urls.append(l)

    elif len(l.rsplit(" ", 1)) == 2:
        name, hash = l.rsplit(" ", 1)
        HosterPluginTester.files[name] = str(hash)

hoster, c = c.pluginManager.parseUrls(urls)

plugins = accumulate(hoster)
for plugin, urls in plugins.iteritems():
    # closure functions to retain local scope
    def meta_class(plugin):
        class _testerClass(HosterPluginTester):
            pass
        _testerClass.__name__ = plugin
        return _testerClass

    _testerClass = meta_class(plugin)

    for i, url in enumerate(urls):
        def meta(__plugin, url, flag, sig):
            def _test(self):
                self.test_plugin(__plugin, url, flag)

            _test.func_name = sig
            return _test

        tmp_flag = flags.get(url, None)
        if flags.get(url, None):
            sig = "test_LINK%d_%s" % (i, tmp_flag)
        else:
            sig = "test_LINK%d" % i

        # set test method
        setattr(_testerClass, sig, meta(plugin, url, tmp_flag, sig))


    #register class
    locals()[plugin] = _testerClass
    # remove from locals, or tested twice
    del _testerClass
