#!/usr/bin/env bash
#
# Start ghmcp server in stdio mode.
#

set -x

cd $(git rev-parse --show-toplevel) || {
  printf "cd to git root failed.\n" >&2
  exit 1
}

declare current_repo
current_repo=$(pwd)

# Set PYTHONPATH to the git root where ghmcp module is located
export PYTHONPATH="$current_repo"

python3 \
  -m ghmcp.main \
  --stdio \
  --repos "/Users/rubens/dev/java/ms-reqresp-lib" \
  --log-level DEBUG || {
  printf "ghmcp.main stdio failed.\n" >&2
  exit 1
  }

printf "done\n"