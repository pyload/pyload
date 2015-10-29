# -*- coding: utf-8 -*-

import __builtin__

# Quick and dirty logger
import logging
import logging.handlers
import sys
from os.path import join
log = logging.getLogger("log")
console = logging.StreamHandler(sys.stdout)
frm = logging.Formatter("%(asctime)s %(levelname)-8s  %(message)s", "%d.%m.%Y %H:%M:%S")
console.setFormatter(frm)
log.addHandler(console) #if console logging
file_handler = logging.FileHandler('log.txt', encoding="utf8")
file_handler.setFormatter(frm)
log.addHandler(file_handler)
log.setLevel(logging.DEBUG)

# Prepare some dummy requirements for module importing
__builtin__._ = lambda x: x

