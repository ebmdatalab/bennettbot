#!/bin/bash

set -euo pipefail

coverage run --module pytest "$@"
coverage report || $BIN/coverage html
