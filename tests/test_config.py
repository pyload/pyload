# -*- coding: utf-8 -*-
from module import ConfigParser
import os


class TestConfig:

    def setUp(self):
        ConfigParser.pypath = ".."
        self.config = ConfigParser.ConfigParser()

    def teardown(self):
        os.unlink('pyload.conf')
        os.unlink('plugin.conf')

    def test_read(self):
        assert self.config.get('webinterface', 'template') == 'modern'
        assert self.config.get('remote', 'port') == 7227

    def test_write(self):
        self.config.set('proxy','username', 'Mäf')
        assert self.config.get('proxy', 'username') == u'Mäf'