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
    entry_points={
        'console_scripts': ['autolat = autolat:main'],
    },
    install_requires=['argparse', 'BeautifulSoup', 'simplejson'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Licence :: BSD',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
    ]
)
