#!/bin/bash

declare -a cmds=(
    "black --check . --exclude .venv"
    "flake8"
    "isort --check-only **/*.py"
)

for cmd in "${cmds[@]}"; do
  echo "$cmd"
  eval "$cmd" || exit 1
done
