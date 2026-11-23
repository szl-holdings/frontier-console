# Domain Leader Study — frontier-console (receipts-native FastAPI observability)

OUROBOROS phase-3, cohort-02 tranche-3, Kimi ruling W26-C2T3-EXEC-20261123 (GO, 7 conditions). PROPOSE-ONLY, DRAFT. Documentation only, no implementation in this PR.

## Current state (repo inspection 2026-11-23, W26G receipts)
Receipts-native FastAPI observability: an X-SZL-Receipt sha256 header on every /api/* response, with honest SNAPSHOT/UNKNOWN status values. Sibling estate lanes actively develop this repo (multiple audit/fix/lap branches observed and untouched).

## Domain leaders studied
| Leader | What they have | Key sources |
| --- | --- | --- |
| OpenTelemetry semantic conventions | Standardized attribute names and value sets for HTTP and runtime signals: the reference pattern for making per-response receipt headers and statuses comparable across services | OpenTelemetry semantic-conventions spec, incl. HTTP conventions (https://opentelemetry.io/docs/specs/semconv/) |

## Absorption notes (proposal only)
frontier-console already emits a per-response receipt digest with honest status terms; OTel semconv is the reference pattern for normalization (stable attribute naming, status taxonomies) worth absorbing into the receipt schema so estate consoles remain cross-comparable. No code change proposed in this PR.

## Provenance
Pre-write probes 2026-11-23: no docs/LEADERS-STUDY.md on main; no open PRs; branch name docs/leaders-study-c2t3 absent before creation; source web-verified live 2026-11-23 (W26G citation receipts, spec status + HTTP semconv).

PROPOSE-ONLY: merge requires a separate explicit owner go. Ruling nonce: W26-C2T3-EXEC-20261123.
