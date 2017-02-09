# -*- coding: utf-8 -*-
#
# http://code.activestate.com/recipes/286134/ (r3) (modified)

from __future__ import unicode_literals

import dis
from builtins import map

_const_codes = list(map(dis.opmap.__getitem__, [
    'POP_TOP', 'ROT_TWO', 'ROT_THREE', 'ROT_FOUR', 'DUP_TOP',
    'BUILD_LIST', 'BUILD_MAP', 'BUILD_TUPLE',
    'LOAD_CONST', 'RETURN_VALUE', 'STORE_SUBSCR'
]))

_load_names = ['False', 'True', 'null', 'true', 'false']

_locals = {'null': None, 'true': True, 'false': False}


def _get_opcodes(codeobj):
    i = 0
    opcodes = []
    s = codeobj.co_code
    names = codeobj.co_names
    while i < len(s):
        code = ord(s[i])
        opcodes.append(code)
        if code >= dis.HAVE_ARGUMENT:
            i += 3
        else:
            i += 1
    return opcodes, names


def test_expr(expr, allowed_codes):
    try:
        c = compile(expr, "", "eval")
    except:
        msg = "{} is not a valid expression"
        raise ValueError(msg.format(expr))
    codes, names = _get_opcodes(c)
    for code in codes:
        if code not in allowed_codes:
            for n in names:
                if n not in _load_names:
                    msg = "opcode {} not allowed"
                    raise ValueError(msg.format(dis.opname[code]))
    return c


def const_eval(expr):
    c = test_expr(expr, _const_codes)
    return eval(c, None, _locals)
