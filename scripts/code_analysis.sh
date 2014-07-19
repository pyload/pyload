#!/bin/sh

PYLOAD="../module"  # Check ~/pyload/module directory

echo "Running sloccount ..."
REPORT="sloccount.sc"
sloccount --duplicates --wide --details $PYLOAD > $REPORT && echo "Done. Report saved to $REPORT"

echo "Running pep8 ..."
REPORT="pep8.txt"
pep8 $PYLOAD > $REPORT && echo "Done. Report saved to $REPORT"

echo "Running pylint ..."
REPORT="pylint.txt"
pylint --reports=no $PYLOAD > $REPORT && echo "Done. Report saved to $REPORT"

#echo "Running pyflakes ..."
#REPORT="pyflakes.txt"
#{
   # pyflakes to pylint syntak
#  find $PYLOAD -type f -name "*.py" | egrep -v '^\./lib' | xargs pyflakes  > pyflakes.log || :
   # Filter warnings and strip ./ from path
#  cat pyflakes.log | awk -F\: '{printf "%s:%s: [E]%s\n", $1, $2, $3}' | grep -i -E -v "'_'|pypath|webinterface|pyreq|addonmanager" > $REPORT
#  sed -i 's/^.\///g' $REPORT
#} && echo "Done. Report saved to $REPORT"
