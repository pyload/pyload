# -*- coding: utf-8 -*-

import os
import os.path
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


class SevenZipUnRarTester(unittest.TestCase):
    # test case setup
    dir_rar_output = pyload_root + '/tests/tmp'
    file_rar_pass = 'test'
    file_test_this = '7z_this.txt'
    file_test_other = '7z_other.txt'
    file_test_content = [dir_rar_output + '/' + file_test_this, dir_rar_output + '/' + file_test_other]
    file_rar_unprotected = pyload_root + '/tests/assets/7z_test.rar' # without password
    file_rar_pass_protected = pyload_root + '/tests/assets/7z_test-p.rar' # with password & without encrypted header
    file_rar_pass_and_header_protected = pyload_root + '/tests/assets/7z_test-hp.rar' # with password & with encrypted header

    def setUp(self):
        self.klass = plugin.SevenZipUnRar
        self.instance = plugin.SevenZipUnRar(Noop.getInstance(), self.file_rar_unprotected, self.dir_rar_output, True, True, 0)
        self.instance.init()
        for file in self.file_test_content:
            try:
                os.unlink(file)
            except OSError:
                pass

    def tearDown(self):
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