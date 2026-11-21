#!/usr/bin/env bash
# From any working directory. No port is published and no provider key is passed.
# Cleanup: remove only the new smoke container/tag and scratch dir on exit.
# Docker may retain shared base-image layers and build cache; never prune them.
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
scratch=$(mktemp -d)
tag="frontier-console-smoke:$(basename "$scratch" | tr '[:upper:]' '[:lower:]')"
cid=
tag_owned=
cleanup() {
  rc=$?
  if [[ -n "$cid" ]]; then docker rm -f "$cid" >/dev/null || rc=1; fi
  if [[ -n "$tag_owned" ]]; then docker image rm "$tag" >/dev/null || rc=1; fi
  rmdir "$scratch" || rc=1
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
if docker image inspect "$tag" >/dev/null 2>&1; then
  echo "Refusing to overwrite an existing smoke tag" >&2
  exit 1
fi
docker build --tag "$tag" .
tag_owned=yes
cid=$(docker run --detach --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges "$tag")
docker exec "$cid" python -c 'import os,sys; sys.exit(0 if os.geteuid() != 0 and sys.version_info[:3] == (3,11,18) else 1)'
app_sha=$(sha256sum app.py | cut -d' ' -f1)
html_sha=$(sha256sum static/index.html | cut -d' ' -f1)
docker exec -i "$cid" python - --app-sha "$app_sha" --html-sha "$html_sha" < tools/runtime_smoke.py
