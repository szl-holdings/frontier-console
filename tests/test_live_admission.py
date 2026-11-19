"""Offline release admission invariants: no network, credentials, or deployments."""
import hashlib
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "tools" / "live_admission.py"
spec = importlib.util.spec_from_file_location("szl_live_admission", MODULE)
admission = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admission)
NOW = datetime(2026, 11, 19, 16, 0, tzinfo=timezone.utc)
SHA = "a" * 40


def api_response(data, *, ts="2026-11-19T16:00:00Z"):
    body = json.dumps({"status": "OK", "ts": ts, "data": data}, sort_keys=True).encode()
    return body, {"x-szl-receipt": "sha256:" + hashlib.sha256(body).hexdigest()}


def fixture(fleet_source="live"):
    local_app = b'APP_VERSION = "1.3.1"\n'
    local_html = b'<html><script>const message="healthy";</script></html>\n'
    urls = {
        admission.SPACE_API: (json.dumps({
            "sha": SHA, "runtime": {"stage": "RUNNING"}
        }).encode(), {}),
        admission.SPACE_HUB + "/resolve/" + SHA + "/app.py": (local_app, {}),
        admission.SPACE_HUB + "/resolve/" + SHA + "/static/index.html": (local_html, {}),
        admission.LIVE_URL + "/": (local_html, {}),
    }
    for ep in admission.ENDPOINTS:
        data = {"source": "live"}
        if ep == "health":
            data = {"version": "1.3.1"}
        if ep == "estate":
            data = {"github": {"source": "live"}}
        if ep == "fleet":
            data = {"source": fleet_source}
        urls[admission.LIVE_URL + "/api/" + ep] = api_response(data)
    return local_app, local_html, urls


class EnvelopeTests(unittest.TestCase):
    def test_valid_receipt(self):
        body, headers = api_response({"version": "1.3.1"})
        self.assertEqual(admission.parse_envelope(body, headers)["data"]["version"], "1.3.1")

    def test_tampered_body_rejected(self):
        body, headers = api_response({"version": "1.3.1"})
        with self.assertRaisesRegex(ValueError, "mismatch"):
            admission.parse_envelope(body.replace(b"1.3.1", b"1.3.2"), headers)

    def test_missing_hash_rejected(self):
        body, _ = api_response({})
        with self.assertRaisesRegex(ValueError, "missing"):
            admission.parse_envelope(body, {})

    def test_non_ok_envelope_rejected_even_with_valid_hash(self):
        body = b'{"status":"UNAVAILABLE","data":{}}'
        header = {"x-szl-receipt": "sha256:" + admission.sha256(body)}
        with self.assertRaisesRegex(ValueError, "not an OK"):
            admission.parse_envelope(body, header)

    def test_fresh_timestamp_limits(self):
        self.assertTrue(admission.timestamp_fresh("2026-11-19T15:46:00Z", now=NOW))
        self.assertFalse(admission.timestamp_fresh("2026-11-19T15:44:00Z", now=NOW))
        self.assertFalse(admission.timestamp_fresh("2026-11-19T16:03:00Z", now=NOW))
        self.assertFalse(admission.timestamp_fresh("INVALID", now=NOW))

    def test_static_js_parse_guard(self):
        self.assertTrue(admission.script_syntax_ok(b"<script>const x=1;</script>"))
        self.assertFalse(admission.script_syntax_ok(b"<script>const x=(;</script>"))
        self.assertFalse(admission.script_syntax_ok(b"<div>No script</div>"))


class AdmissionTests(unittest.TestCase):
    def run_fixture(self, *, fleet="live", alter=None, missing=None):
        app, html, urls = fixture(fleet)
        if alter:
            alter(urls)
        with tempfile.TemporaryDirectory(prefix="szl-admission-tests-") as d:
            root = Path(d)
            (root / "static").mkdir()
            (root / "app.py").write_bytes(app)
            (root / "static" / "index.html").write_bytes(html)

            def read(url):
                if url == missing:
                    raise TimeoutError("offline")
                return urls[url]

            return admission.assess(root=root, read=read, now=NOW)

    def test_all_scoped_obligations_pass(self):
        result = self.run_fixture()
        self.assertEqual(result["admission"], "PASS_FOR_SCOPED_CHECKS_ONLY")
        self.assertEqual(result["hold_checks"], [])
        self.assertIn("Historical mesh snapshots", result["limitations"][1])

    def test_fleet_snapshot_prevents_false_green(self):
        result = self.run_fixture(fleet="SNAPSHOT (SALAD_API_KEY not configured)")
        self.assertEqual(result["admission"], "HOLD")
        self.assertIn("fleet_live_provenance", result["hold_checks"])

    def test_served_js_parse_failure_prevents_false_green(self):
        def mutate(urls):
            invalid = b"<html><script>const x=(;</script></html>"
            urls[admission.LIVE_URL + "/"] = (invalid, {})
            urls[admission.SPACE_HUB + "/resolve/" + SHA + "/static/index.html"] = (invalid, {})
        result = self.run_fixture(alter=mutate)
        self.assertIn("served_javascript_syntax", result["hold_checks"])
        self.assertIn("served_frontend_parity", result["checks"])
        self.assertEqual(result["admission"], "HOLD")

    def test_missing_hub_revision_fails_closed(self):
        result = self.run_fixture(missing=admission.SPACE_API)
        self.assertEqual(result["admission"], "HOLD")
        self.assertIn("hub_revision", result["hold_checks"])
        self.assertIn("app_parity", result["hold_checks"])

    def test_unauthenticated_api_failure_fails_closed(self):
        result = self.run_fixture(missing=admission.LIVE_URL + "/api/health")
        self.assertEqual(result["admission"], "HOLD")
        self.assertIn("api_health_hash_envelope", result["hold_checks"])
        self.assertIn("health_version_parity", result["hold_checks"])

    def test_stale_api_receipt_timestamp_is_not_current_health(self):
        def mutate(urls):
            urls[admission.LIVE_URL + "/api/health"] = api_response(
                {"version": "1.3.1"}, ts="2026-11-19T15:30:00Z"
            )
        result = self.run_fixture(alter=mutate)
        self.assertEqual(result["admission"], "HOLD")
        self.assertIn("api_health_freshness", result["hold_checks"])


if __name__ == "__main__":
    unittest.main()
