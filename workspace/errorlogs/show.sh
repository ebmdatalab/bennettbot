#!/bin/bash

set -euo pipefail

while getopts "hta" option; do
    case $option in
        h)
          command="head"
          ;;
        t)
          command="tail"
          ;;
        a)
          command="all"
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
    output=$(head "$logfile")
  elif [[ "$command" == "tail" ]]; then
    output=$(tail "$logfile")
  else
    output=$(cat "$logfile")
  fi
  echo "\`\`\`$output\`\`\`"
else
  echo "ERROR: $logdir/stderr not found"
fi
