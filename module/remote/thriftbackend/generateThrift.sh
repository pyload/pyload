#!/bin/sh
rm -rf thriftgen

# use thrift from trunk or a release with dynamic/slots python code generation

thrift -v --strict --gen py:slots,dynamic --gen java pyload.thrift
mv gen-py thriftgen
