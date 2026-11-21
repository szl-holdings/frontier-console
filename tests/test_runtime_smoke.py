"""Deterministic negative controls for the offline installed-image probe."""
import hashlib
import json
import unittest
from unittest.mock import patch

from tools import runtime_smoke as smoke

APP = "a" * 64
PAGE = b"<html>source</html>"
HTML = hashlib.sha256(PAGE).hexdigest()


def api(data):
    body = json.dumps({"status": "OK", "data": data}).encode()
    return body, {"Content-Type": "application/json", "X-SZL-Receipt": "sha256:" + hashlib.sha256(body).hexdigest(),
                  "X-SZL-App": "frontier-console/1.3.1"}


class RuntimeSmokeTests(unittest.TestCase):
    def responses(self):
        return {
            "/": (PAGE, {"Content-Type": "text/html; charset=utf-8"}),
            "/api/health": api({"self_sha256": APP, "version": "1.3.1"}),
            "/api/fleet": api({"source": "SNAPSHOT (SALAD_API_KEY not configured)",
                              "snapshot_ts": "2001-01-01T00:00Z"}),
        }

    def check(self, replies, app_sha=APP, html_sha=HTML):
        with patch.object(smoke, "get", side_effect=lambda _port, path: replies[path]):
            return smoke.check(7860, app_sha, html_sha)

    def test_success_only_proves_source_and_snapshot(self):
        result = self.check(self.responses())
        self.assertEqual(result["fleet_mode"], "SNAPSHOT")
        self.assertEqual(result["production_admission"], "NOT_EVALUATED")

    def test_independent_source_and_html_expectations(self):
        for hashes in [(APP, "b" * 64), ("b" * 64, HTML), ("", HTML)]:
            with self.subTest(hashes=hashes), self.assertRaises(ValueError):
                self.check(self.responses(), *hashes)

    def test_modified_body_or_version_is_rejected(self):
        for path in ("/api/fleet", "/api/health"):
            replies = self.responses()
            body, headers = replies[path]
            replies[path] = body + b" ", headers
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.check(replies)
        replies = self.responses()
        replies["/api/health"][1]["X-SZL-App"] = "other/1.3.1"
        with self.assertRaises(ValueError):
            self.check(replies)

    def test_valid_checksum_does_not_make_fleet_live(self):
        for fleet in [{"source": "live", "snapshot_ts": "2001-01-01T00:00Z"},
                      {"source": "SNAPSHOT (SALAD_API_KEY not configured)"},
                      {"source": "SNAPSHOT (SALAD_API_KEY not configured)", "snapshot_ts": True},
                      {"source": "SNAPSHOT (SALAD_API_KEY not configured)", "snapshot_ts": "2001-02-31T00:00Z"}]:
            with self.subTest(fleet=fleet), self.assertRaises(ValueError):
                self.check({**self.responses(), "/api/fleet": api(fleet)})

    def test_correct_bytes_with_wrong_media_type_do_not_pass(self):
        for path in ("/", "/api/health", "/api/fleet"):
            replies = self.responses()
            replies[path][1]["Content-Type"] = "application/octet-stream"
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.check(replies)
