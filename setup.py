#!/usr/bin/env python

import fnmatch
import glob
import os
import sys

from setuptools import setup

VERSION = "1.0.0"

setup(
    name='doitlive',
    version=VERSION,
    description='Tools for livecoding performances',
    author='Zach Banks',
    author_email='zbanks@mit.edu',
    url='https://github.com/zbanks/doitlive',
    packages=[
        'doitlive', 
    ],
    download_url="https://github.com/zbanks/doitlive/tarball/{}".format(VERSION),
    zip_safe=True,
    package_dir = {
        'doitlive': 'src'
    },
    package_data={
    },
)
