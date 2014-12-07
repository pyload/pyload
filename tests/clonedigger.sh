#!/bin/sh

PYLOAD="../pyload"  # Check pyload directory
clonedigger -o cpd.xml --cpd-output --fast --ignore-dir="remote" ${PYLOAD}
