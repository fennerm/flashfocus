#!/usr/bin/env bash
supervisord </dev/null &>/dev/null &
sleep 1
python3 -m pytest --failed-first --verbose -x --pdb --cov-report term-missing \
    --cov="$PWD"
python2 -m pytest --failed-first --verbose -x --pdb --cov-report term-missing \
    --cov="$PWD"
