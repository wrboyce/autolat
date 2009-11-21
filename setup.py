#!/usr/bin/env python
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='autolat',
    version='dev',
    author='Will Boyce',
    author_email='me@willboyce.com',
    url='http://github.com/wrboyce/autolat',
    packages=['autolat'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Licence :: BSD',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
    ]
)
