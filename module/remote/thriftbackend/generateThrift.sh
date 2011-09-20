#!/bin/sh
rm -rf thriftgen

# use thrift from trunk or a release with dynamic/slots python code generation

thrift -strict -v --gen py --gen java pyload.thrift
mv gen-py thriftgen
