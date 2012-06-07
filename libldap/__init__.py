# -*- coding: utf-8 -*-

try:
    import ldap
except ImportError:
    print 'You need to install the python ldap bindings to use this command.'
    print 'On Gentoo run: /usr/bin/emerge python-ldap -va'
    print 'On debian run: apt-get install python-ldap'
    import sys
    sys.exit(1)


class Error(Exception):
    '''Base class for all errors in this package'''
    pass


def set_ldap_options(options):
    """Set global ldap options.

    options must be a dictionary with ldap options, e.g.
    { 'OPT_X_TLS_CACERTFILE': '/path/to/cert.crt' }
    """
    for k,v in options.items():
        #log.debug('set_ldap_options: %s = %s', k, v)
        if hasattr(ldap, k):
            if k == 'OPT_X_TLS_REQUIRE_CERT':
                v = getattr(ldap, 'OPT_X_TLS_%s' % v.upper())
            ldap.set_option(getattr(ldap, k), v)


def ldap_search_paged(l, basedn, scope, filter, attributes, timeout, page_size):
    # FIXME: untested
    from ldap.controls import SimplePagedResultsControl
    lc = SimplePagedResultsControl(
        ldap.LDAP_CONTROL_PAGE_OID, True, (page_size,'')
    )
    # Send search request
    result_id = l.search_ext(basedn, scope, filter, attributes, serverctrls=[lc])

    pages = 0
    while True:
        pages += 1
        log.debug('Getting page %d', pages)
        result_type, result_data, result_msgid, serverctrls = l.result3(result_id)
        log.debug('%d results', len(result_data))
        if not result_data:
            break
        pctrls = [c for c in serverctrls if c.controlType == ldap.LDAP_CONTROL_PAGE_OID]
        if pctrls:
            est, cookie = pctrls[0].controlValue
            if cookie:
                lc.controlValue = (page_size, cookie)
                result_id = l.search_ext(basedn, scope, filter, attributes, serverctrls=[lc])
            else:
                break
        else:
            log.warn('Server ignores RFC 2696 control.')
            break


def ldap_search_async(l, basedn, scope, filter, attributes, timeout):
    result_id = l.search(basedn, scope, filter, attributes)
    log.debug('result_id: %s', result_id)
    while True:
        result_type, result_data = l.result(result_id, timeout)
        log.debug('result_type: %s', result_type)
        log.debug('result_data: %s', result_data)

        if not result_data:
            break
        else:
            if result_type == ldap.RES_SEARCH_ENTRY:
                yield result_data


def ldap_search(url, binddn, bindpw, basedn, scope=ldap.SCOPE_SUBTREE, filter='(objectclass=*)', attributes=None, async=False, timeout=0, page_size=0):
    try:
        log.debug('Connecting to: %s', url)
        l = ldap.initialize(url)
        l.simple_bind_s(binddn, bindpw)

        log.debug('Searching..')

        try:
            if async:
                if page_size:
                    return ldap_search_paged(l, basedn, scope, filter, attributes, timeout, page_size)
                else:
                    return ldap_search_async(l, basedn, scope, filter, attributes, timeout)
            else:
                return l.search_s(basedn, scope, filter, attributes)

        except ldap.LDAPError, error_message:
            log.error('Search failed: %s ', error_message)

    except ldap.LDAPError, error_message:
        log.error('Connection failed: %s ', error_message)
        raise


def dict_from_ldap_result(data, attributes=None):
    if attributes:
        d = dict.fromkeys(attributes)
    else:
        d = {}
    d['dn'] = data[0]
    for k,v in data[1].items():
        if len(v) == 1:
            d[k] = v[0]
        else:
            d[k] = v
    return d

