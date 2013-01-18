#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from bottle import request, HTTPError, redirect

from webinterface import env, TEMPLATE, PYLOAD, SETUP

# TODO: useful but needs a rewrite, too
def render_to_response(name, args={}, proc=[]):
    for p in proc:
        args.update(p())
    if is_mobile():
        t = env.get_or_select_template(("mobile/" + name,))
    else:
        t = env.get_or_select_template((TEMPLATE + "/" + name, "default/" + name, name))
    return t.render(**args)


def set_session(request, user):
    s = request.environ.get('beaker.session')
    s["uid"] = user.uid
    s.save()
    return s

def get_user_api(s):
    if s:
        uid = s.get("uid", None)
        if (uid is not None) and (PYLOAD is not None):
            return PYLOAD.withUserContext(uid)
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
    mobile_agents = ['w3c ','acs-','alav','alca','amoi','audi','avan','benq','bird','blac','blaz','brew','cell','cldc','cmd-',
                     'dang','doco','eric','hipt','inno','ipaq','java','jigs','kddi','keji','leno','lg-c','lg-d','lg-g','lge-',
                     'maui','maxo','midp','mits','mmef','mobi','mot-','moto','mwbp','nec-','newt','noki','palm','pana','pant',
                     'phil','play','port','prox','qwap','sage','sams','sany','sch-','sec-','send','seri','sgh-','shar','sie-',
                     'siem','smal','smar','sony','sph-','symb','t-mo','teli','tim-','tosh','tsm-','upg1','upsi','vk-v','voda',
                     'wap-','wapa','wapi','wapp','wapr','webc','winw','winw','xda ','xda-']
    if mobile_ua in mobile_agents:
        return True
    return False


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
                    if api.user.hasPermission(perm):
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return HTTPError(403, "Forbidden")
                        else:
                            return redirect("/nopermission")

                kwargs["api"] = api
                return func(*args, **kwargs)
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return HTTPError(403, "Forbidden")
                else:
                    return redirect("/login")

        return _view

    return _dec
