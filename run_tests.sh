#!/usr/bin/env bash
docker build -t i3flash .
docker run --rm -p 8083:8083 -ti --name i3flash -e DISPLAY=:0.0 i3flash
