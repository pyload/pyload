#!/bin/sh
rm -rf thriftgen

# use thrift 0.7.0 from trunk
# patched if needed https://issues.apache.org/jira/browse/THRIFT-1115?page=com.atlassian.jira.plugin.system.issuetabpanels%3Achangehistory-tabpanel#issue-tabs
# --gen py:slots,dynamic

thrift -strict -v --gen py --gen java pyload.thrift
mv gen-py thriftgen
