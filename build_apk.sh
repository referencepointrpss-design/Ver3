#!/usr/bin/env bash
set -e

# Run this script from inside the project folder.
# It will use the current virtual environment, or activate ~/buildozer_env if it exists.

if ! command -v buildozer >/dev/null 2>&1; then
    if [ -f "$HOME/buildozer_env/bin/activate" ]; then
        # shellcheck disable=SC1091
        source "$HOME/buildozer_env/bin/activate"
    fi
fi

if ! command -v buildozer >/dev/null 2>&1; then
    echo "Buildozer is not installed or the virtual environment is not activated."
    echo "Run: source ~/buildozer_env/bin/activate"
    exit 1
fi

python3 prebuild_check.py
buildozer -v android debug
