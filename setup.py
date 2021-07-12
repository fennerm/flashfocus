from io import open
from setuptools import find_packages, setup

# This speeds up the flash_window script
import fastentrypoints  # noqa: F401

setup(
    name="flashfocus",
    version="2.2.3",
    author="Fenner Macrae",
    author_email="fmacrae.dev@gmail.com",
    description=("Simple focus animations for tiling window managers"),
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://www.github.com/fennerm/flashfocus",
    py_modules=["flashfocus"],
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    python_requires=">=3.6",
    install_requires=[
        "xcffib>=0.6.0,<1.0",
        "click>=6.7,<9.0",
        "cffi>=1.11,<2.0",
        "xpybutil>=0.0.6,<1.0",
        "marshmallow>=2.15,<4.0",
        "pyyaml>=5.1,<6.0",
        "i3ipc>=2.1.1,<3.0",
    ],
    packages=find_packages(exclude=["*test*"]),
    keywords="xorg flash focus i3 bspwm awesomewm herbsluftwm",
    scripts=["bin/nc_flash_window"],
    include_package_data=True,
    entry_points="""
        [console_scripts]
        flashfocus=flashfocus.cli:cli
        flash_window=flashfocus.client:client_request_flash
    """,
)
