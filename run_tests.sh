#!/usr/bin/env bash
docker build -t flashfocus .
docker run --rm -p 8083:8083 -it --name flashfocus -e DISPLAY=:0.0 flashfocus
docker rm --force flashfocus || true
