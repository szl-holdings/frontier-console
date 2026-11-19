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
