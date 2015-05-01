# -*- coding: utf-8 -*-
# The MIT License (MIT)
#
# Copyright © 2014 Tim Bielawa <timbielawa@gmail.com>
# See GitHub Contributors Graph for more information
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sub-license, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import bitmath
import argparse
import progressbar.widgets

######################################################################
# Integrations with 3rd party modules
def BitmathType(bmstring):
    """An 'argument type' for integrations with the argparse module.

For more information, see
https://docs.python.org/2/library/argparse.html#type Of particular
interest to us is this bit:

   ``type=`` can take any callable that takes a single string
   argument and returns the converted value

I.e., ``type`` can be a function (such as this function) or a class
which implements the ``__call__`` method.

Example usage of the bitmath.BitmathType argparser type:

   >>> import bitmath
   >>> import argparse
   >>> parser = argparse.ArgumentParser()
   >>> parser.add_argument("--file-size", type=bitmath.BitmathType)
   >>> parser.parse_args("--file-size 1337MiB".split())
   Namespace(file_size=MiB(1337.0))

Invalid usage includes any input that the bitmath.parse_string
function already rejects. Additionally, **UNQUOTED** arguments with
spaces in them are rejected (shlex.split used in the following
examples to conserve single quotes in the parse_args call):

   >>> parser = argparse.ArgumentParser()
   >>> parser.add_argument("--file-size", type=bitmath.BitmathType)
   >>> import shlex

   >>> # The following is ACCEPTABLE USAGE:
   ...
   >>> parser.parse_args(shlex.split("--file-size '1337 MiB'"))
   Namespace(file_size=MiB(1337.0))

   >>> # The following is INCORRECT USAGE because the string "1337 MiB" is not quoted!
   ...
   >>> parser.parse_args(shlex.split("--file-size 1337 MiB"))
   error: argument --file-size: 1337 can not be parsed into a valid bitmath object
"""
    try:
        argvalue = bitmath.parse_string(bmstring)
    except ValueError:
        raise argparse.ArgumentTypeError("'%s' can not be parsed into a valid bitmath object" %
                                         bmstring)
    else:
        return argvalue

######################################################################
# Speed widget for integration with the Progress bar module
class BitmathFileTransferSpeed(progressbar.widgets.Widget):
    """Widget for showing the transfer speed (useful for file transfers)."""
    __slots__ = ('system', 'format')

    def __init__(self, system=bitmath.NIST, format="{value:.2f} {unit}/s"):
        self.system = system
        self.format = format

    def update(self, pbar):
        """Updates the widget with the current NIST/SI speed.

Basically, this calculates the average rate of update and figures out
how to make a "pretty" prefix unit"""

        if pbar.seconds_elapsed < 2e-6 or pbar.currval < 2e-6:
            scaled = bitmath.Byte()
        else:
            speed = pbar.currval / pbar.seconds_elapsed
            scaled = bitmath.Byte(speed).best_prefix(system=self.system)

        return scaled.format(self.format)
