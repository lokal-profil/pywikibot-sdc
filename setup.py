# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from setuptools import setup

version = '0.1.1'
repo = 'pywikibot-sdc'

with open("README.md", "r") as readme:
    long_description = readme.read()

setup(
    name='pywikibot-sdc',
    packages=['pywikibotsdc'],
    install_requires=[
        'future',
        'mwparserfromhell',
        'setuptools>50.0.0; python_version >= "3.6"',
        'pathlib; python_version < "3.6"',
        'pywikibot==6.0.0; python_version >= "3.6"',
        'pywikibot==3.0.20200703; python_version < "3.6"'
    ],
    version=version,
    description='Support for importing Structured Data to Wikimedia Commons.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='André Costa',
    author_email='',
    url='https://github.com/lokal-profil/' + repo,
    download_url='https://github.com/lokal-profil/' + repo + '/tarball/' + version,
    keywords=['Wikimedia Commons', 'Wikimedia', 'Commons', 'pywikibot', 'API'],
    license="MIT",
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "pywikibotsdc=pywikibotsdc.__main__:main",
        ]
    },
)
