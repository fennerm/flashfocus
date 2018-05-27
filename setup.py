from io import open
from setuptools import (
    find_packages,
    setup,
)

# This speeds up the flash_window script
import fastentrypoints

setup(
    name='flashfocus',
    version='1.0.7',
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
    install_requires=['xcffib', 'click', 'cffi', 'xpybutil', 'marshmallow',
                      'pyyaml'],
    packages=find_packages(exclude=["*test*"]),
    keywords='xorg flash focus i3 bspwm awesomewm herbsluftwm',
    scripts=['bin/nc_flash_window'],
    include_package_data=True,
    entry_points='''
        [console_scripts]
        flashfocus=flashfocus.ui:cli
        flash_window=flashfocus.client:client_request_flash
    ''',
)
