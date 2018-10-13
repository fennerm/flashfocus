#!/usr/bin/env bash
supervisord </dev/null &>/dev/null &
sleep 1
python3 -m pytest --failed-first --verbose -x --cov-report term-missing \
    --cov="$PWD" --color yes --showlocals --durations 10 --pdb && \
python2 -m pytest --failed-first --verbose -x --cov-report term-missing \
    --cov="$PWD" --color yes --showlocals --durations 10 --pdb
