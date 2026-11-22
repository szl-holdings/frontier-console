"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { createHash, webcrypto } = require("node:crypto");
const { TextDecoder } = require("node:util");
const { test } = require("node:test");

// Execute exactly the production inline script without its timer/bootstrap tail.
// No network, DOM dependency, tokens, or deployment is needed.
const html = fs.readFileSync(path.join(__dirname, "..", "static", "index.html"), "utf8");
const match = html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(match, "inline script must exist");
const end = match[1].lastIndexOf("function tick(){");
assert.ok(end > 0, "bootstrap boundary must exist");
const context = vm.createContext({ crypto: webcrypto, TextDecoder });
vm.runInContext(match[1].slice(0, end), context, { timeout: 3000, filename: "console-inline.js" });
const parse = vm.runInContext("parseReceiptResponse", context);
const notices = vm.runInContext("auditNotices", context);
const receiptLabel = vm.runInContext("rcp", context);

function response(payload, opts = {}) {
  const bytes = Buffer.from(opts.bytes ?? JSON.stringify(payload), "utf8");
  const signed = Buffer.from(opts.signedBytes ?? bytes);
  const hash = "sha256:" + createHash("sha256").update(signed).digest("hex");
  return {
    ok: opts.ok ?? true,
    status: opts.status ?? 200,
    headers: { get: name => name.toLowerCase() === "x-szl-receipt" ? (opts.header ?? hash) : null },
    arrayBuffer: async () => Uint8Array.from(bytes).buffer,
  };
}

test("HTTP body receipt matches exact bytes and is displayed", async () => {
  const value = await parse(response({ status: "OK", data: { source: "live", count: 2 } }));
  assert.equal(value.data.count, 2);
  assert.equal(value._integrity, "BODY_HASH_MATCH");
  assert.match(receiptLabel(value), /response SHA-256 checked sha256:/);
});

test("tampered body is rejected even when header looks correct", async () => {
  const clean = Buffer.from('{"status":"OK","data":{"count":2}}');
  const tampered = Buffer.from('{"status":"OK","data":{"count":3}}');
  await assert.rejects(() => parse(response({}, { bytes: tampered, signedBytes: clean })), /response hash mismatch/);
});

test("missing and malformed headers fail closed", async () => {
  const payload = { status: "OK", data: {} };
  for (const header of ["", "sha256:abc", "opaque-header"]) {
    await assert.rejects(() => parse(response(payload, { header })), /missing or malformed/);
  }
  assert.match(receiptLabel(null), /UNVERIFIED/);
});

test("HTTP errors and non-OK envelopes fail closed", async () => {
  await assert.rejects(() => parse(response({ status: "OK", data: {} }, { ok: false, status: 503 })), /HTTP 503/);
  await assert.rejects(() => parse(response({ status: "UNAVAILABLE", data: {} })), /response not OK/);
});

test("browser without cryptographic hash support fails closed", async () => {
  const old = context.crypto;
  context.crypto = undefined;
  try {
    await assert.rejects(() => parse(response({ status: "OK", data: {} })), /SHA-256 unavailable/);
  } finally {
    context.crypto = old;
  }
});

test("HTTP 200 does not disguise Salad fleet snapshot as live", () => {
  const results = {
    fleet: { data: { source: "SNAPSHOT (SALAD_API_KEY not configured)", total_lanes_measured: 73 } },
    hf: { data: { source: "live" } },
    estate: { data: { github: { source: "live" } } },
    mesh: { data: { events: [] } },
    governance: { data: { governance: {} } },
    health: { data: { version: "1.3.1" } },
  };
  const labels = notices(results);
  assert.ok(labels.some(x => x.includes("FLEET NOT LIVE")));
  assert.ok(labels.some(x => x.includes("HISTORICAL MESH")));
});

test("missing proof-critical API data is withheld, not filled from stale numbers", () => {
  const view = { innerHTML: "" };
  context.document = { getElementById: () => view };
  vm.runInContext("S.data={mesh:null,governance:null}; render()", context);
  assert.match(view.innerHTML, /PROOF-CRITICAL FEEDS UNAVAILABLE/);
  assert.doesNotMatch(view.innerHTML, /2000 steps|RUNNING \(measured/);
  assert.doesNotMatch(html, /const FALLBACK=/);
});


test("Models page markup is valid JavaScript after pre-existing parser repair", () => {
  new vm.Script(match[1], { filename: "console-inline.js" });
});

// Exercise the *real browser pull() call path*, not just parseReceiptResponse().
// It must actually invoke the parser and the visible audit-notice pathway.
const JS_UNDER_TEST = match[1].slice(0, end);
function syntheticPull({ mutateAllBytes = false, fleetSource = "live", failEndpoint = null, source = JS_UNDER_TEST } = {}) {
  const elements = new Map();
  function getElementById(id) {
    if (!elements.has(id)) elements.set(id, { innerHTML: "", textContent: "", style: {} });
    return elements.get(id);
  }
  const data = {
    health: { version: "1.3.1" },
    estate: { github: { source: "live" }, site: { site_posture_measured: "TEST FIXTURE" } },
    hf: { source: "live", models: [], datasets: [], spaces: [] },
    fleet: { source: fleetSource, lanes: [], watchers: { mesh_watch: "ALIVE (HISTORICAL FIXTURE)" }, watchers_source: "SNAPSHOT", watchers_snapshot_ts: "2026-11-19T09:40Z", total_lanes: 0 },
    mesh: {
      scholar_v1: {
        final_loss: 0.5, corpus_sha256: "a".repeat(64), model: "fixture",
        evidence: "#", status: "REPORTED", base: "fixture", steps: 1,
        gpu_hours: 0, signature: "UNVERIFIED",
      },
      events: [],
    },
    governance: { governance: { principles: [], gates_held: [] } },
  };
  const fetch = async url => {
    const endpoint = url.replace("/api/", "");
    if (!(endpoint in data)) throw Error("unrecognized test endpoint");
    const payload = { status: "OK", data: data[endpoint] };
    const signedBytes = Buffer.from(JSON.stringify(payload));
    const bodyBytes = mutateAllBytes
      ? Buffer.from(JSON.stringify({ ...payload, data: { ...data[endpoint], tampered: true } }))
      : signedBytes;
    const hash = "sha256:" + createHash("sha256").update(signedBytes).digest("hex");
    return {
      ok: endpoint !== failEndpoint,
      status: endpoint === failEndpoint ? 503 : 200,
      headers: { get: name => name.toLowerCase() === "x-szl-receipt" ? hash : null },
      arrayBuffer: async () => Uint8Array.from(bodyBytes).buffer,
      // A malicious source edit could bypass verification and use .json() instead.
      json: async () => JSON.parse(bodyBytes.toString("utf8")),
    };
  };
  const scope = vm.createContext({
    crypto: webcrypto,
    TextDecoder,
    fetch,
    document: { getElementById },
  });
  vm.runInContext(source, scope, { timeout: 3000, filename: "synthetic-console.js" });
  return {
    async run({ tab = "OVERVIEW" } = {}) {
      await vm.runInContext("pull()", scope, { timeout: 3000 });
      if (tab !== "OVERVIEW") {
        vm.runInContext("S.tab=" + JSON.stringify(tab) + ";render()", scope, { timeout: 3000 });
      }
      return {
        live: vm.runInContext("S.live", scope),
        stale: getElementById("stale"),
        view: getElementById("view"),
      };
    },
  };
}

test("browser pull rejects every tampered HTTP-200 receipt instead of accepting JSON", async () => {
  const { live, stale, view } = await syntheticPull({ mutateAllBytes: true }).run();
  assert.equal(live, false);
  assert.match(stale.textContent, /UNAVAILABLE \/ UNVERIFIED API/);
  assert.equal(stale.style.display, "block");
  assert.match(view.innerHTML, /PROOF-CRITICAL FEEDS UNAVAILABLE/);
  assert.doesNotMatch(view.innerHTML, /REPORTED|0\.5000|2000 steps/);
});

test("browser pull shows SNAPSHOT fleet and historical mesh warnings on otherwise valid 200s", async () => {
  const { stale, live } = await syntheticPull({
    fleetSource: "SNAPSHOT (SALAD_API_KEY not configured)",
  }).run();
  assert.equal(live, true);  // All API payload hashes matched; NOT live fleet proof.
  assert.equal(stale.style.display, "block");
  assert.match(stale.textContent, /FLEET NOT LIVE: SNAPSHOT/);
  assert.match(stale.textContent, /HISTORICAL MESH VALUES/);
});

test("live fleet never promotes historical watcher PIDs to live UI", async () => {
  const { view } = await syntheticPull({ fleetSource: "live" }).run({ tab: "FLEET" });
  assert.match(view.innerHTML, /FLEET LANES<\/b> \/ live/);
  assert.match(view.innerHTML, /WATCHERS<\/b> \/ SNAPSHOT @ 2026-11-19T09:40Z/);
  assert.doesNotMatch(view.innerHTML, /WATCHERS<\/b> \/ live/);
});

test("browser pull with one failing proof-critical API withholds cards", async () => {
  const { live, stale, view } = await syntheticPull({ failEndpoint: "governance" }).run();
  assert.equal(live, false);
  assert.match(stale.textContent, /UNAVAILABLE \/ UNVERIFIED API: governance/);
  assert.match(view.innerHTML, /PROOF-CRITICAL FEEDS UNAVAILABLE/);
});

test("mutation sentinels prove these tests catch bypassed verification and hidden warnings", async () => {
  const unverified = JS_UNDER_TEST.replace(
    'res[e]=await parseReceiptResponse(await fetch("/api/"+e,{cache:"no-store"}));',
    'res[e]=await (await fetch("/api/"+e,{cache:"no-store"})).json();',
  );
  assert.notEqual(unverified, JS_UNDER_TEST, "source must call receipt parser in pull()");
  const unsafe = await syntheticPull({ source: unverified, mutateAllBytes: true }).run();
  assert.equal(unsafe.live, true, "fixture must expose parser-bypass mutant");
  const hidden = JS_UNDER_TEST.replace(
    "const notices=auditNotices(res);",
    "const notices=[];",
  );
  assert.notEqual(hidden, JS_UNDER_TEST, "source must call auditNotices in pull()");
  const muted = await syntheticPull({ source: hidden, fleetSource: "SNAPSHOT" }).run();
  assert.equal(muted.stale.style.display, "none", "fixture must expose hidden-warning mutant");
});
