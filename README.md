---
title: SZL Frontier Console
emoji: 🪢
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# SZL Frontier Console

Receipts-native observability console for the SZL Holdings governed-AI estate. One page: fleet, khipu receipts mesh, models, proofs, governance, standards.

Doctrine v11: deny by default, fail closed, honest UNKNOWN over fabricated green. Every /api/* response carries an X-SZL-Receipt header (sha256 of the raw body). If a live probe fails, the console shows a labeled SNAPSHOT or UNKNOWN, never a fabricated green.

## Stack

- Back end: FastAPI + uvicorn (app.py). Live probes: HF hub anonymous read, GitHub org API, Salad fleet when SALAD_API_KEY is set. Baked hash-pinned estate receipts.
- Front end: single-file static/index.html, no build step, dark mission-control theme, 30s auto-refresh.
- Deploy: Dockerfile (port 7860) for HF Spaces; any container host for szlholdings.com.

## Endpoints

| Route | Payload |
|---|---|
| /api/health | uptime, version, self sha256 of app.py |
| /api/estate | org stats (live), doctrine, links |
| /api/hf | live HF org inventory: models / datasets / spaces + runtime stages |
| /api/fleet | Salad fleet lanes (live if key set; else labeled snapshot) |
| /api/mesh | khipu receipts: scholar-v1 completion, outreach sends, proof results, mesh events |
| /api/governance | doctrine, trust ceiling, open/held gates, standards positions |

## Run locally

pip install -r requirements.txt
uvicorn app:app --port 7860

## Deploy to szlholdings.com

The container runs anywhere Docker runs. Recommended path: owner-gated Cloudflare onboarding (billing and DNS are owner-only per doctrine), point szlholdings.com at the console host, HTTPS via Cloudflare or Caddy. No secrets are required for public operation; SALAD_API_KEY (optional) unlocks live fleet telemetry.

Apache-2.0 aligned with the rest of the estate. (c) SZL Holdings.
