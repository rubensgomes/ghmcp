#!/usr/bin/env bash
#
# Poetry updates.
#

poetry self add poetry-plugin-up || {
  printf "add poetry-plugin-up failed.\n" >&2
  exit 1
}

poetry self update -vvv || {
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

printf "done\n"

