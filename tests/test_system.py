# -*- coding: utf-8 -*-

import os
import shutil
import sys
import re
import requests
import time
from nose.tools import *

if os.name =='nt':
    from wexpect import spawn as p_spawn
    PY_PATH = 'c:\\python27\\python.exe'
else:
    from pexpect import spawn as p_spawn
    PY_PATH = '/usr/bin/python2.7'

api_url = "http://localhost:8000/api/%s"
url = "http://localhost:8000/%s"

base_path = os.path.dirname(os.path.abspath(__file__))
pyloadpath = os.path.abspath(os.path.join(base_path, '..', 'pyLoadCore.py'))


def setup_start(pyloadpath):
    c = p_spawn(PY_PATH + ' ' +  pyloadpath)
    if os.name != 'nt':
        c.logfile = sys.stdout
    else:
        lgfile = open('logfile.txt', 'w')
        c.logfile = lgfile
    c.expect('Choose your Language .*:')
    c.sendline('en')
    c.expect('When you are ready.*')
    c.sendline('j')
    c.expect('System check finished.*')
    systemresult = c.before
    var = re.findall('py-OpenSSL:\s(OK|missing)',systemresult)
    c.sendline('')
    c.expect('Continue.*')
    c.sendline('')
    c.expect('Change config.*')
    return var, c

def doInitalConfig(username, password, download_folder=None, config_folder=None):
    if not config_folder:
        if os.name == 'nt':
            conf_path = 'pyload'
        else:
            conf_path = '.pyload'
        configdir = os.path.join(os.path.expanduser("~"), conf_path)
        shutil.rmtree(configdir, ignore_errors=True)
        configdirfile = os.path.join(base_path, '..', 'module', 'config', 'configdir')
        if os.path.exists(configdirfile):
            os.remove(configdirfile)
    else:
        shutil.rmtree(config_folder, ignore_errors=True)
    var, c = setup_start(pyloadpath)
    if config_folder:
        c.sendline('y')
        c.expect('Configpath.*')
        c.sendline(config_folder)
        c.sendline('')
        # finished start again
        var, c = setup_start(pyloadpath)
    c.sendline('n')
    c.expect('Make basic.*')
    c.sendline('y')
    c.expect('Username.*')
    c.sendline(username)
    c.expect('Password.*')
    c.sendline(password)
    c.expect('Password.*again.*')
    c.sendline(password)
    c.expect('Enable remote access.*')
    c.sendline('y')
    c.expect('Language.*')
    c.sendline('en')
    c.expect('Downloadfolder.*')
    if download_folder:
        c.sendline(download_folder)
    else:
        c.sendline('')
    c.expect('Max.*')
    c.sendline('')
    c.expect('Use Reconnect.*')
    c.sendline('')
    if var[0] == 'OK':
        c.expect('Do you want to configure ssl.*')
        c.sendline('')
    c.expect('Do you want to configure webinterface.*')
    c.sendline('')
    c.expect('Activate webinterface.*')
    c.sendline('')
    c.expect('Address.*')
    c.sendline('')
    c.expect('Port.*')
    c.sendline('')
    c.expect('Server.*')
    c.sendline('')
    c.expect('Template.*')
    c.sendline('')
    c.expect('Hit enter.*')
    c.sendline('')
    if os.name == 'nt':
        c.logfile.close()


class TestSystem:

    @classmethod
    def setupClass(cls):
        doInitalConfig('Mäf', 'müfo')

    def test_login(self):
        c = p_spawn(PY_PATH + ' ' + pyloadpath)
        if os.name != 'nt':
            c.logfile = sys.stdout
        else:
            lgfile = open('login_logfile.txt', 'w')
            c.logfile = lgfile
        # Wait pyload is running
        c.expect('ADDON ClickNLoad: Proxy listening.*')
        # Login via API
        r = requests.Session()
        u = r.post(api_url % "login", data={"username": "Mäf", "password": "müfo"})
        self.key = u.json()
        assert self.key is not False
        r.close()
        # Login Via Web Interface
        r = requests.Session()
        u = r.post(url % "login", data={"username": "Mäf", "password": "müfo", "submit":"login", "do":"login"})
        content = u.text
        assert "Incorrect username/email or password." not in content
        assert "Logout" in content
        r.close()
        if os.name == 'nt':
            c.logfile.close()

    def test_change_password(self):
        c = p_spawn(PY_PATH + ' ' + pyloadpath + ' -u')
        if os.name != 'nt':
            c.logfile = sys.stdout
        else:
            lgfile = open('password_logfile.txt', 'w')
            c.logfile = lgfile
        c.expect('.*/2/3/4:')
        c.sendline('1')
        c.expect('Username.*')
        c.sendline('Mäf')
        c.expect('Password.*')
        c.sendline('Külu')
        c.expect('Password.*again.*')
        c.sendline('Külu')
        c.expect('.*/2/3/4:')
        time.sleep(3)
        c.sendline('4')
        time.sleep(3)
        if os.name == 'nt':
            c.logfile.close()
        c = p_spawn(PY_PATH + ' ' + pyloadpath)
        if os.name != 'nt':
            c.logfile = sys.stdout
        else:
            lgfile = open('pyload_logfile.txt', 'w')
            c.logfile = lgfile
        # Wait pyload is running
        c.expect('ADDON ClickNLoad: Proxy listening.*')
        # Login Via Web Interface
        r = requests.Session()
        u = r.post(url % "login", data={"username": "Mäf", "password": "Külu", "submit":"login", "do":"login"})
        content = u.text
        assert "Logout" in content
        # Change Password in UI
        u = r.post(url % "json/change_password", data={"user_login": "Mäf",
                                                       "login_current_password": "Külu",
                                                       "login_new_password": "müfo",
                                                       "login_new_password2": "müfo"})
        assert u.status_code == 200

        # c.terminate()
        # Needs some time to save database
        time.sleep(2)
        u = r.get(url % "api/kill")
        assert u.status_code == 200
        r.close()
        if os.name == 'nt':
            c.logfile.close()

    def test_delete_user(self):
        c = p_spawn(PY_PATH + ' ' + pyloadpath + ' -u')
        if os.name != 'nt':
            c.logfile = sys.stdout
        else:
            lgfile = open('delete_logfile.txt', 'w')
            c.logfile = lgfile
        c.expect('.*/2/3/4:')
        c.sendline('1')
        c.expect('Username.*')
        c.sendline('Türbo')
        c.expect('Password.*')
        c.sendline('Küku')
        c.expect('Password.*again.*')
        c.sendline('Küku')
        c.expect('.*/2/3/4:')
        c.sendline('3')
        c.expect('Username.*')
        c.sendline('Türbo')
        c.sendline('2')
        c.expect('Users.*Mäf.*(.*)----.*')
        result = c.after
        c.sendline('4')
        assert "Trübo" not in result
        if os.name == 'nt':
            c.logfile.close()

