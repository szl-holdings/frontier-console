#!/usr/bin/env python3
"""Bounded, anonymous, read-only release admission for SZL Frontier Console.

A functioning HTTP endpoint or a SHA-256 header is NOT a signed model receipt.
Never treat snapshot fleet data or malformed browser JavaScript as production green.
No tokens, private keys, local caches, Docker, training, or Git worktrees are touched.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
SPACE = "SZLHOLDINGS/frontier-console"
SPACE_API = "https://huggingface.co/api/spaces/" + SPACE
SPACE_HUB = "https://huggingface.co/spaces/" + SPACE
LIVE_URL = "https://szlholdings-frontier-console.hf.space"
ENDPOINTS = ("health", "estate", "hf", "fleet", "mesh", "governance")
MAX_BODY = 2_000_000
TIMEOUT_S = 8
MAX_TIMESTAMP_AGE_S = 900
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256_HEADER = re.compile(r"^sha256:([0-9a-f]{64})$")
SCRIPT = re.compile(rb"<script(?:\s[^>]*)?>(.*?)</script\s*>", re.I | re.S)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str) -> tuple[bytes, dict[str, str]]:
    """Fetch a fixed, public URL; reject oversized or non-200 responses."""
    request = urllib.request.Request(
        url, headers={"User-Agent": "szl-frontier-live-admission/1", "Accept": "*/*"}
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
        status = response.status
        if status != 200:
            raise ValueError("HTTP status not 200")
        data = response.read(MAX_BODY + 1)
        if len(data) > MAX_BODY:
            raise ValueError("response exceeds bounded byte limit")
        return data, {key.lower(): value for key, value in response.headers.items()}


def parse_envelope(body: bytes, headers: dict[str, str]) -> dict[str, Any]:
    """Check exact bytes then parse the API envelope; no claims about source signatures."""
    header = str(headers.get("x-szl-receipt", "")).strip().lower()
    if not SHA256_HEADER.fullmatch(header):
        raise ValueError("missing or malformed response hash")
    if header != "sha256:" + sha256(body):
        raise ValueError("response hash mismatch")
    doc = json.loads(body)
    if not isinstance(doc, dict) or doc.get("status") != "OK":
        raise ValueError("not an OK API envelope")
    if not isinstance(doc.get("data"), dict):
        raise ValueError("API payload is not an object")
    return doc


def timestamp_fresh(ts: Any, *, now: datetime) -> bool:
    if not isinstance(ts, str):
        return False
    try:
        stamp = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return False
    age_s = (now - stamp).total_seconds()
    return -120 <= age_s <= MAX_TIMESTAMP_AGE_S


def script_syntax_ok(html: bytes) -> bool:
    """Check the ACTUAL inline JavaScript syntax using Node without executing it."""
    parts = SCRIPT.findall(html)
    if len(parts) != 1:
        return False
    try:
        p = subprocess.run(
            ["node", "--check", "-"],
            input=parts[0],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return p.returncode == 0


def _result(checks: dict[str, dict[str, str]], name: str, ok: bool, detail: str) -> None:
    checks[name] = {"result": "PASS" if ok else "HOLD", "detail": detail}


def assess(
    *,
    root: Path = ROOT,
    read: Callable[[str], tuple[bytes, dict[str, str]]] = fetch,
    js_valid: Callable[[bytes], bool] = script_syntax_ok,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Collect independent public observations; failures are explicit HOLDs."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must have a time zone")
    checks: dict[str, dict[str, str]] = {}
    hub_sha = None
    hub_app = None
    canonical_app_sha = None
    hub_frontend = None
    checked_at = now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def safe_read(name: str, url: str) -> bytes | None:
        try:
            body, _ = read(url)
            _result(checks, name, True, "anonymous HTTP 200, bounded read")
            return body
        except Exception as e:
            _result(checks, name, False, "public read unavailable (" + type(e).__name__ + ")")
            return None

    try:
        hub_data = safe_read("hub_metadata_read", SPACE_API)
        if hub_data is not None:
            meta = json.loads(hub_data)
            value = str(meta.get("sha", "")).lower()
            if SHA40.fullmatch(value):
                hub_sha = value
            _result(checks, "hub_revision", hub_sha is not None, "exact immutable Space SHA required")
            runtime = meta.get("runtime")
            runtime = runtime if isinstance(runtime, dict) else {}
            runtime_sha = runtime.get("sha")
            _result(
                checks, "runtime_revision_parity",
                hub_sha is not None and isinstance(runtime_sha, str)
                and bool(SHA40.fullmatch(runtime_sha)) and runtime_sha == hub_sha,
                "reported container runtime SHA must match immutable Hub revision",
            )
            _result(
                checks, "space_stage",
                runtime.get("stage") == "RUNNING",
                "Space metadata reports RUNNING (not proof of front-end execution)",
            )
        else:
            _result(checks, "hub_revision", False, "metadata unavailable")
            _result(checks, "runtime_revision_parity", False, "metadata unavailable")
            _result(checks, "space_stage", False, "metadata unavailable")
    except (ValueError, TypeError, AttributeError):
        _result(checks, "hub_revision", False, "malformed Space metadata")
        _result(checks, "runtime_revision_parity", False, "malformed Space metadata")
        _result(checks, "space_stage", False, "malformed Space metadata")

    for label, path in (("app", "app.py"), ("frontend", "static/index.html")):
        local = None
        try:
            local = (root / path).read_bytes()
            _result(checks, label + "_local", True, "source available; sha256=" + sha256(local))
        except OSError:
            _result(checks, label + "_local", False, "canonical GitHub checkout source missing")
        remote = (
            safe_read(label + "_pinned_hub_read", SPACE_HUB + "/resolve/" + hub_sha + "/" + path)
            if hub_sha
            else None
        )
        if remote is None and not hub_sha:
            _result(checks, label + "_pinned_hub_read", False, "immutable Hub SHA unavailable")
        if label == "app":
            hub_app = remote
            if local is not None:
                canonical_app_sha = sha256(local)
        else:
            hub_frontend = remote
        _result(
            checks, label + "_parity",
            local is not None and remote is not None and local == remote,
            "exact canonical GitHub checkout vs immutable Hub bytes; local="
            + (sha256(local) if local is not None else "UNAVAILABLE")
            + " Hub=" + (sha256(remote) if remote is not None else "UNAVAILABLE"),
        )

    page = safe_read("live_frontend_read", LIVE_URL + "/")
    _result(
        checks, "served_frontend_parity",
        page is not None and hub_frontend is not None and page == hub_frontend,
        "actual HTTP-served HTML must equal the immutable Space source",
    )
    _result(
        checks, "served_javascript_syntax",
        page is not None and js_valid(page),
        "actual served inline JavaScript must parse under Node --check",
    )

    expected_version = None
    if hub_app is not None:
        match = re.search(rb'^APP_VERSION\s*=\s*["\']([^"\']+)["\']', hub_app, re.M)
        if match:
            expected_version = match.group(1).decode("ascii", errors="replace")

    for endpoint in ENDPOINTS:
        name = "api_" + endpoint
        try:
            body, headers = read(LIVE_URL + "/api/" + endpoint)
            doc = parse_envelope(body, headers)
            fresh = timestamp_fresh(doc.get("ts"), now=now)
            _result(checks, name + "_hash_envelope", True, "HTTP 200, matching body SHA-256, OK envelope")
            _result(checks, name + "_freshness", fresh, "server timestamp within 15 minutes (with 120s clock skew)")
            data = doc["data"]
            if endpoint == "health":
                ok = expected_version is not None and data.get("version") == expected_version
                _result(checks, "health_version_parity", ok, "API health version must match pinned Space source")
                # Exact equality to the checkout's hexdigest also requires 64 lowercase hex digits.
                _result(checks, "health_self_sha256_parity",
                        canonical_app_sha is not None and data.get("self_sha256") == canonical_app_sha,
                        "API health self_sha256 must match exact canonical GitHub app.py bytes")
            elif endpoint == "fleet":
                _result(
                    checks, "fleet_live_provenance",
                    data.get("source") == "live",
                    "source=" + str(data.get("source", "UNAVAILABLE"))
                    + "; HTTP 200 alone is NOT live Salad evidence",
                )
            elif endpoint == "hf":
                _result(
                    checks, "hf_inventory_live",
                    data.get("source") == "live",
                    "HF inventory live readback required",
                )
            elif endpoint == "estate":
                gh = data.get("github")
                _result(
                    checks, "github_census_live",
                    isinstance(gh, dict) and gh.get("source") == "live",
                    "GitHub census must come from live public API, not a fixed snapshot",
                )
        except Exception as e:
            _result(checks, name + "_hash_envelope", False, "API unavailable or unverified (" + type(e).__name__ + ")")
            _result(checks, name + "_freshness", False, "cannot prove server timestamp freshness")
            required = {"health": "health_version_parity", "fleet": "fleet_live_provenance",
                        "hf": "hf_inventory_live", "estate": "github_census_live"}
            if endpoint in required:
                _result(checks, required[endpoint], False, "API unavailable")
            if endpoint == "health":
                _result(checks, "health_self_sha256_parity", False, "verified health envelope unavailable")
    hold = [name for name, entry in checks.items() if entry["result"] != "PASS"]
    return {
        "schema": "szl.frontier-console.live-admission/v1",
        "checked_at_utc": checked_at,
        "scope": "public GitHub/HF source parity, browser syntax, response integrity, source freshness",
        "admission": "HOLD" if hold else "PASS_FOR_SCOPED_CHECKS_ONLY",
        "hub_revision": hub_sha,
        "hold_checks": hold,
        "checks": checks,
        "limitations": [
            "Unsigned HTTP response digests do not prove cryptographic model provenance.",
            "Historical mesh snapshots do not prove current model evaluation, signing, or training.",
            "The check never authorizes promotion, spending, GPU training, DNS, or secret use.",
        ],
    }


def main() -> int:
    report = assess()
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if report["admission"] == "PASS_FOR_SCOPED_CHECKS_ONLY" else 1


if __name__ == "__main__":
    sys.exit(main())
