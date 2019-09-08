SHELL=/bin/bash

TEST_PORT="8083:8083"

define deploy_to_pypi
	set -euo pipefail
	IFS=$$'\n\t'
	rm -rf dist
	python setup.py sdist
	python setup.py bdist_wheel --universal
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

define run_tests
	docker build -t flashfocus .
	docker run --rm -p $(TEST_PORT) -it --name flashfocus -e DISPLAY=${DISPLAY} flashfocus
	docker rm --force flashfocus || true
endef

define deploy
	set -euo pipefail
	$(call run_tests)
	$(call update_changelog)
	bumpversion ${1}
	$(call deploy_to_pypi)
	$(call deploy_to_github)
endef

run_tests:
	$(call run_tests)

run_tests_noninteractive:
	docker build -t flashfocus .
	docker run --rm -p $(TEST_PORT) --name flashfocus -e DISPLAY=${DISPLAY} flashfocus
	docker rm --force flashfocus || true

patch_release:
	$(call deploy,"patch")

minor_release:
	$(call deploy,"minor")

major_release:
	$(call deploy,"major")
