#!/usr/bin/env bash
NS=nosetests
which nosetests2 > /dev/null && NS=nosetests2
$NS tests/HosterPluginTester.py tests/CrypterPluginTester.py -s --with-xunit --with-coverage --cover-erase --cover-package=module.plugins
coverage xml
