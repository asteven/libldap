# -*- coding: utf-8 -*-
'''
Utilities for dealing with ldap users.
'''
import logging
log = logging.getLogger(__name__)

import ldap

from . import Error
from . import search


class AuthenticationError(Error):
    pass


class LdapUser(object):
    def __init__(self, uri, base_dn, bind_dn='', bind_pw=''):
        self.uri = uri
        self.base_dn = base_dn
        self.bind_dn = bind_dn
        self.bind_pw = bind_pw

    def _search(self, scope=ldap.SCOPE_SUBTREE, filter='(objectclass=*)', attributes=None, async=False):
        return libldap.ldap_search(self.uri, self.bind_dn, self.bind_pw, self.base_dn,
            scope=scope, filter=filter, attributes=attributes, async=async)

    def is_valid(self, username):
        """Check weither the given username is valid/exists.
        is_valid(username, config) -> bool
        """
        filter ='(cn=%s)' % username
        attributes = ['dn']
        try:
            result = self._search(scope=ldap.SCOPE_ONELEVEL, filter=filter, attributes=attributes, async=False)
            if result:
                return True
            else:
                return False
        except ldap.LDAPError, error_message:
            log.error('Failed to verify username against ldap: %s; %s', username, error_message)
            return False

    def get(self, username):
        """Get the entry for the given username from ldap.

        get(username, config) -> dict
        """
        filter ='(cn=%s)' % username
        attributes = None
        try:
            result = self._search(scope=ldap.SCOPE_ONELEVEL, filter=filter, attributes=attributes, async=False)
            if result:
                entry = libldap.dict_from_ldap_result(result[0])
                return entry
            else:
                return None
        except ldap.LDAPError, error_message:
            log.error('Failed to verify username against ldap: %s; %s', username, error_message)
            return None

    def authenticate(self, username, password, user_dn_template='cn=%(username)s,%(base_dn)s'):
        """Authenticate the given username/password against ldap.
        """
        try:
            connection = ldap.initialize(self.uri)
            user_dn = user_dn_template % {'username': username, 'base_dn': self.base_dn}
            connection.simple_bind_s(user_dn.encode('utf-8'), password.encode('utf-8'))
            connection.unbind_s()
        except ldap.INVALID_CREDENTIALS, e:
            log.error(e)
            raise AuthenticationError('User DN/password rejected by LDAP server.')
        except ldap.SERVER_DOWN, e:
            log.error(e)
            raise AuthenticationError('Can\'t contact LDAP server.')

    def find(self, query):
        filter ='(cn=%s)' % query
        for result in self._search(scope=ldap.SCOPE_SUBTREE, filter=filter, attributes=None, async=True):
            log.debug('result: %s', result)
            yield result


