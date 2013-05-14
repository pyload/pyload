# -*- coding: utf-8 -*-

import binascii
import os
import os.path
import re
import sys

import unittest

pyload_root = os.path.dirname(os.path.abspath(__file__ + '/..'))
print ""
print "Using pyLoad-Root: " + pyload_root
print "----------------------------------------------------------------------"
sys.path.append(pyload_root)

import module.plugins.internal.SevenZipUnRar as plugin


class Noop:
    instance = None

    @classmethod
    def getInstance(cls):
        if cls.instance == None:
            cls.instance = cls()
        return cls.instance

    def noop(self, *args, **kwargs):
        pass

    def __getattr__(self, item):
        return self.noop


file_rar_unprotected_bin = binascii.unhexlify(re.sub(r'\s+', '', '''
5261 7221 1a07 00cf 9073 0000 0d00 0000
0000 0000 dc56 7420 802c 0019 0000 000d
0000 0003 dbdb 7ac0 c5a5 ac42 1d33 0c00
a481 0000 377a 5f6f 7468 6572 2e74 7874
0811 0bec cb76 14b1 b623 e0e1 e1c0 8dfc
6ffb 5a6c 93b1 6d47 a0e6 8a74 2090 2d00
1800 0000 0c00 0000 03f8 c1e1 9ed5 a5ac
421d 330b 00a4 8100 0037 7a5f 7468 6973
2e74 7874 00c0 0800 cbec cbf6 14e8 db11
4360 c0f0 b7f1 bffd 56de 4f15 a23d c43d
7b00 4007 00
''')) # without password

file_rar_pass_protected_bin = binascii.unhexlify(re.sub(r'\s+', '', '''
5261 7221 1a07 00cf 9073 0000 0d00 0000
0000 0000 5998 7424 8434 0020 0000 000d
0000 0003 dbdb 7ac0 c5a5 ac42 1d33 0c00
a481 0000 377a 5f6f 7468 6572 2e74 7874
7853 3f95 9103 c873 437d e375 8ab0 f500
82f7 8d3d 0863 1bda 40e3 be87 2d6c 482b
1a87 a1d9 d510 921f 7da2 7424 9435 0020
0000 000c 0000 0003 f8c1 e19e d5a5 ac42
1d33 0b00 a481 0000 377a 5f74 6869 732e
7478 7478 533f 9591 03c8 7300 c00a 8218
9b23 9be5 0153 409c ede2 7101 a2e7 115d
dea5 4653 f78a e3db 2228 fe21 86c4 3d7b
0040 0700
''')) # password is: test

file_rar_pass_and_header_protected_bin = binascii.unhexlify(re.sub(r'\s+', '', '''
5261 7221 1a07 00ce 9973 8000 0d00 0000
0000 0000 09b5 7cf9 8949 076f aac1 f3c9
00eb fa38 ac66 2194 7431 b718 fa5f 28f9
2c9f 5a9f 2838 6027 296d 71b2 7995 2d60
d46b 5f00 9ad4 f138 c1d7 db6d cf7b d017
846b 7e58 1edd 27b7 c6c0 88fd d10e a64b
9ded b1b2 00a4 f6f1 3563 becb dc4d bca6
6869 bc27 6759 10c2 a5be c7a2 09b5 7cf9
8949 076f 5781 dab6 59b3 1dff d6ba 9acd
3cce 5a71 aa19 4e25 71b9 e4b7 7497 7e90
25b1 b736 7ea8 ee48 7532 0e04 1660 9247
59eb c382 efa2 70a6 e4b4 6e5f 32cd c35e
ae77 f373 7695 939b fe0b 2e83 ba4a d399
a861 1e5d 5781 1b3d 13aa 0aa9 8093 53e5
cbab c876 09b5 7cf9 8949 076f 9087 29f2
0c3a b447 dcc4 9afc 3961 6d83
''')) # password is: test


class SevenZipUnRarTester(unittest.TestCase):
    # test case setup
    dir_rar_output = pyload_root + '/tests/tmp'
    file_rar_pass = 'test'
    file_test_this = '7z_this.txt'
    file_test_other = '7z_other.txt'
    file_test_content = [dir_rar_output + '/' + file_test_this, dir_rar_output + '/' + file_test_other]
    file_rar_unprotected = pyload_root + '/tests/tmp/7z_test.rar' # without password
    file_rar_pass_protected = pyload_root + '/tests/tmp/7z_test-p.rar' # with password & without encrypted header
    file_rar_pass_and_header_protected = pyload_root + '/tests/tmp/7z_test-hp.rar' # with password & with encrypted header

    @classmethod
    def setUpClass(cls):
        file_rar = open(cls.file_rar_unprotected, 'wb')
        file_rar.write(file_rar_unprotected_bin)
        file_rar.close()
        file_rar = open(cls.file_rar_pass_protected, 'wb')
        file_rar.write(file_rar_pass_protected_bin)
        file_rar.close()
        file_rar = open(cls.file_rar_pass_and_header_protected, 'wb')
        file_rar.write(file_rar_pass_and_header_protected_bin)
        file_rar.close()
        return

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.file_rar_unprotected)
        os.unlink(cls.file_rar_pass_protected)
        os.unlink(cls.file_rar_pass_and_header_protected)
        return

    def setUp(self):
        self.klass = plugin.SevenZipUnRar
        self.instance = plugin.SevenZipUnRar(Noop.getInstance(), self.file_rar_unprotected, self.dir_rar_output, True, True, 0)
        self.instance.init()
        return

    def tearDown(self):
        for file in self.file_test_content:
            try:
                os.unlink(file)
            except OSError:
                pass
        return

    def testCheckDeps(self):
        if os.name != "nt":
            code = os.system("which 7z >/dev/null 2>&1")
            if code == 0:
                self.assertTrue(self.klass.checkDeps())
            else:
                self.assertFalse(self.klass.checkDeps())
        else:
            self.assertFalse(self.klass.checkDeps())

    def testGetTargetsBasic(self):
        possible_targets = [('test.rar', 1), ('test.part01.rar', 2), ('test.r01', 3)]
        noise_targets = [('test.rar.no', 4), ('test.part01.no', 5), ('test.part01.rar.no', 6), ('test.r01.no', 7)]
        targets = self.klass.getTargets(possible_targets + noise_targets)
        self.assertEqual(possible_targets, targets)

    def testGetTargetsExtended(self):
        possible_targets = [('test.rar', 1), ('test.part01.rar', 2), ('test.r01', 3)]
        noise_targets = [('test.part02.rar', 4), ('test.part03.rar', 5), ('test.r02', 6), ('test.r03', 7)]
        targets = self.klass.getTargets(possible_targets + noise_targets)
        self.assertEqual(possible_targets, targets)

    def testCheckArchiveUnprotected(self):
        self.instance.file = self.file_rar_unprotected
        self.assertFalse(self.instance.checkArchive())
        self.assertFalse(self.instance.passwordProtected)
        self.assertFalse(self.instance.headerProtected)

    def testCheckArchivePassProtected(self):
        self.instance.file = self.file_rar_pass_protected
        self.assertTrue(self.instance.checkArchive())
        self.assertTrue(self.instance.passwordProtected)
        self.assertFalse(self.instance.headerProtected)

    def testCheckArchivePassAndHeaderProtected(self):
        self.instance.file = self.file_rar_pass_and_header_protected
        self.assertTrue(self.instance.checkArchive())
        self.assertTrue(self.instance.passwordProtected)
        self.assertTrue(self.instance.headerProtected)

    def testCheckPasswordUnprotected(self):
        self.instance.file = self.file_rar_unprotected
        self.instance.checkArchive()
        self.assertTrue(self.instance.checkPassword(""))
        self.assertTrue(self.instance.checkPassword(self.file_rar_pass)) # even if a password is set

    def testCheckPasswordPassProtected(self):
        self.instance.file = self.file_rar_pass_protected
        self.instance.checkArchive()
        self.assertTrue(self.instance.checkPassword("")) # yes, that's true :()
        self.assertTrue(self.instance.checkPassword(self.file_rar_pass))

    def testCheckPasswordPassAndHeaderProtected(self):
        self.instance.file = self.file_rar_pass_and_header_protected
        self.instance.checkArchive()
        self.assertFalse(self.instance.checkPassword(""))
        self.assertTrue(self.instance.checkPassword(self.file_rar_pass))

    def testListContent(self):
        self.instance.file = self.file_rar_unprotected
        self.instance.checkArchive()
        self.instance.listContent()
        self.assertEqual(set(self.file_test_content), self.instance.files)

    def testExtract(self):
        self.instance.file = self.file_rar_unprotected
        self.instance.extract(Noop.getInstance().noop, None)
        for file in self.file_test_content:
            self.assertTrue(os.path.exists(file))


if __name__ == '__main__':
    unittest.main()