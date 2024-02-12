#!/bin/bash

set -euo pipefail

while getopts "htaf:" option; do
    case "$option" in
        h)
          command="head"
          ;;
        t)
          command="tail"
          ;;
        a)
          command="all"
          ;;
        f)
          if [[ "$OPTARG" == "error" ]]; then
            filename="stderr"
          elif [[ "$OPTARG" == "output" ]]; then
            filename="stdout"
          else
            echo "Error: invalid logtype '$OPTARG'; must be either 'error' or 'output'"
            exit
          fi
          ;;
        \?) # Invalid option
            echo "Error: Invalid option"
            exit;;
    esac
  done

shift $((OPTIND-1))
logdir=$1
host_dir=${HOST_LOGS_DIR:-$LOGS_DIR}

logfile="$(echo "$logdir" | sed "s|$host_dir|$LOGS_DIR|g")/$filename"
if test -f "$logfile"; then
  echo "Reading $command of log file: $logdir/$filename"
  echo "------------------------------"
  if [[ "$command" == "head" ]]; then
    output=$(head "$logfile")
  elif [[ "$command" == "tail" ]]; then
    output=$(tail "$logfile")
  else
    output=$(cat "$logfile")
  fi
  if [[ "$output" == "" ]]; then
    echo "File has no content"
  else
    echo "$output"
  fi
else
  echo "ERROR: $logdir/$filename not found"
fi
