# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in genapi/__init__.py
from genapi import __version__ as version

setup(
	name='genapi',
	version=version,
	description='for api',
	author='Frappé',
	author_email='info@frappe.ioFrappé',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
