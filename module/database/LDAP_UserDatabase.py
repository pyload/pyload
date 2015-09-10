# -*- coding: utf-8 -*-
"""
Created on Wed Sep 09 22:12:40 2015

@author: Dracchus
"""

import ldap
import ldap.filter

from DatabaseBackend import DatabaseBackend
from DatabaseBackend import style
from module.Api import PERMS, ROLE

# FIXME ! Hardcoded parameters
# Format of parameters in LDAP_params.py :
#   ldap_url       = "ldap://127.0.0.1"
#   dn_format      = "uid={uid},ou=People,dc=dracchus,dc=site"
#   pyload_cn      = "cn=pyload,ou=Group,dc=dracchus,dc=site"
#   manager_cn     = "cn=Manager,dc=dracchus,dc=site"
#   manager_passwd = [PASSWORD]
#   users_query    = "ou=People,dc=dracchus,dc=site"
from LDAP_params import *

# Enabled functions
addUser_enable = False  # Disabled for satefy reasons (and not fully implemented)

# Relevant documentation :
#   LDAP injection :
#     https://stackoverflow.com/questions/3028770/preventing-ldap-injection
#     https://www.owasp.org/index.php/LDAP_injection
#     https://www.owasp.org/index.php/Preventing_LDAP_Injection_in_Java
#     http://www.rlmueller.net/CharactersEscaped.htm
#     http://www.rlmueller.net/PowerShellEscape.htm
#     http://www.faqs.org/rfcs/rfc2254.html
#   Modify LDAP fields :
#     https://www.packtpub.com/books/content/python-ldap-applications-part-3-more-ldap-operations-and-ldap-url-library
#   Pyload code :
#     https://github.com/pyload/pyload/blob/stable/module/database/UserDatabase.py
#     https://github.com/pyload/pyload/blob/stable/module/database/DatabaseBackend.py
#   @classmethod:
#      http://lifecs.likai.org/2014/03/really-understanding-python.html

class LDAP_UserMethods:

    # Parameters are stored globally
    # Mandatory to insert into Pyload code source

    @classmethod
    def __manager_login(cls):    
        # Warning ! Storing Manager password is not secure !
        # TODO : Make a special pyload manager user.
        # Login to LDAP server
        l = ldap.initialize(ldap_url)
        l.protocol_version = ldap.VERSION3
        l.simple_bind_s(manager_cn, manager_passwd)
        return l
    
    @classmethod
    def __anonymous_login(cls):
        # Login to LDAP server
        l = ldap.initialize(ldap_url)
        l.protocol_version = ldap.VERSION3
        l.simple_bind_s(manager_cn, manager_passwd)
        return l

    @classmethod
    def __login(cls, user, passwd):
        # User dn
        dn = cls.__user_dn(user)
        # Login to LDAP server
        l = ldap.initialize(ldap_url)
        l.protocol_version = ldap.VERSION3
        l.simple_bind_s(dn, passwd)
        return l

    @classmethod
    def __user_dn(cls, user):
        return dn_format.format(uid = ldap.filter.escape_filter_chars(user, escape_mode = 2))
    
    @classmethod
    def __user_data_from_field(cls, field):
        # Permission
        if 'pyloadPermission' in field:
            permission = int(field['pyloadPermission'][0])
        else:
            permission = PERMS.ALL  # Safe default : no rights. See Api.Py.
        # Role
        if 'pyloadRole' in field:
            role = int(field.get('pyloadRole', [None])[0])
        else:
            role = ROLE.USER  # Safe default : user mode, no admin. See Api.Py.
        # Other fields + return
        return {"id": field['uid'][0],                               # Mandatory
                "name": field['gecos'][0],                           # Mandatory
                "role": role,                                        # May be unimplemented in current database
                "permission": permission,                            # May be unimplemented in current database
                "template": field.get('pyloadTemplate', [None])[0],  # May be unimplemented in current database
                "email": field.get('mail', [None])[0]}               # May be unimplemented in current database

    @classmethod
    def __invalid_user(cls):
        return {}

    @style.queue
    def checkAuth(db, user, passwd):
        u"""Check whether the current user is a valid pyloader."""
        try:
            # Login to LDAP server
            l = LDAP_UserMethods.__login(user, passwd)
            # Retrieve real dn
            # Countermeasure against injection attacks
            real_dn = l.whoami_s()[3:]  # Removes the 'dn'
            # Retrive user info
            # Uses real_dn because user input is always untrustworthy
            info = l.search_s(real_dn, ldap.SCOPE_BASE)[0][1]
            # Real uid
            real_uid = info['uid'][0]
            # Retrieve pyload group info
            pyload_members = l.search_s(pyload_cn, ldap.SCOPE_BASE)[0][1]['memberUid']
            # Check user against pyload members
            if real_uid in pyload_members:
                # User in group, return user info
                return LDAP_UserMethods.__user_data_from_field(info)
            else:
                # User not in group, invalid
                return LDAP_UserMethods.__invalid_user()
        except ldap.INVALID_CREDENTIALS:
            # Invalid login
            return LDAP_UserMethods.__invalid_user()
   
    @classmethod
    def addUser(cls, db, user, passwd):
        if addUser_enable:
            # If function enabled
            # Login to LDAP server
            l = cls.__login(user, passwd)
            # Search user in database
            dn = LDAP_UserMethods.__user_dn(user)
            res = l.search_s(dn, ldap.SCOPE_BASE)
            if len(res) == 0:
                # If user is not in database
                # TODO ! Code !
                raise NotImplementedError()
            else:
                # Else, user is already in database
                # Login as Manager
                l = cls.__manager_login()
                # FIXME ! Add user to pyload group !
                # Change user password
                l.password_s(user, None, passwd)
        else:
            # Else, Function disabled
            raise NotImplementedError()

    
    @classmethod
    def changePassword(cls, db, user, oldpw, newpw):
        # Login to LDAP server
        l = cls.__login(user, oldpw)
        # Change user password
        l.password_s(user, oldpw, newpw)
    
    @style.queue
    def setPermission(db, user, perms):
        # FIXME + Warning ! This function doesn't check that user entry can
        # receive the data (right objectClass)
        # Login as Manager
        l = LDAP_UserMethods.__manager_login()
        # Modify user attributes
        # FIXME ! More checking !
        dn = LDAP_UserMethods.__user_dn(user)
        l.modify_s(dn, [(ldap.MOD_REPLACE, 'pyloadPermission', str(perms))])

    @style.queue
    def setRole(db, user, role):
        # FIXME + Warning ! This function doesn't check that user entry can
        # receive the data (right objectClass)
        # Login as Manager
        l = LDAP_UserMethods.__manager_login()
        # Modify user attributes
        # FIXME ! More checking !
        dn = LDAP_UserMethods.__user_dn(user)
        l.modify_s(dn, [(ldap.MOD_REPLACE, 'pyloadRole', str(role))])
    
    # Contrary to MySQL, LDAP doesn't allow easily to retrieve only some fields
    @classmethod
    def listUsers(cls, db):   
        return cls.getAllUserData(db).keys()
    
    @style.queue
    def getAllUserData(db):
        # Anonymous login to LDAP server
        l = LDAP_UserMethods.__anonymous_login()
        # Retrieve pyload group members
        pyload_members = l.search_s(pyload_cn, ldap.SCOPE_BASE)[0][1]['memberUid']
        # For each user in pyload members
        users = {}
        for uid in pyload_members:
            # Search user info
            try:
                dn = LDAP_UserMethods.__user_dn(uid)
                res = l.search_s(dn, ldap.SCOPE_BASE)
            except ldap.NO_SUCH_OBJECT:
                # No user
                res = None
            if res is None or len(res) == 0:
                # If user cannot be found
                #
                # We simply ignore it, since valid users are both in pyload group and in database.
                # This situation can occur in special configuration cases.
                #
                # This test is in first position to avoid errors triggered by len(None).
                pass
            elif len(res) == 1:
                # Elif one single user can be found
                # Get and store all user data
                users[uid] = LDAP_UserMethods.__user_data_from_field(res[0][1])
            elif len(res) > 1:
                # Elif several user can be found
                # This is a problem with LDAP server
                # FIXME : Report it
                pass
            else:
                # Else, user cannot be found
                # FIXME : Report the problem
                pass
        return users

    @classmethod
    def removeUser(cls, db, uid=None):
        # WARNING !
        # TODO : Check this point
        #
        # This function is not implemented, and will probably never be implemented
        # because letting pyload modify LDAP database is rather dangerous
        #
        # It is better to modify LDAP database from LDAP management interface
        raise NotImplementedError()

DatabaseBackend.registerSub(LDAP_UserMethods)

