from setuptools import setup, find_packages

name = 'libldap'

setup(
    name=name,
    version='0.2.0',
    author='Steven Armstrong',
    author_email='steven-%s@armstrong.cc' % name,
    url='http://github.com/asteven/%s/' % name,
    description='Collection of helpers for working with ldap',
    packages=find_packages(),
    install_requires=['distribute', 'python-ldap'],
)

