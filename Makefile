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

run_tests:
	docker build -t flashfocus .
	docker run --rm -p $(TEST_PORT) -it --name flashfocus -e DISPLAY=:0.0 flashfocus
	docker rm --force flashfocus || true

run_tests_noninteractive:
	docker build -t flashfocus .
	docker run --rm -p $(TEST_PORT) --name flashfocus -e DISPLAY=:0.0 flashfocus
	docker rm --force flashfocus || true

patch_release:
	set -euo pipefail
	$(call update_changelog)
	bumpversion patch
	$(call deploy_to_pypi)
	$(call deploy_to_github)

minor_release:
	set -euo pipefail
	$(call update_changelog)
	bumpversion minor
	$(call deploy_to_pypi)
	$(call deploy_to_github)

major_release:
	set -euo pipefail
	$(call update_changelog)
	bumpversion major
	$(call deploy_to_pypi)
	$(call deploy_to_github)
