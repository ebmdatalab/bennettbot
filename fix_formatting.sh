#!/bin/bash

declare -a cmds=(
    "black . --exclude .venv"
    "isort **/*.py"
)

for cmd in "${cmds[@]}"; do
  echo "$cmd"
  eval "$cmd"
done
