#!/usr/bin/env python

from setuptools import setup

try:
    from pypandoc import convert_file
    read_me = lambda f: convert_file(f, 'rst')
except ImportError:
    print('pypandoc is not installed.')
    read_me = lambda f: open(f, 'r').read()

setup(name='echonetlite',
      version='0.1.0',
      description='Echonet Lite',
      long_description=read_me('README.md'),
      author='Keiichi SHIMA',
      author_email='keiichi@iijlab.net',
      url='https://github.com/keiichishima/echonetlite',
      packages=['echonetlite'],
      install_requires=['Twisted>=16.3.0'],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: Information Technology',
          'License :: OSI Approved :: BSD License',
          'Programming Language :: Python :: 3.5',
          'Topic :: Home Automation',
          'Topic :: System :: Networking',
          'Topic :: Software Development :: Libraries :: Python Modules'],
      license='BSD License',
  )
