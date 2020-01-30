#!/bin/bash

# set -euo pipefail

REPO_ROOT=$(dirname $(dirname $0))
VIRTUALENV_PATH=$REPO_ROOT/venv/bin

source "$REPO_ROOT/environment"
source "$VIRTUALENV_PATH/activate"

export PYTHONPATH="$PYTHONPATH:$REPO_ROOT"

python -m ebmbot.$1
