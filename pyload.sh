#!/bin/sh
#find src/ -name __pycache__ | xargs rm -rf
export PYTHONPATH=$PWD/src:$PYTHONPATH
set -x
exec python3 -m src.pyload "$@"
