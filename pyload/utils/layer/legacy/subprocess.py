# -*- coding: utf-8 -*-
#
# Monkey patch bug in python 2.6 and earlier
# http://bugs.python.org/issue6122 , http://bugs.python.org/issue1236 ,
# http://bugs.python.org/issue1731717

from __future__ import absolute_import, unicode_literals

import os
import sys
from subprocess import *

from future import standard_library

standard_library.install_aliases()


if sys.version_info < (2, 7) and os.name != 'nt':
    import errno

    def _eintr_retry_call(func, *args):
        while True:
            try:
                return func(*args)

            except OSError as exc:
                if exc.errno == errno.EINTR:
                    continue
                raise

    # Unsued timeout option for older python version
    def wait(self, timeout=0):
        """Wait for child process to terminate.

        Returns returncode attribute

        """
        if self.returncode is None:
            try:
                pid, sts = _eintr_retry_call(os.waitpid, self.pid, 0)

            except OSError as exc:
                if exc.errno != errno.ECHILD:
                    raise Exception()
                # This happens if SIGCLD is set to be ignored or waiting
                # For child processes has otherwise been disabled for our
                # process.  This child is dead, we can't get the status.
                sts = 0

            self._handle_exitstatus(sts)

        return self.returncode

    Popen.wait = wait
