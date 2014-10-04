#!/bin/sh

PYLOAD="../pyload"  # Check pyload directory

echo "Running sloccount ..."
REPORT="sloccount.sc"
sloccount --duplicates --wide --details $PYLOAD > $REPORT && echo "Done. Report saved to $REPORT"

echo "Running pep8 ..."
REPORT="pep8.txt"
pep8 $PYLOAD > $REPORT && echo "Done. Report saved to $REPORT"

echo "Running pylint ..."
REPORT="pylint.txt"
pylint --reports=no $PYLOAD > $REPORT && echo "Done. Report saved to $REPORT"
