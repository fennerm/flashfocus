from io import open
import os
from setuptools import (
    find_packages,
    setup,
)

import fastentrypoints

setup(
    name='flashfocus',
    version='0.2.0',
    author='Fenner Macrae',
    author_email='fmacrae.dev@gmail.com',
    description=("Simple focus animations for tiling window managers"),
    long_description=open('README.md', 'r', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    license='MIT',
    url='https://www.github.com/fennerm/flashfocus',
    py_modules=['flashfocus'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    install_requires=['xcffib', 'click', 'cffi'],
    packages=find_packages(exclude=["*test*"]),
    keywords='xorg flash focus i3 bpswm awesomewm',
    entry_points='''
        [console_scripts]
        flashfocus=flashfocus.cli:cli
        flash_window=flashfocus.client:client_request_flash
    ''',
)
