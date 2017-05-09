#!/usr/bin/env python3

from setuptools import setup


setup(name='esl',
      version='1.0.0',
      author='Gennady Kovalev <gik@bigur.ru>',
      description='Scripting language with LUA syntax to embed into '
                  'Python 3 async applications',
      long_description=open('README.md').read(),
      license='LICENSE',
      keywords='python python3 script scripting language lua async embed',
      install_requires=["python3-ply"],
      packages=['esl', 'esl.extensions'])
