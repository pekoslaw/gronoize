#!/usr/bin/env python

from distutils.core import setup
from memoize import __version__
setup(name='memoize',
    version=__version__,
    packages=['memoize'],
    description='Rock solid memoize for Python/Django',
    author='matee',
    author_email='memoize@matee.net',
    url='https://github.com/matee911/memoize',
    keywords = ['cache', 'memoize', 'django'],
    classifiers = [
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Natural Language :: English",
        "Natural Language :: Polish",
        "Environment :: Web Environment",
        "Environment :: Other Environment",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2 :: Only",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 2.6",
        "Topic :: Database",
        "Topic :: Internet",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Topic :: Other/Nonlisted Topic",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        
    ]
    )