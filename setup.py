#!/usr/bin/env python

import fnmatch
import glob
import os
import sys

from setuptools import setup

VERSION = "1.0.1"

setup(
    name='refreshable',
    version=VERSION,
    description='Tools for livecoding performances',
    author='Zach Banks',
    author_email='zbanks@mit.edu',
    url='https://github.com/zbanks/doitlive',
    packages=[
        'refreshable', 
    ],
    download_url="https://github.com/zbanks/doitlive/tarball/{}".format(VERSION),
    zip_safe=True,
    package_dir = {
        'refreshable': 'src'
    },
    package_data={
    },
)
