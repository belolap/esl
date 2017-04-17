#!/usr/bin/env python3

from setuptools import setup


setup(name='esl',
      version='0.0.2',
      author='Gennady Kovalev <gik@bigur.ru>',
      description='Simple scripting language to use with Python 3',
      long_description=open('README.md').read(),
      license='LICENSE',
      keywords='python python3 script scripting language javascript lua',
      install_requires=["python3-ply"],
      packages=['esl'])
