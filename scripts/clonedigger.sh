#!/bin/sh

PYLOAD="../module"  # Check ~/pyload/module directory
clonedigger -o cpd.xml --cpd-output --fast --ignore-dir="lib" --ignore-dir="remote" $PYLOAD
