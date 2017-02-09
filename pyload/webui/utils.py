# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import re

from bottle import HTTPError, redirect, request

from pyload.webui.interface import PYLOAD, SETUP


def add_json_header(r):
    r.headers.replace("Content-type", "application/json")
    r.headers.append("Cache-Control", "no-cache, must-revalidate")
    r.headers.append("Access-Control-Allow-Origin",
                     request.get_header('Origin', '*'))
    r.headers.append("Access-Control-Allow-Credentials", "true")


def set_session(request, user):
    s = request.environ.get('beaker.session')
    s['uid'] = user.uid
    s.save()
    return s


def get_user_api(s):
    if s:
        uid = s.get("uid", None)
        if (uid is not None) and (PYLOAD is not None):
            return PYLOAD.with_user_context(uid)
    return None


def is_mobile():
    if request.get_cookie("mobile"):
        if request.get_cookie("mobile") == "True":
            return True
        else:
            return False
    mobile_ua = request.headers.get('User-Agent', '').lower()
    if mobile_ua.find('opera mini') > 0:
        return True
    if mobile_ua.find('windows') > 0:
        return False
    if request.headers.get('Accept', '').lower().find('application/vnd.wap.xhtml+xml') > 0:
        return True
    if re.search('(up.browser|up.link|mmp|symbian|smartphone|midp|wap|phone|android)', mobile_ua) is not None:
        return True
    mobile_ua = mobile_ua[:4]
    mobile_agents = ['w3c ', 'acs-', 'alav', 'alca', 'amoi', 'audi', 'avan', 'benq', 'bird', 'blac', 'blaz', 'brew',
                     'cell', 'cldc', 'cmd-',
                     'dang', 'doco', 'eric', 'hipt', 'inno', 'ipaq', 'java', 'jigs', 'kddi', 'keji', 'leno', 'lg-c',
                     'lg-d', 'lg-g', 'lge-',
                     'maui', 'maxo', 'midp', 'mits', 'mmef', 'mobi', 'mot-', 'moto', 'mwbp', 'nec-', 'newt', 'noki',
                     'palm', 'pana', 'pant',
                     'phil', 'play', 'port', 'prox', 'qwap', 'sage', 'sams', 'sany', 'sch-', 'sec-', 'send', 'seri',
                     'sgh-', 'shar', 'sie-',
                     'siem', 'smal', 'smar', 'sony', 'sph-', 'symb', 't-mo', 'teli', 'tim-', 'tosh', 'tsm-', 'upg1',
                     'upsi', 'vk-v', 'voda',
                     'wap-', 'wapa', 'wapi', 'wapp', 'wapr', 'webc', 'winw', 'winw', 'xda ', 'xda-']
    if mobile_ua in mobile_agents:
        return True
    return False

# TODO: Implement language selection...
def select_language(langs):
    # TODO: Use accept
    accept = request.headers.get('Accept-Language', '')
    return langs[0]


def login_required(perm=None):
    def _dec(func):
        def _view(*args, **kwargs):

            # In case of setup, no login methods can be accessed
            if SETUP is not None:
                redirect("/setup")

            s = request.environ.get('beaker.session')
            api = get_user_api(s)
            if api is not None:
                if perm:
                    if api.user.has_permission(perm):
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return HTTPError(403, "Forbidden")
                        else:
                            return redirect("/nopermission")

                kwargs['api'] = api
                return func(*args, **kwargs)
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return HTTPError(403, "Forbidden")
                else:
                    return redirect("/login")

        return _view

    return _dec
