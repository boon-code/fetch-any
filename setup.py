from setuptools import setup
import datetime

YEAR = datetime.date.today().year

__author__ = "Manuel Huber"
__version__ = "0.1.0"
__docformat__ = "restructuredtext en"

with open('fetchany/version.py', 'w') as f:
	f.write("__version__ = '{0}'".format(__version__))


setup( name = 'fetchany'
     , version = __version__
     , description = 'Fetch multiple repositories (git, svn, hg, bzr, tar)'
     , author = __author__
     , author_email = 'Manuel.h87@gmail.com'
     , url = 'https://github.com/boon-code'
     , classifiers = [ "Development Status :: 2 - Pre-Alpha"
                     , "License :: OSI Approved :: MIT License"
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
