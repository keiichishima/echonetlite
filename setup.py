#!/usr/bin/env python

from setuptools import setup

try:
    from pandoc import convert
    read_me = lambda f: convert(f, 'rst')
except ImportError:
    print('pandoc is not installed.')
    read_me = lambda f: open(f, 'r').read()

setup(name='echonetlite',
      version='0.0.1',
      description='Echonet Lite',
      long_description=read_me('README.md'),
      author='Keiichi SHIMA',
      author_email='keiichi@iijlab.net',
      # url='',
      packages=['echonetlite'],
      install_requires=['Twisted>=16.3.0'],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: Information Technology',
          'License :: OSI Approved :: BSD License',
          'Programming Language :: Python :: 3.4',
          'Topic :: Scientific/Engineering :: Information Analysis',
          'Topic :: Software Development :: Libraries :: Python Modules'],
      license='BSD License',
  )
