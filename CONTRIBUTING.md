# Installation
* Requires python >=3.8
* `make install_dev`

# Running tests
* Requires docker
* `make run_tests`
* Drop into debugger on failure: `make_run_tests_pdb`
* Alternatively you can create a draft PR and the tests will run automatically.

# Deploying to PyPI
* Requires credentials. Currently handled by @fennerm
* `make <patch_release/minor_release/major_release>`
