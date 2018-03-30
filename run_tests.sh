#!/usr/bin/env bash
docker build -t flashfocus .
docker run --rm -p 8083:8083 -t --name flashfocus -e DISPLAY=:0.0 flashfocus
