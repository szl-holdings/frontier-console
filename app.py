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

APP_VERSION = "1.3.1"
START_TS = time.time()
HF_ORG = "SZLHOLDINGS"
GH_ORG = "szl-holdings"

try:
    with io.open(__file__, "rb") as _f:
        SELF_SHA256 = hashlib.sha256(_f.read()).hexdigest()
except Exception:
    SELF_SHA256 = "UNAVAILABLE"


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def receipted(payload: Any, status: str = "OK") -> Response:
    body = json.dumps({"status": status, "ts": _now(), "data": payload}, sort_keys=True).encode()
    r = Response(content=body, media_type="application/json")
    r.headers["X-SZL-Receipt"] = "sha256:" + hashlib.sha256(body).hexdigest()
    r.headers["X-SZL-App"] = "frontier-console/" + APP_VERSION
    r.headers["Cache-Control"] = "no-store"
    return r


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

STRUCTURE_V1 = {
    "id": "khipu-structure-v1-complete",
    "kind": "TRAINING_COMPLETION",
    "status": "AUTHORIZED",
    "ts": "2026-11-18T12:51:52Z",
    "model": "SZLHOLDINGS/salad-khipu-structure-v1",
    "base": "Qwen/Qwen3-1.7B",
    "steps": 2000,
    "final_loss": 0.03599780797958374,
    "gpu_hours": 25.62,
    "corpus_sha256": "0e4a09da905e708b63e661cf83b09df30e9352d143f725a5b24f4a22f107c616",
    "signature": "ed25519 DSSE receipt mesh/khipu-structure-v1-complete.json (SZLHOLDINGS/khipu-scholar-runs)",
    "evidence": "https://huggingface.co/SZLHOLDINGS/salad-khipu-structure-v1",
    "no_decipherment_claims": True,
}


STRUCTURE_EVAL = {
    "id": "eval-khipu-structure-v1",
    "kind": "EVAL_COMPLETION",
    "status": "OBSERVED",
    "ts": "2026-11-19T04:56:50Z",
    "candidate": "SZLHOLDINGS/salad-khipu-structure-v1",
    "metrics": {"cipher_exact_match": 0.9113475177304965, "cipher_n": 282, "eval_rows": 343, "minutes": 4.5},
    "train_sha256_matches_training_receipt": True,
    "receipt": "mesh/eval-khipu-structure-v1-eval.json (SZLHOLDINGS/khipu-scholar-runs)",
    "preds": "mesh/eval-khipu-structure-v1-preds.jsonl",
    "fix_note": "eval group definition patched on Salad 2026-11-19 (split bug: structure split='test', scholar data_files=)",
    "no_decipherment_claims": True,
}

SUPPLY_CHAIN = {
    "status": "ML-BOMs LIVE; ADAPTER SIGNING QUEUED",
    "ml_boms": [
        {"model": "salad-khipu-scholar-v1", "artifact": "bom/ml-bom.json", "spec": "CycloneDX 1.7 ML-BOM", "commit": "6a3677595f90bb857406e026e050bc63078425af"},
        {"model": "salad-khipu-structure-v1", "artifact": "bom/ml-bom.json", "spec": "CycloneDX 1.7 ML-BOM", "commit": "03ceac415c12cca0a3f1fd5cdfd69b36ec4b3f19"},
    ],
    "model_signing": {"lane": "szl-sign-adapters-v1 + clone b", "tool": "CoSAI sigstore model-signing (estate EC P-256 key; ed25519 manifest fallback), fail closed", "restraint": "integrity signing with estate-held key, not keyless OIDC identity", "status": "QUEUED on free tier, auto-park armed"},
    "field_leaders": {
        "provenance": "Sigstore model-signing / CycloneDX 1.7 / OWASP AIBOM / SPDX 3.0",    "throughput": "Unsloth (spec merged, gated on measured smoke test)",
        "corpus_studies": "Metrological Domain Profiling IV (context citation only)",
    },
    "no_decipherment_claims": True,
}

FLEET_SNAPSHOT = {
    "ts": "2026-11-19T09:40Z",
    "lanes": [
        {"lane": "szl-train-khipu-scholar-4b-v1", "status": "RUN #3 + RESILIENCE PATCHED @ 2026-11-19T09:00Z", "note": "silent hard kills diagnosed (no crash receipts); checkpoints now sync to hub every 200 steps + resume-from-latest on boot; honest ETA ~2026-11-20/21 UTC"},
        {"lane": "szl-train-khipu-structure-v1", "status": "COMPLETE + RELEASED @ 12:51:52Z; churn retrain parked 16:42Z", "note": "loss 0.0360 / 2,000 steps / 25.62 GPU-h"},
        {"lane": "szl-eval-khipu-scholar-v1", "status": "EVAL (replicas=1, measured)", "note": "scholar eval lane"},
        {"lane": "szl-eval-khipu-structure-v1", "status": "EVAL COMPLETE (cipher_exact_match 0.9113, n=282, 04:56:50Z), PARKED (replicas=0)", "note": "structure eval lane"},
        {"lane": "szl-sign-adapters-v1", "status": "QUEUED on free tier (cpu-only) since 08:22Z", "note": "CoSAI sigstore model-signing over both released adapters; estate-key fallback; auto-park watcher armed; b-clone hedge szl-sign-adapters-v1b"},
        {"lane": "szl-eval-heritage-transfer-v1", "status": "QUEUED on free tier since 07:18Z", "note": "heritage-transfer eval (47 Lean-verified gold rows); auto-park watcher armed; b-clone hedge szl-eval-heritage-transfer-v1b"},
        {"lane": "szl-inference-v3", "status": "SERVING (replicas=1, measured)", "note": "inference lane"},
    ],
    "total_lanes_measured": 73,
    "watchers": {"mesh_watch": "ALIVE (PID 23704; source lost in cleanup - resilience debt)", "sign_watch": "ALIVE (PID 19760, 24h window): auto-parks sign + heritage lanes on receipt", "train4b_watch": "ALIVE (PID 25144, 48h window): auto-parks 4b train lane on complete receipt"},
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
    # The two P_B4 declarations still contain `sorry` on lutar-lean/main.
    # Do not promote strategy sketches or draft PRs to machine-checked discharges.
    "lean_discharges": ["P_B5", "P_A5.f_n2_up"],
    "open_theorems": [
        "P_B4.entry_bound (source contains sorry; proof candidate under review)",
        "P_B4.n2_base_case (source contains sorry)",
        "putnam_B4_correct (strategy locked: three-bound staircase equality)",
    ],
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
    {"ts": "2026-11-19T09:25Z", "kind": "HEDGE", "detail": "b-clones created (sign-adapters-v1b, eval-heritage-transfer-v1b): deterministic idempotent jobs doubled against free-tier queue; tri-level auto-park (watchers 19760 / 25144 / 24020)"},
    {"ts": "2026-11-19T08:58Z", "kind": "SPEED", "detail": "4b run #4 measured ~33 s/step (vs 72 s earlier runs), step 20 loss 2.96; honest ETA ~2026-11-20 early UTC"},

    {"ts": "2026-11-19T09:00Z", "kind": "RESILIENCE", "detail": "4b lane run #3 restarted 08:36Z after another silent hard kill; PATCHED: checkpoints sync to the runs repo every 200 steps + resume-from-latest on boot + post-complete cleanup"},
    {"ts": "2026-11-19T08:22Z", "kind": "SIGN", "detail": "model-signing lane created (szl-sign-adapters-v1, cpu): CoSAI sigstore model-signing over both released adapters, estate-key fallback, fail closed; auto-park watcher armed"},
    {"ts": "2026-11-19T08:05Z", "kind": "SUPPLY_CHAIN", "detail": "CycloneDX 1.7 ML-BOMs live next to both released adapters (scholar 6a367759, structure 03ceac41), receipt-verified values only"},

    {"ts": "2026-11-19T04:58Z", "kind": "PARK", "detail": "structure eval lane parked (replicas=0) after signed eval receipt; scholar eval keeps auto-parking until 4b adapter lands"},
    {"ts": "2026-11-19T04:56:50Z", "kind": "EVAL", "detail": "structure-v1 eval COMPLETE: cipher_exact_match 0.9113 (n=282 of 343 rows, 4.5 min), receipt + preds on mesh; split bug fixed on Salad"},
    {"ts": "2026-11-19T01:13Z", "kind": "RESTART", "detail": "scholar-4b restarted from scratch (Nov-18 run died silently, step 1260 / loss 0.0081 lost); retraining, ETA ~2026-11-20"},
    {"ts": "2026-11-18T16:42Z", "kind": "RELEASE", "detail": "salad-khipu-structure-v1 PUBLIC: measured card + signed receipt block; churn retrain parked (decommission receipt)"},
    {"ts": "2026-11-18T16:38Z", "kind": "WATCH", "detail": "mesh_watch relaunched (PID 23704); structure eval gate fired on AUTHORIZED complete receipt"},
    {"ts": "2026-11-18T12:51:52Z", "kind": "TRAINING_COMPLETE", "detail": "structure-v1: loss 0.0360 / 2,000 steps / 25.62 GPU-h, DSSE receipt"},
    {"ts": "2026-11-18T02:49Z", "kind": "AUDIT", "detail": "org audit measured: 174 GitHub repos, Salad lanes, HF models/datasets/spaces live-counted"},
    {"ts": "2026-11-18T02:44Z", "kind": "ACCESS", "detail": "szl-lambda-gate -> gated=auto; alyagh pending request auto-granted"},
    {"ts": "2026-11-18T02:43Z", "kind": "OUTREACH", "detail": "3 khipu-scholars co-authorship emails sent from stephen@szlholdings.com (Hyland first)"},
    {"ts": "2026-11-18T02:35Z", "kind": "RELEASE", "detail": "szl-khipu-scholar PR #4 merged (main 0c67eda): scholar-v1 RELEASED"},
    {"ts": "2026-11-18T00:06:08Z", "kind": "TRAINING_COMPLETE", "detail": "scholar-v1: loss 0.0085 / 2,000 steps / 9.45 GPU-h, DSSE receipt"},
    {"ts": "2026-11-17T19:18Z", "kind": "SPACE", "detail": "khipu-proof-loom v2 Space RUNNING (3 min after merge)"},
    {"ts": "2026-11-17T19:15:47Z", "kind": "MERGE", "detail": "Proof Loom v2 merged to szl-khipu main (00002bf1)"},
]

SHOWCASE = {
    "models": [
        {"id": "salad-khipu-scholar-v1", "downloads": 0, "note": "scholar adapter RELEASED"},
        {"id": "salad-khipu-structure-v1", "downloads": 0, "note": "structure adapter RELEASED"},
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
    "repos": ["a11oy", "killinchu", "hatun-mcp", "szl-khipu", "szl-khipu-scholar", "szl-lake", "szl-router", "szl-serve", "platform", "governance-as-code", "szl-evidence-core", "szl-trust", "frontier-54-runs", "frontier-console", "szl-gpu-bridge", "a-11-oy.github.io", "szlholdings.com"],
    "datasets": ["khipu-scholars-corpus-v1", "khipu-scholar-runs", "khipu-scholar-eval-v1", "frontier-54-runs", "killinchu-osint-corpus", "szl-lake", "doctrine-v10-v11", "estate-graph", "governed-receipts-bench", "energy-attested-runs"],
    "kernels": ["kernels/SZLHOLDINGS/szl-lambda-gate (public)", "szl-kernels (299 downloads)"],
}

ESTATE_FALLBACK = {
    "org_github": "https://github.com/szl-holdings",
    "org_hf": "https://huggingface.co/" + HF_ORG,
    "site": "https://szlholdings.com",
    "site_posture_measured": "A 34.111.179.208; TLS handshake fails (SSLEOFError) @ 2026-11-18T02:49Z - DNS/TLS repair is owner-gated",
    "repos_measured": 174,
    "lanes_measured": 73,
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
                insts = insts.get("instances", insts) if isinstance(insts, dict) else insts
                l["instances"] = len(insts) if isinstance(insts, list) else len(str(insts))
            except Exception:
                l["instances"] = "UNKNOWN"
        # Container observations came from Salad; watcher PIDs did not.
        # Never present the dated local watcher snapshot as live provider data.
        return {
            "source": "live",
            "ts": _now(),
            "total_lanes": len(lanes),
            "active": active,
            "parked_count": len(lanes) - len(active),
            "watchers": FLEET_SNAPSHOT["watchers"],
            "watchers_source": "SNAPSHOT",
            "watchers_snapshot_ts": FLEET_SNAPSHOT["ts"],
        }
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
    return receipted({"scholar_v1": SCHOLAR_V1, "structure_v1": STRUCTURE_V1, "structure_eval": STRUCTURE_EVAL, "supply_chain": SUPPLY_CHAIN, "outreach": OUTREACH, "proof": PROOF, "events": EVENTS})


@app.get("/api/governance")
def governance():
    return receipted({"governance": GOVERNANCE, "standards": STANDARDS, "showcase": SHOWCASE})
