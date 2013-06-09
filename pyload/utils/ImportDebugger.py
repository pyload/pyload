# -*- coding: utf-8 -*-

import sys

class ImportDebugger(object):

    def __init__(self):
        self.imported = {}

    def find_module(self, name, path=None):

        if name not in self.imported:
            self.imported[name] = 0

        self.imported[name] += 1

        print name, path

sys.meta_path.append(ImportDebugger())