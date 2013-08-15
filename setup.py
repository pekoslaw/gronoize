#!/usr/bin/env python


from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
from gronoize import __version__
setup(name='gronoize',
    version=__version__,
    packages=['gronoize', 'gronoize.backends'],
    description='Rock solid memoize for Python/Django',
    author=u'Piotr Kalmus',
    author_email='pckalmus@gmail.com',
    url='https://github.com/pekoslaw/gronoize',
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
        "Programming Language :: Python :: 3 :: Only",
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
        
    ],
    cmdclass = {'build_ext': build_ext},
    ext_modules = [Extension("gronoize.utils", ["gronoize/utils.py"]),
                   Extension("gronoize.decorators", ["gronoize/decorators.py"]),
                   Extension("gronoize.middleware", ["gronoize/middleware.py"]),
                   ]
)