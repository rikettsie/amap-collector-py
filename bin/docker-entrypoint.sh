#!/bin/sh
# Default: run the amap_collector CLI, forwarding any flags.
# Override: pass a full command (e.g. uv run pytest) to run it instead.
case "$1" in
  uv|python|pytest) exec "$@" ;;
  *)                exec uv run amap_collector "$@" ;;
esac
