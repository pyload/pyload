#!/bin/sh
rm -rf thriftgen
thrift --gen py pyload.thrift
mv gen-py thriftgen
