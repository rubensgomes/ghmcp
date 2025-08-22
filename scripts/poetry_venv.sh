#!/usr/bin/env bash
#
# Poetry virtual env setup..
#

poetry config virtualenvs.in-project true || {
  printf "config virtualenvs failed.\n" >&2
  exit 1
}

poetry lock --regenerate -vv || {
  printf "lock --regenerate failed.\n" >&2
  exit 1
}

poetry build || {
  printf "build failed.\n" >&2
  exit 1
}

poetry install || {
  printf "install failed.\n" >&2
  exit 1
}

# display information about virtual environment 
poetry env info

printf "done\n"

