from io import open
from setuptools import (
    find_packages,
    setup,
)

# This
import fastentrypoints

setup(
    name='flashfocus',
    version='0.3.6',
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
    scripts=['bin/flash_window_socat'],
    entry_points='''
        [console_scripts]
        flashfocus=flashfocus.ui:cli
        flash_window=flashfocus.client:client_request_flash
    ''',
)
