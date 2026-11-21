# Runtime smoke and publication hold

The source workflow qualifies a built image, not the deployed console. Keep
scheduled live admission separate: a green PR check does not supersede a
failed publication check or establish current fleet state.

## Reconciliation of the observed revisions

[Scheduled GitHub run 44924295237](https://github.com/szl-holdings/frontier-console/actions/runs/44924295237)
reported `HOLD` against GitHub `1c7a97560f06ce9a5b199b8e6f387fe0feba7de4`
and immutable Space revision `911281de0294f77c1c09f7da1e8d25e9c32d51fa`.
The following are the SHA-256 of the actual bytes, not signed identities.

| File | Canonical GitHub checkout | Immutable publication observed by the run |
| --- | --- | --- |
| `app.py` | `a0e68564488efddba3f41835ba0ebd34495870589eac009220270a5e1d1aabbf` | `66ae2076c5de2566a5060171656d561227dd55f9e1e115fd719c173d45dc3b64` |
| `static/index.html` | `f9342c95a31736c39f06e685c21a294bfb8e3342900266bbdd7bb210d49427f6` | `e968dc5aed403920b322ada334a58f612937dd4843e4b6541fce730e096402d9` |

Both source parity checks held. The served HTML matched the immutable Space
file, but its inline JavaScript failed the syntax check. The fleet HTTP
response identified itself as `SNAPSHOT (SALAD_API_KEY not configured)`, not
live telemetry. These four holds are observations at that revision and time,
not a claim about a later deployment. Do not copy the failing publication into
GitHub or change the acceptance test to obtain a pass. A separately authorized
publisher would have to reconcile the protected files and measure a new
immutable revision; fleet admission still requires independent live evidence.

## Reproduce the source and image checks

Run from a GitHub checkout on Linux. The source workflow pins Python 3.11.18
and Node 24.22.3; the image uses a digest-pinned official Python base, a
hash-locked wheel set and an unprivileged default user.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/frontend_contract.test.cjs
bash tools/smoke_image.sh
```

The image command needs Docker and network access only for build inputs.
The probe starts the actual image `CMD` with `--network none`, read-only root
and no keys or host port. From inside that network namespace it checks `/`,
`/api/health` and `/api/fleet` over loopback. It compares served HTML and
the app's reported source digest with independent checkout hashes; validates
raw-body checksums and requires the dated credential-free snapshot label.
It never requests `/api/hf` or `/api/estate`. A pass prints
`production_admission: NOT_EVALUATED`; an incorrect source, body checksum or
snapshot label fails. `X-SZL-Receipt` is an unkeyed SHA-256 checksum, not a
DSSE signature or proof of who produced a response. A fresh response timestamp
is not proof that the underlying fleet snapshot is fresh.

The Docker wrapper removes only its temporary container, unique image tag and
empty scratch directory on exit; shared base layers/build cache may remain.
The loopback probe creates no files. Do not run a global Docker prune.

## Dependency refresh

`requirements.txt` is the human-maintained input. With uv 0.12.17, refresh
the exact transitive lock below, review the diff, and rerun the source and
image checks. Omit `--upgrade` to reproduce the already selected versions, as CI does.

```bash
uv pip compile requirements.txt --default-index https://pypi.org/simple \
  --python-version 3.11.18 --universal --generate-hashes --only-binary :all: \
  --no-annotate --no-header --upgrade -o requirements.lock
```

Docker installs with `--require-hashes --only-binary=:all:` and runs
`pip check`; a new release cannot silently change the image dependency graph.
Resolver and Docker caches may remain locally. The only intended tracked
output of the refresh is `requirements.lock`.
