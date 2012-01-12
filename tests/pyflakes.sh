#!/bin/bash
find -name '*.py' |egrep -v '^.(/tests/|/module/lib)'|xargs pyflakes  > pyflakes.log || :
cat pyflakes.log | awk -F\: '{printf "%s:%s: [E]%s\n", $1, $2, $3}' > pyflakes.txt
