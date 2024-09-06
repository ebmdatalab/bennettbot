#!/bin/bash

set -euo pipefail

echo Running ruff
ruff check --output-format=full .
ruff format --diff --quiet .
