#!/bin/bash

sloccount --duplicates --wide --details pyload > sloccount.sc

echo "Running pep8"
pep8 pyload > pep8.txt

echo "Running pylint"
pylint --reports=no pyload > pylint.txt || exit 0

#echo "Running pyflakes"
# pyflakes to pylint syntak
#find -name '*.py' |egrep -v '^.(/tests/|/pyload/lib)'|xargs pyflakes  > pyflakes.log || :
# Filter warnings and strip ./ from path
#cat pyflakes.log | awk -F\: '{printf "%s:%s: [E]%s\n", $1, $2, $3}' | grep -i -E -v "'_'|COREDIR|webinterface|REQUEST|addonmanager" > pyflakes.txt
#sed -i 's/^.\///g' pyflakes.txt
