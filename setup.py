#! /usr/bin/env python3
"""Count votes."""
# See: https://packaging.python.org/en/latest/distributing/

from setuptools import setup, find_packages 
from codecs import open  # To use a consistent encoding
from os import path
from glob import glob

here = path.abspath(path.dirname(__file__))

#!# Get the long description from the relevant file
#!with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
#!    long_description = f.read()

with open(path.join(here,'vvote','VERSION')) as version_file:
    version = version_file.read().strip()

setup(
    name='vvote',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # http://packaging.python.org/en/latest/tutorial.html#version
    # EXAMPLE: '0.0.4rc2',
    version=version,

    description='Count votes.',
    long_description='Tally votes.',

    # The project's main homepage.
    url='https://github.com/pothiers/vvote',

    # Author details
    author='The Python Packaging Authority',
    author_email='pypa-dev@googlegroups.com',

    # Choose your license
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Information Technology',
        'Intended Audience :: End Users/Desktop',
 
       # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.4',
    ],

    # What does your project relate to?
    keywords='verification',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    #! packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    packages=['vvote', 'lvr'],

    # List run-time dependencies here.  These will be installed by pip when your
    # project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/technical.html#install-requires-vs-requirements-files
    #!install_requires=['openpyxl',],

    # If there are data files included in your packages that need to be
    # installed, specify them here. 
    package_data={'vvote': ['VERSION',]},

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages.
    # see http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    #!data_files=[('my_data', ['data/data_file'])],
                    

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            #'countvote=vvote.vvote:main',
            #'sovc=vvote.sovc:main',
            #'lvr=vvote.lvr:main',
            #'transpose=vvote.transpose:main',
            #'genmap=vvote.mapping:main',
            #'compare=vvote.comparesovc:main',

            'xls2csv=vvote.xlsx2csv:main',

            #!'lvrdb=vvote.lvr_db:main',
            #!'lvrcnt=vvote.lvr_count:main',
            #!'lvr2csv=vvote.lvr_db_csv:main',
            'lvrdb=lvr.lvr_db:main',
            'lvrcnt=lvr.lvr_count:main',
            'lvr2csv=lvr.lvr_db_csv:main',

            'sovcdb=vvote.sovc_db:main',
            'makemapdb=vvote.mapping_db:main',
            'cli=vvote.cli:main',
            'loadelection=vvote.election_db:main',
        ],
    },
)

