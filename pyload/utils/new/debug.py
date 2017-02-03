# -*- coding: utf-8 -*-
#@author: vuolter

from __future__ import unicode_literals

import inspect
import os
import pprint
import sys
import traceback
import types

from pyload.utils.new import convert
from pyload.utils.new.check import proprieties
from pyload.utils.new.path import makefile, open


def report(value, path=None):
    frame = inspect.currentframe()
    try:
        name = "{}_line{}.report".format(
            frame.f_back.f_code.co_name, frame.f_back.f_lineno)
        file = os.path.join(path or "reports", name)
        with makefile(file, 'wb') as f:
            f.write(value)
    finally:
        del frame  #: delete it just now or wont be cleaned by gc


def _format_dump(obj):
    dump = []
    for attr_name in proprieties(obj):
        if attr_name.endswith("__"):
            continue
        try:
            attr_dump += pprint.pformat(getattr(obj, attr_name))
        except Exception as e:
            attr_dump += "<ERROR WHILE PRINTING VALUE> {}".format(e.message)
        dump.append((attr_name, attr_dump))
    return dump


def format_dump(obj):
    title = "DUMP {!r}:".format(obj)
    body = '\n'.join("\t{:20} = {}".format(attr_name, attr_dump)
                     for attr_name, attr_dump in _format_dump(obj))
    return "{}\n{}\n".format(title, body)


def print_dump(obj, file=None):
    text = format_dump(obj)
    if file:
        return file.write(text)
    print text


def _format_framestack(frame=None, limit=None):
    limit = None if not limit else abs(limit)
    stack = []
    etype, value, tb = sys.exc_info(frame)
    try:
        while tb:
            stack.append(tb.tb_frame)
            tb = tb.tb_next

        dump = []
        for frame in stack[1:limit]:
            msg = "Frame {} in {} at line {}"
            frame_name = msg.format(frame.f_code.co_name,
                                    frame.f_code.co_filename,
                                    frame.f_lineno)
            frame_dump = []
            for attr_name, value in frame.f_locals.items():
                try:
                    attr_dump += pprint.pformat(value)
                except Exception as e:
                    attr_dump += "<ERROR WHILE PRINTING VALUE> {}".format(
                        e.message)
                frame_dump.append((attr_name, attr_dump))

            dump.append((frame_name, frame_dump))
            del frame

        return dump

    finally:
        del stack[:]  #: delete all just to be sure...


def format_framestack(frame=None, limit=None):
    framestack = _format_framestack(frame, limit)
    stack_desc = []
    for frame_name, frame_dump in framestack:
        dump = '\n'.join("\t{:20} = {}".format(attr_name, attr_dump)
                         for attr_name, attr_dump in frame_dump)
        stack_desc.append('{}\n{}'.format(frame_name, dump))

    title = "FRAMESTACK {!r}:".format(frame)
    body = '\n\n'.join(stack_desc)
    return "{}\n{}\n".format(title, body)


def print_framestack(frame=None, limit=None, file=None):
    text = format_framestack(frame, limit)
    if file:
        return file.write(text)
    print text


def _format_traceback(frame=None, limit=None, offset=None):
    """
    Format call-stack and exception information (if available).
    """
    limit = None if not limit else abs(limit)
    offset = 1 if not offset else abs(offset) + 1
    etype, value, tb = sys.exc_info()
    try:
        stack = []
        exception = []

        callstack = traceback.extract_stack(frame)[::-1][offset:limit][::-1]
        if etype is not None:
            exception_callstack = traceback.extract_tb(tb)

            #: Does this exception belongs to us?
            if callstack[-1][0] == exception_callstack[0][0]:
                callstack.pop()
                callstack.extend(exception_callstack)
                exception = traceback.format_exception_only(etype, value)

        stack = traceback.format_list(callstack)

        return stack, exception

    finally:
        del tb


def format_traceback(frame=None, limit=None, offset=None):
    offset = 1 if not offset else abs(offset) + 1
    stack, exception = _format_traceback(frame, limit, offset)
    title = "Traceback (most recent call last):"
    body = ''.join(stack + exception)
    return "{}\n{}\n".format(title, body)


def print_traceback(frame=None, limit=None, file=None):
    text = format_traceback(frame, limit, offset=1)
    if file:
        return file.write(text)
    print text
