#!/usr/bin/python
# -*- coding: UTF-8 -*-

from setuptools import setup

import versioneer
commands = versioneer.get_cmdclass().copy()

setup( 
    name = 'NIST',
    version = versioneer.get_version(),
    description = 'Python library for manipulating NIST files (Data Format for the Interchange of Fingerprint, Facial & Other Biometric Information)',
    author = 'Marco De Donno',
    author_email = 'Marco.DeDonno@unil.ch; mdedonno1337@gmail.com',
    packages = [
        'NIST',
        'NIST.traditional',
        'NIST.fingerprint'
    ],
    install_requires = [
        'future',
        'pillow',
    ],
 )
