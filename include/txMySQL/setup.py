#!/usr/bin/env python

from setuptools import setup


setup(name='txmysql',
      version='0.4.0',
      description='Twisted MySQL Protocol implementation',
      author='Hybrid Logic',
      author_email='luke@hybridlogic.co.uk',
      url='https://github.com/hybridlogic/txMySQL',
      platforms='any',
      packages=[
          'txmysql',
      ],
      install_requires=[
          'setuptools',
          'qbuf',
          ],
      zip_safe=False,
)
