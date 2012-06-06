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
