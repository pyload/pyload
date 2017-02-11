#!/usr/bin/env bash
NS=nosetests
which nosetests2 > /dev/null && NS=nosetests2
# must be executed within tests dir
cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
$NS HosterPluginTester.py CrypterPluginTester.py -s --with-xunit --with-coverage --cover-erase --cover-package=pyload.plugin --with-id
coverage xml
