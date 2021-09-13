# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in wongkar_selling/__init__.py
from wongkar_selling import __version__ as version

setup(
	name='wongkar_selling',
	version=version,
	description='w',
	author='w',
	author_email='w',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
