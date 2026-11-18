"""
SZL Frontier Console - back end.
Receipts-native observability for the SZL Holdings governed-AI estate.
Doctrine v11: deny by default, fail closed, honest UNKNOWN over fabricated green.
Every /api/* response carries X-SZL-Receipt: sha256 of the raw body.
"""
import hashlib
import io
import json
import os
import time
import urllib.request
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.responses import FileResponse, Response

APP_VERSION = "1.0.0"
START_TS = time.time()
HF_ORG = "SZLHOLDINGS"
GH_ORG = "szl-holdings"

try:
    with io.open(__file__, "r", encoding="utf-8") as _f:
        SELF_SHA256 = hashlib.sha256(_f.read().encode("utf-8")).hexdigest()
except Exception:
    SELF_SHA256 = "UNAVAILABLE"


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def receipted(payload: Any, status: str = "OK") -> Response:
    body = json.dumps({"status": status, "ts": _now(), "data": payload}, sort_keys=True).encode()
    r = Response(content=body, media_type="application/json")
    r.headers["X-SZL-Receipt"] = "sha256:" + hashlib.sha256(body).hexdigest()
    r.headers["X-SZL-App"] = "frontier-console/" + APP_VERSION
    return r


def failed(payload: Any) -> Response:
    return receipted(payload, status="DEGRADED")


# ------------------------------------------------------------------ baked receipts (public evidence, hash-pinned)

SCHOLAR_V1 = {
    "id": "khipu-scholar-v1-complete",
    "kind": "TRAINING_COMPLETION",
    "status": "AUTHORIZED",
    "ts": "2026-11-18T00:06:08Z",
    "model": "SZLHOLDINGS/salad-khipu-scholar-v1",
    "base": "Qwen/Qwen3-1.7B",
    "steps": 2000,
    "final_loss": 0.008520788699388503,
    "gpu_hours": 9.45,
    "corpus_sha256": "0a32769c0d56f11510abdf4f7e83dfaacabc99db3284384b6cf690abf42f7e43",
    "signature": "DSSE-signed mesh receipt, ed25519",
    "evidence": "https://huggingface.co/SZLHOLDINGS/salad-khipu-scholar-v1",
    "card_commits": ["b211e4cb", "b976db65"],
    "no_decipherment_claims": True,
}

FLEET_SNAPSHOT = {
    "ts": "2026-11-18T02:49Z",
    "lanes": [
        {"lane": "szl-eval-khipu-scholar-v1", "status": "EVAL (replicas=1, measured)", "note": "scholar eval lane"},
        {"lane": "szl-eval-khipu-structure-v1", "status": "EVAL (replicas=1, measured)", "note": "structure eval lane"},
        {"lane": "szl-inference-v3", "status": "SERVING (replicas=1, measured)", "note": "inference lane"},
        {"lane": "szl-a11oy-code-train-v2", "status": "TRAINING (replicas=1, measured)", "note": "a11oy code train"},
        {"lane": "szl-frontier54-v2r-all", "status": "RUNNING (replicas=1, measured)", "note": "frontier 54"},
        {"lane": "szl-ring-bench-v1", "status": "BENCH (replicas=1, measured)", "note": "ring bench"},
        {"lane": "szl-ring-bench-v2", "status": "BENCH (replicas=1, measured)", "note": "ring bench"},
        {"lane": "khipu-scholar-4b", "status": "TRAINING (step 640 / loss 0.0106 @ 02:21Z)", "note": "completes 2026-11-19"},
        {"lane": "khipu-structure-v1", "status": "TRAINING (step 1180 / loss 0.0353 @ 02:21Z)", "note": "completes 2026-11-19"},
    ],
    "total_lanes_measured": 145,
    "watchers": {"mesh_watch": "ALIVE (PID 15404 @ 02:45Z)", "complete_watch": "ALIVE (PID 28552 @ 02:45Z)"},
}

OUTREACH = [
    {"who": "Prof. Sabine Hyland", "to": "sph@st-andrews.ac.uk", "ts": "2026-11-18T02:42:54Z", "gmail_id": "1a1ec8928516dbaf", "sent_first": True},
    {"who": "Mackinley FitzPatrick", "to": "mackfitzpatrick@fas.harvard.edu", "ts": "2026-11-18T02:43:07Z", "gmail_id": "1a1ec895feb9cdf4"},
    {"who": "Ashok Khosla", "to": "khipufieldguide@gmail.com", "ts": "2026-11-18T02:43:08Z", "gmail_id": "1a1ec89605d3da74"},
]

PROOF = {
    "spatial_null": {"observed": 54, "expected": 11.035, "p": 0.000999, "receipt": "merged to szl-khipu main"},
    "hjo_certificate": "hjo_certificate_v1.json",
    "proof_loom_v2": {"merged_sha": "00002bf117420363a8844d03cecbd177bd2bd199", "merged_ts": "2026-11-17T19:15:47Z", "space": "https://huggingface.co/spaces/SZLHOLDINGS/khipu-proof-loom", "space_stage_measured": "RUNNING @ 2026-11-18T02:49Z"},
    "lean_discharges": ["P_B5", "P_A5.f_n2_up", "P_B4.n2_base_case", "P_B4.entry_bound"],
    "open_theorems": ["putnam_B4_correct (strategy locked: three-bound staircase equality)"],
}

GOVERNANCE = {
    "doctrine": "v11 LOCKED",
    "trust_ceiling": 0.97,
    "principles": ["Deny by default", "Fail closed", "Signed receipts for every machine action", "Honest UNKNOWN over fabricated green", "Owner gates on irreversible actions"],
    "gates_held": ["PyPI publish (owner-only)", "Cloudflare onboarding: billing/DNS (owner-only)", "szlholdings.com DNS/TLS (owner-only)"],
    "gates_recent": ["szl-lambda-gate flipped gated=auto (2026-11-18): access requests auto-granted, funnel preserved"],
    "components": {
        "a11oy": {"repo": "https://github.com/szl-holdings/a11oy", "role": "governed-AI command center; deny by default, signed receipts, trust ceiling 0.97"},
        "killinchu": {"repo": "https://github.com/szl-holdings/killinchu", "hf": "https://huggingface.co/SZLHOLDINGS/killinchu", "role": "OSINT/vision lane (KILLINCHU-EYE model, killinchu-osint corpus)"},
        "hatun-mcp": {"repo": "https://github.com/szl-holdings/hatun-mcp", "role": "MCP tooling lane (hatun-mcp space, hatun24 train lanes)"},
    },
}

STANDARDS = {
    "positions": ["Agent audit records", "Rule provenance", "Receipts as first-class evidence"],
    "repo": "https://github.com/szl-holdings/platform",
    "path": "docs/standards/positions/",
    "ietf_note": "IETF AUDIT BoF-aligned public positions",
}

EVENTS = [
    {"ts": "2026-11-18T02:49Z", "kind": "AUDIT", "detail": "org audit measured: 174 GitHub repos, 145 Salad lanes, HF models/datasets/spaces live-counted"},
    {"ts": "2026-11-18T02:44Z", "kind": "ACCESS", "detail": "szl-lambda-gate -> gated=auto; alyagh pending request auto-granted"},
    {"ts": "2026-11-18T02:43Z", "kind": "OUTREACH", "detail": "3 khipu-scholars co-authorship emails sent from stephen@szlholdings.com (Hyland first)"},
    {"ts": "2026-11-18T02:35Z", "kind": "RELEASE", "detail": "szl-khipu-scholar PR #4 merged (main 0c67eda): scholar-v1 RELEASED"},
    {"ts": "2026-11-18T00:06:08Z", "kind": "TRAINING_COMPLETE", "detail": "scholar-v1: loss 0.0085 / 2000 steps / 9.45 GPU-h, DSSE receipt"},
    {"ts": "2026-11-17T19:18Z", "kind": "SPACE", "detail": "khipu-proof-loom v2 Space RUNNING (3 min after merge)"},
    {"ts": "2026-11-17T19:15:47Z", "kind": "MERGE", "detail": "Proof Loom v2 merged to szl-khipu main (00002bf1)"},
]

SHOWCASE = {
    "models": [
        {"id": "SZL-Khipu-1.5B-GGUF", "downloads": 5172, "note": "flagship GGUF"},
        {"id": "SZL-Khipu-1.5B", "downloads": 1972, "note": "flagship"},
        {"id": "A11OY-MINI", "downloads": 904, "note": "governed mini"},
        {"id": "chaski", "downloads": 653, "note": "courier lane"},
        {"id": "KHIPU-R2", "downloads": 318, "note": "receipts model"},
        {"id": "WILLAY", "downloads": 303, "note": "messenger lane"},
        {"id": "szl-kernels", "downloads": 299, "note": "live kernels"},
        {"id": "receiptagent-1.5b-v2-trained", "downloads": 133, "note": "receipt agent"},
        {"id": "szl-lambda-gate", "downloads": 69, "note": "auto-gated pointer repo"},
    ],
    "spaces": ["khipu-proof-loom", "a11oy", "killinchu", "counsel", "terra", "sentra", "finance", "anatomy", "szl-frontier", "szl-model-inference-lab", "ayllu", "szl-constellation"],
    "repos": ["a11oy", "killinchu", "hatun-mcp", "szl-khipu", "szl-khipu-scholar", "szl-lake", "szl-router", "szl-serve", "platform", "governance-as-code", "szl-evidence-core", "szl-trust", "frontier-54-runs", "szl-gpu-bridge", "a-11-oy.github.io", "szlholdings.com"],
    "datasets": ["khipu-scholars-corpus-v1", "frontier-54-runs", "killinchu-osint-corpus", "szl-lake", "doctrine-v10-v11", "estate-graph", "governed-receipts-bench", "energy-attested-runs"],
    "kernels": ["kernels/SZLHOLDINGS/szl-lambda-gate (public)", "szl-kernels (299 downloads)"],
}

ESTATE_FALLBACK = {
    "org_github": "https://github.com/szl-holdings",
    "org_hf": "https://huggingface.co/" + HF_ORG,
    "site": "https://szlholdings.com",
    "site_posture_measured": "A 34.111.179.208; TLS handshake fails (SSLEOFError) @ 2026-11-18T02:49Z - DNS/TLS repair is owner-gated",
    "repos_measured": 174,
    "lanes_measured": 145,
}


# ------------------------------------------------------------------ live probes

_CACHE: Dict[str, Any] = {}
_CACHE_TTL = 300.0


def _cache(key: str, fn) -> Any:
    now = time.time()
    hit = _CACHE.get(key)
    if hit and now - hit[0] < _CACHE_TTL:
        return hit[1]
    val = fn()
    _CACHE[key] = (now, val)
    return val


def _hf_inventory() -> Dict[str, Any]:
    try:
        from huggingface_hub import HfApi
        api = HfApi()
        models: List[Dict[str, Any]] = []
        for m in api.list_models(author=HF_ORG):
            models.append({"id": m.id, "gated": str(getattr(m, "gated", None)), "private": bool(getattr(m, "private", False)), "downloads": getattr(m, "downloads", None)})
        datasets = []
        for d in api.list_datasets(author=HF_ORG):
            datasets.append({"id": d.id, "private": bool(getattr(d, "private", False)), "gated": str(getattr(d, "gated", None)), "downloads": getattr(d, "downloads", None)})
        spaces = []
        for s in api.list_spaces(author=HF_ORG):
            rt = getattr(s, "runtime", None)
            spaces.append({"id": s.id, "stage": str(getattr(rt, "stage", "UNKNOWN")) if rt else "UNKNOWN", "private": bool(getattr(s, "private", False))})
        return {"source": "live", "models": models, "datasets": datasets, "spaces": spaces}
    except Exception as e:
        return {"source": "UNAVAILABLE", "error": repr(e)[:200], "models": [], "datasets": [], "spaces": []}


def _gh_stats() -> Dict[str, Any]:
    try:
        req = urllib.request.Request("https://api.github.com/orgs/" + GH_ORG, headers={"User-Agent": "szl-frontier-console"})
        with urllib.request.urlopen(req, timeout=15) as r:
            o = json.loads(r.read().decode())
        return {"source": "live", "public_repos": o.get("public_repos"), "login": o.get("login")}
    except Exception as e:
        return {"source": "UNAVAILABLE", "error": repr(e)[:150], "public_repos_measured": ESTATE_FALLBACK["repos_measured"]}


def _salad_fleet() -> Dict[str, Any]:
    key = os.environ.get("SALAD_API_KEY")
    if not key:
        return {"source": "SNAPSHOT (SALAD_API_KEY not configured)", "snapshot_ts": FLEET_SNAPSHOT["ts"], "lanes": FLEET_SNAPSHOT["lanes"], "total_lanes_measured": FLEET_SNAPSHOT["total_lanes_measured"]}
    base = os.environ.get("SALAD_BASE", "https://api.salad.com/api/public/organizations/alloyscape/projects/default/containers")
    try:
        req = urllib.request.Request(base, headers={"Salad-Api-Key": key})
        with urllib.request.urlopen(req, timeout=20) as r:
            body = json.loads(r.read().decode())
        conts = body if isinstance(body, list) else (body.get("items") or body.get("containers") or [])
        lanes = []
        for c in conts:
            if isinstance(c, dict):
                lanes.append({"lane": c.get("name"), "replicas": c.get("replicas")})
        active = [l for l in lanes if (l.get("replicas") or 0) > 0]
        for l in active[:25]:
            try:
                r2 = urllib.request.urlopen(urllib.request.Request(base + "/" + l["lane"] + "/instances", headers={"Salad-Api-Key": key}), timeout=15)
                insts = json.loads(r2.read().decode())
                l["instances"] = len(insts) if isinstance(insts, list) else len(str(insts))
            except Exception:
                l["instances"] = "UNKNOWN"
        return {"source": "live", "ts": _now(), "total_lanes": len(lanes), "active": active, "parked_count": len(lanes) - len(active), "watchers": FLEET_SNAPSHOT["watchers"]}
    except Exception as e:
        return {"source": "DEGRADED (probe failed)", "error": repr(e)[:200], "snapshot_ts": FLEET_SNAPSHOT["ts"], "lanes": FLEET_SNAPSHOT["lanes"]}


app = FastAPI(title="SZL Frontier Console", version=APP_VERSION)


@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.get("/api/health")
def health():
    return receipted({"app": "frontier-console", "version": APP_VERSION, "uptime_s": round(time.time() - START_TS, 1), "self_sha256": SELF_SHA256, "ts": _now()})


@app.get("/api/estate")
def estate():
    return receipted({"github": _cache("gh", _gh_stats), "site": ESTATE_FALLBACK, "doctrine": GOVERNANCE["doctrine"]})


@app.get("/api/hf")
def hf():
    return receipted(_cache("hf", _hf_inventory))


@app.get("/api/fleet")
def fleet():
    return receipted(_cache("salad", _salad_fleet))


@app.get("/api/mesh")
def mesh():
    return receipted({"scholar_v1": SCHOLAR_V1, "outreach": OUTREACH, "proof": PROOF, "events": EVENTS})


@app.get("/api/governance")
def governance():
    return receipted({"governance": GOVERNANCE, "standards": STANDARDS, "showcase": SHOWCASE})
