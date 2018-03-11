#!/usr/bin/env bash
docker build -t flashfocus .
docker run --rm -p 8083:8083 -ti --name flashfocus -e DISPLAY=:0.0 flashfocus
