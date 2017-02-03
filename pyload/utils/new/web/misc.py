# -*- coding: utf-8 -*-
#@author: vuolter

from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()

import cStringIO
import gzip
import json
import os

import bottle

from contextlib import closing

from pyload.api import ACCESS, AUTH, has_permission
from pyload.utils.new import convert
from pyload.utils.new.lib import beaker
from pyload.webui import env


################################################################################
#: Classes  ####################################################################
################################################################################

# json encoder that accepts TBase objects
class TBaseEncoder(json.JSONEncoder):
    def default(self, value):
        if type(value) in (instance, object):
            return convert.to_dict(value, {})
        return json.JSONEncoder.default(self, value)


################################################################################
#: Functions  ##################################################################
################################################################################

def parse_permissions(session):
    perms = {x: False for x in dir(AUTH) if not x.startswith("_")}
    perms['ADMIN']    = False
    perms['is_admin'] = False

    if not session.get("auth", False):
        return perms

    if session.get("role") == ACCESS.ADMIN:
        for k in perms.keys():
            perms[k] = True

    elif session.get("perms"):
        p = session.get("perms")
        get_permission(perms, p)

    return perms


################################################################################
#: Decorators  #################################################################
################################################################################

def require_auth(perm=None):
    def wrapper(func):
        def new(*args, **kwargs):
            s = bottle.request.environ.get('beaker.session')
            if s.get("name", None) and s.get("auth", False):
                if perm and not parse_permissions(s).get(perm):
                    if bottle.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        res = bottle.HTTPError(403, "Forbidden")
                    else:
                        res = bottle.redirect("/nopermission")
                else:
                    res = func(*args, **kwargs)
            elif bottle.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                res = bottle.HTTPError(403, "Forbidden")
            else:
                res = bottle.redirect("/login")
            return res
        return new
    return wrapper


################################################################################
#: Functions  ##################################################################
################################################################################

def add_json_header(response):
    response.headers.replace("Content-type", "application/json")
    response.headers.append("Cache-Control", "no-cache, must-revalidate")
    response.headers.append("Access-Control-Allow-Origin",
                            bottle.request.get_header('Origin', '*'))
    response.headers.append("Access-Control-Allow-Credentials", "true")


def permlist():
    return [x for x in dir(AUTH) if not x.startswith("_") and x != "ALL"]


def get_permission(perms, p):
    """
    Returns a dict with permission key

    :param perms: dictionary
    :param p:  bits
    """
    for name in permlist():
        perms[name] = has_permission(p, getattr(AUTH, name))


def httperror(code, msg):
    return bottle.HTTPError(code,
                            json.dumps(msg),
                            **dict(bottle.response.headers))


def json_response(obj):
    result = json.dumps(obj, cls=TBaseEncoder)
    if 'gzip' not in bottle.request.headers.get('Accept-Encoding', ''):
        return result
    # do not compress small string
    if len(result) > 500:
        bottle.response.set_header("Vary", "Accept-Encoding")
        bottle.response.set_header("Content-Encoding", "gzip")
        with closing(cStringIO.StringIO()) as s:
            with gzip.GzipFile(mode='wb', compresslevel=6, fileobj=s) as f:
                f.write(result)
            return s.getvalue()
    return result


def parse_userdata(session):
    return {'name'    : session.get("name", "Anonymous"),
            'is_admin': session.get("role", 1) == 0,
            'is_auth' : session.get("auth", False)}


def render_to_response(file, args={}, proc=[]):
    for p in proc:
        args.update(p())
    return env.get_template(file).render(**args)


#@NOTE: Incomplete...
# def select_language(langs):
    # accept = bottle.request.headers.get('Accept-Language', '')
    # return langs[0]


def set_permission(perms):
    """
    Generates permission bits from dictionary

    :param perms: dict
    """
    permission = 0
    for name in dir(AUTH):
        if name.startswith("_"):
            continue
        if name in perms and perms[name]:
            permission |= getattr(AUTH, name)
    return permission


def set_session(info):
    s = bottle.request.environ.get('beaker.session')
    s.update({'auth'    : True,
              'uid'     : info['id'],
              'name'    : info['name'],
              'role'    : info['role'],
              'perms'   : info['permission'],
              'template': info['template']})
    s.save()
    return s
