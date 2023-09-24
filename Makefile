SHELL=/usr/bin/env bash

define deploy_to_pypi
	set -euo pipefail
	IFS=$$'\n\t'
	scripts/test
	$(call update_changelog)
	bumpversion ${1}
	rm -rf dist src/flashfocus.egg-info
	python3 -m build
	twine upload dist/*
endef
	
define deploy_to_github
	git push origin master
	git push --tags
endef

define update_changelog
	vim CHANGELOG.md
	git add CHANGELOG.md
	git commit -m "Updated changelog"
endef

define deploy
	set -euo pipefail
	scripts/test
	$(call update_changelog)
	bumpversion ${1}
	$(call deploy_to_pypi)
	$(call deploy_to_github)
endef

run_tests:
	scripts/test

run_tests_pdb:
	scripts/test --pdb

patch_release:
	$(call deploy,"patch")

minor_release:
	$(call deploy,"minor")

major_release:
	$(call deploy,"major")
