#!/bin/bash
PYTHON=python
which python2 > /dev/null && PYTHON=python2
$PYTHON pyLoadCore.py --configdir=tests/config --quit
