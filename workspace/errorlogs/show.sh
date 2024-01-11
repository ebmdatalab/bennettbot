#!/bin/bash

set -euo pipefail

while getopts "ht" option; do
    case $option in
        h)
          command="head"
          ;;
        t)
          command="tail"
          ;;
        \?) # Invalid option
            echo "Error: Invalid option"
            exit;;
    esac
  done

shift
logdir=$1
host_dir=${HOST_LOGS_DIR:-$LOGS_DIR}

logfile="$(echo "$logdir" | sed "s|$host_dir|$LOGS_DIR|g")/stderr"
if test -f "$logfile"; then
  echo "Reading $command of error log: $logdir/stderr"
  echo "------------------------------"
  if [[ "$command" == "head" ]]; then
    head "$logfile"
  else
    tail "$logfile"
  fi
else
  echo "ERROR: $logdir/stderr not found"
fi
