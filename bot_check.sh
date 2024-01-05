#!/usr/bin/env bash

check_file_path=${BOT_CHECK_FILE:-.bot_startup_check}

if test -f "$check_file_path"; then
  echo "Start up checkfile exists: $check_file_path"
else
  echo "Start up checkfile not found: $check_file_path"
  exit 1
fi
