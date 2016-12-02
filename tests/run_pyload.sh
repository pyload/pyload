#!/usr/bin/env bash

PIDFILE="tests/pyload.pid"
if [ -f "$PIDFILE" ]
then
    kill -9 $(<"$PIDFILE")
fi

cp tests/config/pyload.db.org tests/config/pyload.db
cp tests/config/pyload.conf.org tests/config/pyload.conf

PYTHON=python
which python2 > /dev/null && PYTHON=python2

touch pyload.out
$PYTHON pyload.py -d --configdir=tests/config > pyload.out 2> pyload.err &

for i in {1..30}; do
    grep "pyLoad is up and running" pyload.out > /dev/null && echo "pyLoad started" && break
    sleep 1
done

echo "pyLoad start script finished"
