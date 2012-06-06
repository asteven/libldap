# -*- coding: utf-8 -*-

import logging
log = logging.getLogger('libldap')

import ldap

from . import Error


class ConnectionError(Error):
    pass


class SearchError(Error):
    pass


class LdapSearch(object):
    def __init__(self, uri, base_dn, bind_dn='', bind_pw=''):
        self.uri = uri
        self.base_dn = base_dn
        self.bind_dn = bind_dn
        self.bind_pw = bind_pw
        self._connection = None

    @property
    def connection(self):
        if self._connection is None:
            try:
                self._connection = l = ldap.initialize(self.url)
                log.debug('Connecting to: %s', url)
                l.simple_bind_s(self.bind_dn, self.bind_pw)
            except ldap.LDAPError as error:
                msg = 'Connection failed: %s' % error
                log.error(msg)
                raise ConnectionError(msg)
        return self._connection

    def search(self, scope=ldap.SCOPE_SUBTREE, filter='(objectclass=*)', attributes=None):
        try:
            return self.connection.search_s(self.basedn, scope, filter, attributes)
        except ldap.LDAPError as error:
            msg = 'Search failed: %s' % error
            log.error(msg)
            raise SearchError(msg)

    def async(self, scope=ldap.SCOPE_SUBTREE, filter='(objectclass=*)', attributes=None, timeout=0):
        try:
            result_id = self.connection.search(self.basedn, scope, filter, attributes)
            log.debug('result_id: %s', result_id)
            while True:
                result_type, result_data = self.connection.result(result_id, timeout)
                log.debug('result_type: %s', result_type)
                log.debug('result_data: %s', result_data)
                if not result_data:
                    break
                else:
                    if result_type == ldap.RES_SEARCH_ENTRY:
                        yield result_data
        except ldap.LDAPError as error:
            msg = 'Search failed: %s' % error
            log.error(msg)
            raise SearchError(msg)

    def paged(self, scope=ldap.SCOPE_SUBTREE, filter='(objectclass=*)', attributes=None, page_size=0):
        from ldap.controls import SimplePagedResultsControl
        lc = SimplePagedResultsControl(
            ldap.LDAP_CONTROL_PAGE_OID, True, (page_size,'')
        )
        try:
            # Send search request
            result_id = self.connection.search_ext(basedn, scope, filter, attributes, serverctrls=[lc])

            pages = 0
            while True:
                pages += 1
                log.debug('Getting page %d', pages)
                result_type, result_data, result_msgid, serverctrls = self.connection.result3(result_id)
                log.debug('%d results', len(result_data))
                if not result_data:
                    break
                pctrls = [c for c in serverctrls if c.controlType == ldap.LDAP_CONTROL_PAGE_OID]
                if pctrls:
                    est, cookie = pctrls[0].controlValue
                    if cookie:
                        lc.controlValue = (page_size, cookie)
                        result_id = self.connection.search_ext(basedn, scope, filter, attributes, serverctrls=[lc])
                    else:
                        break
                else:
                    log.warn('Server ignores RFC 2696 control.')
                    break
        except ldap.LDAPError as error:
            msg = 'Search failed: %s' % error
            log.error(msg)
            raise SearchError(msg)
