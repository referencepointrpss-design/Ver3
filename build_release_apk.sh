#!/usr/bin/env bash
set -e
python3 prebuild_check.py
buildozer -v android release
printf '\nRelease build finished. Check the bin folder.\n'
ls -lh bin || true
