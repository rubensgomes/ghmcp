#!/usr/bin/env bash
#
# Poetry virtual env setup..
#

poetry self update || {
  printf "self update failed.\n" >&2
  exit 1
}

poetry self add poetry-plugin-up || {
  printf "add poetry-plugin-up failed.\n" >&2
  exit 1
}

poetry update -vvv || {
  printf "update failed.\n" >&2
  exit 1
}

poetry up --only=dev --latest || {
    printf "up --only-dev --latest failed.\n" >&2
    exit 1
}

poetry up --latest || {
    printf "up --latest failed.\n" >&2
    exit 1
}

poetry lock --regenerate -vv || {
  printf "lock --regenerate failed.\n" >&2
  exit 1
}

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

