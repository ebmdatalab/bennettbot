#!/bin/bash

# Note: this is set as the default CMD in the Dockerfile
# In production, dokku extracts the Procfile and uses the commands defined
# there as the entrypoints, so this script is ignored in production. It is
# used only if we're running the production service with docker compose
# https://dokku.com/docs/processes/process-management/#procfile

set -euo pipefail

just run bot
