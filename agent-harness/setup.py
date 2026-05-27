#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
setup.py for http-test CLI package.
"""

from setuptools import setup, find_namespace_packages

setup(
    name='cli-anything-http-test',
    version='1.0.0',
    description='HTTP Test CLI - CLI harness for http-test HTTP client tool',
    author='OpenCode',
    packages=find_namespace_packages(
        include=['cli_anything.*'],
        where=['.']
    ),
    package_dir={'': 'cli_anything'},
    include_package_data=True,
    install_requires=[
        'click>=8.0.0',
        'requests>=2.28.0',
    ],
    entry_points={
        'console_scripts': [
            'http-test=cli_anything.http_test.http_test_cli:cli',
        ],
    },
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
)