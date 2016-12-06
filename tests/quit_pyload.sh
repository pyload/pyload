#!/bin/bash
PYTHON=python
which python2 > /dev/null && PYTHON=python2
$PYTHON pyload.py --configdir=tests/config --quit
if [ -d userplugins ]; then
    rm -r userplugins
fi
