#!/usr/bin/env bash
supervisord </dev/null &>/dev/null &
sleep 1
pytest
