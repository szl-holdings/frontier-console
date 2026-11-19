# Frontier Console source reconciliation — 2026-11-19

Status: **PROPOSED SOURCE-ALIGNMENT CHANGE, NOT A NEW DEPLOYMENT OR FULL PRODUCTION ADMISSION**.

## Bounded, independent readback
- Live Hugging Face Space: `SZLHOLDINGS/frontier-console`.
- Public Space revision read from the Hugging Face API: `3d6359b89f3fec48d5ffbc8e5a90caa5844a7fbf`, runtime stage `RUNNING`.
- Anonymous `/api/health` readback: `status=OK`, `version=1.3.1`.
- SHA-256 of the bytes at `spaces/SZLHOLDINGS/frontier-console/resolve/main/app.py`: `d8f5c123c510687c324a9256ad5aeeaa58800fa4409a050ca7ec3c08c75e2192` (18,404 bytes).
- BETTERWITHAGE staged `C:\SZL\khipu-corpus\_app_v131.py`: same 18,404 bytes and same SHA-256; Python 3.12 `-m ast` parse returned exit 0.
- Before this PR, protected GitHub `main` at `cba3e43d3ca852e95527a1ce0f2590f55135f0b8` contained `APP_VERSION=1.2.0`; local clean checkout at `2da03bdf9557d770d80dcfd76d19e95dc4be9010` contained `1.1.0`.

## Change
Reconcile GitHub `app.py` to the **exact already-running** Hugging Face Space source. This change does **not** update Hugging Face, start or stop training, rotate credentials, modify model weights, or infer production readiness from a `/health` response.

## Remaining release holds
1. Review and merge via normal branch protection and CI. Re-read both GitHub and pinned HF source after merge; require byte-for-byte parity, not only version equality.
2. Reconcile deployed static assets, Dockerfile, requirements, and any future HF revision independently. Do not let a moving `main` silently redefine this pinned observation.
3. Distinguish baked receipt snapshots from live fleet health. Historical `ALIVE`, `SERVING`, or `QUEUED` labels inside source are **not** proof of current process status, signing completion, inference SLO, or training readiness.
4. The workstation's historical `C:\SZL\EstateOps\disk-hygiene\2026-11-17` evidence path was absent during the 2026-11-19 read-only inspection; this PR neither recreates nor attests to the missing historical receipts.

No secret material was read or copied. Worktree, models, receipts, HF cache, Docker/WSL state, and active processes remain untouched.
