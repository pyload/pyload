# -*- coding: utf-8 -*-

""" Store all usefull functions here """

import sys
from os.path import join

def save_join(*args):
    """ joins a path, encoding aware """
    paths = []
    for path in args:
        # remove : for win comp.
        tmp = path.replace(":", "").encode(sys.getfilesystemencoding(), "replace")
        paths.append(tmp)
    return join(*paths)

if __name__ == "__main__":
    print save_join("test","/test2")