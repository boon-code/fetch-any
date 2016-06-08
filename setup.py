from setuptools import setup
import datetime

YEAR = datetime.date.today().year

__author__ = "Manuel Huber"
__version__ = "0.1.0"
__copyright__ = "{0}, Manuel Huber. All rights reserved".format(YEAR)
__docformat__ = "restructuredtext en"

with open('fetchany/version.py', 'w') as f:
	f.write("__version__ = '{0}'".format(__version__))


setup( name = 'fetchany'
     , version = __version__
     , description = 'Power-Off File System Test Suite'
     , license = "Copyright (C) {0} Manuel Huber. All rights reserved".format(YEAR)
     , author = __author__
     , author_email = 'Manuel.h87@gmail.com'
     , url = 'https://github.com/boon-code'
     , classifiers = [ "Development Status :: 2 - Pre-Alpha"
                     ,"License :: Copyright (C) {0} Manuel Huber".format(YEAR)
                     , "Programming Language :: Python :: 2.7"
                     , "Programming Language :: Python :: 3"
                     ]
     , packages = ['fetchany']
     , install_requires = [ "docopt==0.6.2"
                          , "vcstools==0.1.38"
                          ]
     , entry_points = {
           'console_scripts' :
               [ 'vcsf = fetchany.__init__:main'
               ]
       }
     )
