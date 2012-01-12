#!/bin/bash
find -name '*.py' |egrep -v '^.(/tests/|/module/lib)'|xargs pyflakes  > pyflakes.log || :
