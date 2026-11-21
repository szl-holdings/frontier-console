"""Read-only loopback probe of the installed console. Creates no files or processes.

Pass GitHub-checkout hashes, not hashes taken from the image. Never requests
the live estate/HF endpoints or sends credentials. Success is not admission.
"""
import argparse
import hashlib
import http.client
import json
import re
import time
from datetime import datetime

MAX_BYTES = 2 * 1024 * 1024


def get(port, path):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        body = response.read(MAX_BYTES + 1)
        if response.status != 200 or len(body) > MAX_BYTES:
            raise ValueError(f"{path}: non-200 or oversized response")
        return body, response.headers
    finally:
        connection.close()


def data_for(response):
    body, headers = response
    if headers.get("Content-Type", "").partition(";")[0].strip().lower() != "application/json":
        raise ValueError("API route did not serve JSON")
    if headers.get("X-SZL-Receipt") != "sha256:" + hashlib.sha256(body).hexdigest():
        raise ValueError("response checksum absent or mismatched")
    envelope = json.loads(body)
    if envelope.get("status") != "OK" or not isinstance(envelope.get("data"), dict):
        raise ValueError("missing OK data envelope")
    return envelope["data"]


def check(port, app_sha, html_sha):
    if not all(re.fullmatch(r"[0-9a-f]{64}", digest) for digest in (app_sha, html_sha)):
        raise ValueError("two independent SHA-256 expectations are required")
    until = time.monotonic() + 15
    while True:
        try:
            health = get(port, "/api/health")
            break
        except ConnectionRefusedError:
            if time.monotonic() >= until:
                raise
            time.sleep(0.1)
    data = data_for(health)
    if data.get("self_sha256") != app_sha:
        raise ValueError("served app does not match GitHub checkout")
    if health[1].get("X-SZL-App") != "frontier-console/" + data["version"]:
        raise ValueError("health version header mismatch")
    page, headers = get(port, "/")
    if headers.get("Content-Type", "").partition(";")[0].strip().lower() != "text/html":
        raise ValueError("root route did not serve HTML")
    if hashlib.sha256(page).hexdigest() != html_sha:
        raise ValueError("served HTML does not match GitHub checkout")
    fleet = data_for(get(port, "/api/fleet"))
    if fleet.get("source") != "SNAPSHOT (SALAD_API_KEY not configured)":
        raise ValueError("credential-free fleet response is not labeled snapshot")
    stamp = fleet.get("snapshot_ts")
    if not isinstance(stamp, str) or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d(:\d\d)?Z", stamp):
        raise ValueError("snapshot timestamp missing or malformed")
    datetime.fromisoformat(stamp[:-1] + "+00:00")  # valid date; NOT a freshness test
    return {"runtime_smoke": "PASS", "app_sha256": app_sha, "html_sha256": html_sha,
            "fleet_mode": "SNAPSHOT", "production_admission": "NOT_EVALUATED"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--app-sha", required=True)
    parser.add_argument("--html-sha", required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.port, args.app_sha, args.html_sha), sort_keys=True))
