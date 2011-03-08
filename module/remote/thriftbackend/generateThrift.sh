#!/bin/sh
rm -rf thriftgen
thrift -strict -v --gen py --gen java pyload.thrift
mv gen-py thriftgen
