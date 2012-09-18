#!/bin/bash
find -name '*.py' |egrep -v '^.(/tests/|/module/lib)'|xargs pyflakes  > pyflakes.log || :
# Filter warnings and strip ./ from path
cat pyflakes.log | awk -F\: '{printf "%s:%s: [E]%s\n", $1, $2, $3}' | grep -i -E -v "'_'|pypath|webinterface|pyreq|hookmanager" > pyflakes.txt
sed -i 's/^.\///g' pyflakes.txt
