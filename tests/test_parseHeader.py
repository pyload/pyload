# -*- coding: utf-8 -*-

from nose.tools import nottest
from collections import namedtuple

import common_init
from module.network.HTTPChunk import HTTPChunk

class DummyHTTPDownload:
    pass

class test_parseHeader(HTTPChunk):
    def __init__(self):
        # Prevents initialization of parent object
        pass

    def setUp(self):
        # Dummy initialization
        self.log = common_init.log #Logger
        self.p = DummyHTTPDownload() #Dummy parent class
        self.resume = False #See HTTPCunk __init__ code
        self.headerParsed = False

    def test_parseHeader_1(self):
        self.header = """content-length: 666\r\n"""
        self.parseHeader()
        assert self.headerParsed == True
        assert self.p.size == 666

    def test_parseHeader_2(self):
        self.header = """content-disposition: dummy; filename="test file"; filename*=''UTF-8%20test%20file.bin\r\n"""
        self.parseHeader()
        assert self.headerParsed == True
        assert self.p.nameDisposition == "test file"

    def test_parseHeader_3(self):
        self.header = """content-disposition: dummy; filename="test file"\r\n"""
        self.parseHeader()
        assert self.headerParsed == True
        assert self.p.nameDisposition == "test file"

    def tearDown(self):
        pass

