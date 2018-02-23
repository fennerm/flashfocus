#!/usr/bin/env bash
python -m cProfile -o program.prof run_prof.py
snakeviz program.prof
