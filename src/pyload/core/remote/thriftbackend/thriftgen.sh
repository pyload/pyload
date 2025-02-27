#!/bin/sh

set -eux

if ! command -v thrift; then
  echo error: missing package thrift-compiler
  exit 1
fi

cd "$(dirname "$0")"

mkdir -p thriftgen
rm -rf thriftgen/* || true

rm -rf gen || true
mkdir gen

thrift -r --gen py:slots,dynamic -out gen pyload.thrift

mv gen/pyload/* thriftgen
rm -rf gen

cd thriftgen

mv Pyload.py pyload.py
mv Pyload-remote pyload-remote

patch -p1 <<EOF
--- a/pyload-remote
+++ b/pyload-remote
@@ -19,2 +19,2 @@
-from pyload import Pyload
-from pyload.ttypes import *
+from . import pyload as Pyload
+from .ttypes import *
EOF

chmod +x pyload-remote
