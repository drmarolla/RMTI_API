/* RMTI developer portal. No framework, no build step, no third-party requests. DOM is built with textContent only. */
"use strict";
const S = { spec: null, meth: null, ops: [], key: "", base: "" };
const TIER_COL = ["#dbe4ec", "#a9bccd", "#d9a441", "#b5542d", "#7a1f1f"];
const $ = (s, r = document) => r.querySelector(s);

function h(tag, props, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(props || {})) {
    if (v == null || v === false) continue;
    if (k === "class") e.className = v;
    else if (k === "text") e.textContent = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else e.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat(Infinity)) {
    if (kid == null || kid === false) continue;
    e.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return e;
}
const code = (t) => h("code", { text: t });
const slug = (m, p) => (m + p).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const base = () => (S.base || "").replace(/\/+$/, "");

/* ---------------------------------------------------------------- OpenAPI helpers */
function deref(s) {
  if (s && s.$ref) { const n = s.$ref.split("/").pop(); return Object.assign({ _name: n }, S.spec.components.schemas[n]); }
  return s;
}
function nn(s) {                                        // collapse Optional[...] (anyOf with null)
  s = deref(s);
  if (s && s.anyOf) { const c = s.anyOf.filter((x) => x.type !== "null"); return c.length ? nn(Object.assign({}, s, { anyOf: undefined }, deref(c[0]))) : s; }
  return s;
}
function typeOf(s) {
  s = nn(s); if (!s) return "";
  if (s.enum) return "enum";
  if (s.type === "array") return "array<" + (typeOf(s.items) || "any") + ">";
  if (s._name && s.type === "object") return s._name;
  return s.type || (s._name || "");
}
function constraints(s) {
  s = nn(s); const c = [];
  if (!s) return "";
  if (s.minimum != null) c.push("≥ " + s.minimum);
  if (s.exclusiveMinimum != null) c.push("> " + s.exclusiveMinimum);
  if (s.maximum != null) c.push("≤ " + s.maximum);
  if (s.minLength != null) c.push("min length " + s.minLength);
  if (s.maxLength != null) c.push("max length " + s.maxLength);
  if (s.minItems != null) c.push("min items " + s.minItems);
  if (s.maxItems != null) c.push("max items " + s.maxItems);
  if (s.pattern) c.push("pattern " + s.pattern);
  if (s.enum) c.push("one of " + s.enum.join(", "));
  if (s.default !== undefined && s.default !== null) c.push("default " + JSON.stringify(s.default));
  return c.join("; ");
}
function rows(schema, depth = 0, out = []) {
  schema = nn(schema);
  if (!schema) return out;
  if (schema.type === "array") schema = nn(schema.items);
  const props = (schema && schema.properties) || {};
  const req = (schema && schema.required) || [];
  for (const [name, p] of Object.entries(props)) {
    const d = nn(p);
    out.push({ name, depth, type: typeOf(p), required: req.includes(name), desc: (d && (d.description || d.title)) || "", cons: constraints(p) });
    const inner = d && (d.type === "array" ? nn(d.items) : d);
    if (depth < 2 && inner && inner.properties) rows(inner, depth + 1, out);
  }
  return out;
}
function schemaTable(schema) {
  const r = rows(schema);
  if (!r.length) return h("p", { class: "muted", text: "No fields." });
  return h("table", {}, h("thead", {}, h("tr", {}, ["Field", "Type", "Description"].map((x) => h("th", { text: x })))),
    h("tbody", {}, r.map((x) => h("tr", {},
      h("td", { class: "n" }, "\u00a0\u00a0".repeat(x.depth), x.name, x.required ? h("span", { class: "req", text: " required" }) : null),
      h("td", { class: "n", text: x.type }),
      h("td", {}, x.desc, x.cons ? h("div", { class: "muted", text: x.cons }) : null)))));
}
function example(s, d = 0) {
  s = nn(s); if (!s) return null;
  if (s.examples && s.examples.length) return s.examples[0];
  if ("example" in s) return s.example;
  if (s.enum) return s.enum[0];
  switch (s.type) {
    case "object": { const o = {}; for (const k of s.required || []) if (s.properties && s.properties[k]) o[k] = example(s.properties[k], d + 1); return o; }
    case "array": return [example(s.items, d + 1)];
    case "integer": return s.minimum != null ? s.minimum : (s.exclusiveMinimum != null ? s.exclusiveMinimum + 1 : 1);
    case "number": return (s.minimum != null && s.maximum != null) ? +((s.minimum + s.maximum) / 2).toFixed(2) : (s.exclusiveMinimum != null ? s.exclusiveMinimum + 1 : (s.minimum != null ? s.minimum : 0.5));
    case "boolean": return true;
    case "string": return s.pattern ? "EXAMPLE-001" : "string";
    default: return null;
  }
}
const EXAMPLES = {
  "/v1/cohorts/score": () => ({ cohort_name: "demo-cohort", include_records: true, records: [
    { record_id: "FAC-001", likelihood: 0.90, exposure: 0.65, vulnerability: 0.80, resilience: 0.20, resilience_after: 0.55, consequence_level: 5, population: 16000000 },
    { record_id: "FAC-002", likelihood: 0.55, exposure: 0.70, vulnerability: 0.53, resilience: 0.50 }] }),
  "/v1/fhir/RiskAssessment/_batch": () => EXAMPLES["/v1/cohorts/score"](),
  "/v1/simulations": () => ({ likelihood: { mean: 0.9, evidence_grade: "w_ic" }, exposure: { mean: 0.65, evidence_grade: "w_ic" }, vulnerability: { mean: 0.8, evidence_grade: "w_ic" },
    resilience: { mean: 0.2, evidence_grade: "w_ic" }, resilience_after: { mean: 0.55, evidence_grade: "w_ic" }, n_sims: 20000, seed: 42 }),
  "/v1/portfolios/optimize": () => ({ budget: 100, objective: "delta_R", projects: [
    { name: "A-package", group: "city-A", cost: 50, residual_risk_now: 0.408, residual_risk_after: 0.214 },
    { name: "B-package", group: "city-B", cost: 50, residual_risk_now: 0.374, residual_risk_after: 0.211 },
    { name: "C-package", group: "city-C", cost: 50, residual_risk_now: 0.420, residual_risk_after: 0.291 }] }),
  "/v1/hcc/patients/score": () => ({ albumin_unit: "g/L", bilirubin_unit: "umol/L", patients: [
    { record_id: "PT-001", likelihood: 0.30, exposure: 0.60, albi_grade: 1, surveillance: "usual", bclc_if_missed: "A", improved_surveillance: "optimised" },
    { record_id: "PT-002", likelihood: 0.25, exposure: 0.60, albumin: 30, bilirubin: 50, surveillance: "usual", bclc_if_missed: "C-D", improved_surveillance: "optimised" }] }),
  "/v1/hcc/albi": () => ({ albumin: 38, bilirubin: 17, albumin_unit: "g/L", bilirubin_unit: "umol/L" }),
};
const SAMPLE_CSV = {
  "/v1/cohorts/score/upload": "record_id,likelihood,exposure,vulnerability,resilience,resilience_after,consequence_level,population\nFAC-001,0.90,0.65,0.80,0.20,0.55,5,16000000\nFAC-002,0.55,0.70,0.53,0.50,0.65,4,1100000\n",
  "/v1/hcc/patients/score/upload": "id,L,E,albumin,bilirubin,surveillance,bclc_if_missed\nPT-001,0.30,0.60,38,17,usual,A\nPT-002,0.25,0.60,30,50,usual,C-D\n",
};
function ordered(v, s) {                                 // keep the schema's field order in examples
  s = nn(s);
  if (Array.isArray(v)) return v.map((x) => ordered(x, s && s.items));
  if (v && typeof v === "object" && s && s.properties) {
    const o = {};
    for (const k of Object.keys(s.properties)) if (k in v) o[k] = ordered(v[k], s.properties[k]);
    for (const k of Object.keys(v)) if (!(k in o)) o[k] = v[k];
    return o;
  }
  return v;
}
function bodyExample(op) {
  if (EXAMPLES[op.path]) return EXAMPLES[op.path]();
  return op.schema ? ordered(example(op.schema), op.schema) : null;
}

/* ---------------------------------------------------------------- operations */
function parseOps(spec) {
  const ops = [];
  for (const [path, item] of Object.entries(spec.paths || {})) {
    for (const method of ["get", "post"]) {
      const o = item[method]; if (!o) continue;
      const content = (o.requestBody && o.requestBody.content) || {};
      const mime = Object.keys(content)[0] || null;
      ops.push({ method, path, slug: slug(method, path), tag: (o.tags || ["Other"])[0], summary: o.summary || path, description: o.description || "",
        scope: o["x-required-scope"] || null, mime, multipart: mime === "multipart/form-data", schema: mime ? content[mime].schema : null, responses: o.responses || {} });
    }
  }
  return ops;
}
const methodPill = (m) => h("span", { class: "pill " + m, text: m.toUpperCase() });

/* ---------------------------------------------------------------- code snippets (the key is never inlined) */
function snippets(op, body) {
  const url = base() + op.path;
  const json = body == null ? "" : JSON.stringify(body, null, 2);
  const m = op.method.toUpperCase();
  if (op.multipart) {
    const fields = Object.keys(((nn(op.schema) || {}).properties) || {}).filter((k) => k !== "file");
    const ff = fields.map((k) => [k, k === "cohort_name" ? "demo-cohort" : "..."]);
    const file = op.path.includes("hcc") ? "registry.csv" : "cohort.csv";
    return {
      cURL: `curl -X POST "${url}" \\\n  -H "X-API-Key: $RMTI_API_KEY" \\\n` + ff.filter((x) => x[1] !== "...").map((x) => `  -F "${x[0]}=${x[1]}" \\\n`).join("") + `  -F "file=@${file}"`,
      Python: `import os, requests\n\nr = requests.post(\n    "${url}",\n    headers={"X-API-Key": os.environ["RMTI_API_KEY"]},\n    data=${JSON.stringify(Object.fromEntries(ff.filter((x) => x[1] !== "...")))},\n    files={"file": open("${file}", "rb")},\n    timeout=60,\n)\nr.raise_for_status()\nprint(r.json())`,
      R: `library(httr2)\n\nresp <- request("${url}") |>\n  req_headers("X-API-Key" = Sys.getenv("RMTI_API_KEY")) |>\n  req_body_multipart(${ff.filter((x) => x[1] !== "...").map((x) => `${x[0]} = "${x[1]}", `).join("")}file = curl::form_file("${file}")) |>\n  req_perform()\n\nresp_body_json(resp)`,
      JavaScript: `const fd = new FormData();\n${ff.filter((x) => x[1] !== "...").map((x) => `fd.append("${x[0]}", "${x[1]}");\n`).join("")}fd.append("file", fileInput.files[0]);\n\nconst r = await fetch("${url}", {\n  method: "POST",\n  headers: { "X-API-Key": process.env.RMTI_API_KEY },\n  body: fd,\n});\nconsole.log(await r.json());`,
    };
  }
  if (op.method === "get") {
    return { cURL: `curl "${url}"`, Python: `import requests\nprint(requests.get("${url}", timeout=30).json())`,
      R: `library(httr2)\nrequest("${url}") |> req_perform() |> resp_body_json()`, JavaScript: `const r = await fetch("${url}");\nconsole.log(await r.json());` };
  }
  const pyBody = json.replace(/\btrue\b/g, "True").replace(/\bfalse\b/g, "False").replace(/\bnull\b/g, "None");
  const accept = op.path.includes("/fhir/") ? "application/fhir+json" : "application/json";
  return {
    cURL: `curl -X ${m} "${url}" \\\n  -H "Content-Type: application/json" \\\n  -H "Accept: ${accept}" \\\n  -H "X-API-Key: $RMTI_API_KEY" \\\n  --data-binary @- <<'JSON'\n${json}\nJSON`,
    Python: `import os, requests\n\npayload = ${pyBody}\n\nr = requests.post(\n    "${url}",\n    json=payload,\n    headers={"X-API-Key": os.environ["RMTI_API_KEY"]},\n    timeout=60,\n)\nr.raise_for_status()\nprint(r.json())`,
    R: `library(httr2)\nlibrary(jsonlite)\n\npayload <- fromJSON('${JSON.stringify(body)}', simplifyVector = FALSE)\n\nresp <- request("${url}") |>\n  req_headers("X-API-Key" = Sys.getenv("RMTI_API_KEY")) |>\n  req_body_json(payload, auto_unbox = TRUE) |>\n  req_perform()\n\nresp_body_json(resp)`,
    JavaScript: `const r = await fetch("${url}", {\n  method: "POST",\n  headers: {\n    "Content-Type": "application/json",\n    "X-API-Key": process.env.RMTI_API_KEY,\n  },\n  body: JSON.stringify(${json.replace(/\n/g, "\n  ")}),\n});\nif (!r.ok) throw new Error(await r.text());\nconsole.log(await r.json());`,
  };
}
function copyText(t, btn) {
  const done = () => { const o = btn.textContent; btn.textContent = "Copied"; setTimeout(() => (btn.textContent = o), 1200); };
  if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(done, () => {});
}
function codePanel(map) {
  const names = Object.keys(map); let cur = names[0];
  const pre = h("pre"), copy = h("button", { class: "copy", type: "button", text: "Copy" });
  const tabs = h("div", { class: "tabs", role: "tablist" });
  const show = (n) => { cur = n; pre.textContent = map[n]; [...tabs.querySelectorAll("button[role=tab]")].forEach((b) => b.setAttribute("aria-selected", String(b.textContent === n))); };
  names.forEach((n) => tabs.append(h("button", { type: "button", role: "tab", text: n, onclick: () => show(n) })));
  copy.addEventListener("click", () => copyText(map[cur], copy)); tabs.append(copy);
  show(cur);
  return h("div", { class: "panel" }, tabs, pre);
}

/* ---------------------------------------------------------------- try it */
function tryIt(op, body) {
  const ta = op.multipart ? null : h("textarea", { "aria-label": "Request body", spellcheck: "false" });
  if (ta && op.method === "post") ta.value = JSON.stringify(body, null, 2);
  const out = h("div", { class: "resp", "aria-live": "polite" });
  const file = op.multipart ? h("input", { type: "file", accept: ".csv,.parquet", "aria-label": "File" }) : null;
  const fields = {};
  const extra = [];
  if (op.multipart) {
    for (const k of Object.keys(((nn(op.schema) || {}).properties) || {})) {
      if (k === "file") continue;
      fields[k] = h("input", { type: "text", value: k === "cohort_name" ? "demo-cohort" : (k.endsWith("_unit") ? (k.startsWith("alb") ? "g/L" : "umol/L") : (k === "include_records" ? "true" : "")), "aria-label": k });
      extra.push(h("label", { class: "muted", text: k }), fields[k]);
    }
  }
  const btn = h("button", { class: "btn", type: "button", text: "Send request" });
  const sample = SAMPLE_CSV[op.path] ? h("a", { href: "#", text: "Download sample CSV", onclick: (e) => {
    e.preventDefault(); const a = h("a", { href: URL.createObjectURL(new Blob([SAMPLE_CSV[op.path]], { type: "text/csv" })), download: "sample.csv" }); a.click(); } }) : null;
  btn.addEventListener("click", async () => {
    out.replaceChildren(); btn.disabled = true;
    const headers = {}; if (S.key) headers["X-API-Key"] = S.key;
    let payload;
    if (op.multipart) {
      if (!file.files[0]) { out.append(h("p", { class: "err", text: "Choose a file first." })); btn.disabled = false; return; }
      payload = new FormData(); for (const [k, el] of Object.entries(fields)) payload.append(k, el.value); payload.append("file", file.files[0]);
    } else if (op.method === "post") { headers["Content-Type"] = "application/json"; payload = ta.value; }
    const t0 = performance.now();
    try {
      const r = await fetch(base() + op.path, { method: op.method.toUpperCase(), headers, body: payload });
      const text = await r.text(); let pretty = text; try { pretty = JSON.stringify(JSON.parse(text), null, 2); } catch (_) {}
      const hd = (n) => r.headers.get(n);
      out.append(h("div", { class: "line" }, h("strong", { class: r.ok ? "ok" : "err", text: r.status + " " + (r.statusText || "") }), h("span", { text: Math.round(performance.now() - t0) + " ms" }),
        hd("x-request-id") ? h("span", { text: "request-id " + hd("x-request-id") }) : null, hd("x-ratelimit-remaining") ? h("span", { text: "remaining " + hd("x-ratelimit-remaining") }) : null),
        h("div", { class: "panel" }, h("pre", { text: pretty.length > 60000 ? pretty.slice(0, 60000) + "\n… (truncated in the viewer)" : pretty })));
    } catch (e) { out.append(h("p", { class: "err", text: "Request failed: " + e.message + ". Check the base URL and CORS settings." })); }
    btn.disabled = false;
  });
  return h("section", { class: "try", "aria-label": "Try this endpoint" }, h("h3", { text: "Try it" }),
    op.scope ? h("p", { class: "muted" }, "Uses the key from the Connection panel. Requires scope ", h("span", { class: "scope", text: op.scope }), ".") : h("p", { class: "muted", text: "Public endpoint; no key required." }),
    ta, file, ...extra, sample ? h("p", {}, sample) : null, h("p", {}, btn), out);
}

/* ---------------------------------------------------------------- pages */
const P = {};
P.overview = () => h("div", {},
  h("h1", { text: "RMTI API" }),
  h("p", { class: "lead", text: "Programmatic access to the Risk Mechanism Theory Index: a bounded residual-risk score R = L × E × V × (1 − ρ), five fixed decision tiers, expected annual loss, uncertainty propagation, portfolio selection, hepatocellular-carcinoma surveillance triage, and HL7 FHIR R4 output." }),
  h("div", { class: "callout warn" }, h("strong", { text: "Scope of use. " }), "Research prototype, not validated against outcomes and not a medical device. Results are decision-support indices, not probabilities. Do not send protected health information; use de-identified identifiers. The service holds no HIPAA attestation, BAA, SOC 2 or ISO 27001 certification."),
  h("h2", { text: "Base URL and versioning" }),
  h("p", {}, "All endpoints are under ", code("/v1"), ". Requests and responses are JSON (UTF-8), except file uploads (multipart) and FHIR output (", code("application/fhir+json"), "). Breaking changes will use a new path prefix."),
  h("h2", { text: "What is available" }),
  h("table", {}, h("thead", {}, h("tr", {}, ["Area", "Endpoints", "Scope"].map((x) => h("th", { text: x })))),
    h("tbody", {}, tagsInOrder().map((t) => h("tr", {}, h("td", { text: t }),
      h("td", {}, S.ops.filter((o) => o.tag === t).map((o, i) => [i ? ", " : "", h("a", { href: "#/op/" + o.slug, text: o.path })])),
      h("td", {}, [...new Set(S.ops.filter((o) => o.tag === t).map((o) => o.scope || "public"))].map((s) => h("span", { class: "scope", text: s })))))) ),
  h("h2", { text: "What it does not do" }),
  h("ul", { class: "clean" }, S.meth.limitations.map((x) => h("li", { text: x }))),
  h("h2", { text: "Get started" }),
  h("p", {}, "Read ", h("a", { href: "#/authentication", text: "Authentication" }), ", then follow the ", h("a", { href: "#/quickstart", text: "Quickstart" }), ". Operators deploying the API: see the repository documentation on key issuance."));

P.authentication = () => h("div", {},
  h("h1", { text: "Authentication" }),
  h("p", { class: "lead", text: "Protected endpoints require an institutional API key in the X-API-Key header." }),
  h("div", { class: "panel" }, h("pre", { text: 'curl "' + base() + '/v1/assessments" -H "X-API-Key: $RMTI_API_KEY" ...' })),
  h("h2", { text: "Scopes" }),
  h("table", {}, h("thead", {}, h("tr", {}, ["Scope", "Grants", "Endpoints"].map((x) => h("th", { text: x })))),
    h("tbody", {}, [["score", "Single assessments, simulation, HCC scoring"], ["batch", "Cohort scoring, uploads, portfolio optimisation"], ["fhir", "FHIR R4 RiskAssessment / Bundle output"]].map(([s, g]) =>
      h("tr", {}, h("td", {}, h("span", { class: "scope", text: s })), h("td", { text: g }), h("td", {}, S.ops.filter((o) => o.scope === s).map((o, i) => [i ? ", " : "", h("a", { href: "#/op/" + o.slug, text: o.path })])))))),
  h("h2", { text: "Obtaining a key" }),
  h("p", {}, "Keys are issued out of band by the operator of this deployment" + (S.meth.contact ? " (contact: " + S.meth.contact + ")" : "") + ". A key is shown once; the server stores only its SHA-256 digest. Treat keys as secrets: keep them in environment variables or a secret manager, never in source control or client-side code."),
  h("h2", { text: "Rate limits" }),
  h("p", {}, "Each key has a per-minute limit. Responses carry ", code("X-RateLimit-Limit"), " and ", code("X-RateLimit-Remaining"), "; when exceeded the API returns ", code("429"), " with ", code("Retry-After"), " (seconds)."),
  h("h2", { text: "Status codes" }),
  h("table", {}, h("tbody", {}, [["401", "Key missing or not recognised."], ["403", "Key is valid but lacks the required scope."], ["429", "Rate limit exceeded."], ["503", "Server has no API clients configured (it refuses protected requests rather than run open)."]]
    .map(([c, d]) => h("tr", {}, h("td", { class: "n", text: c }), h("td", { text: d }))))));

P.quickstart = () => {
  const op = S.ops.find((o) => o.path === "/v1/assessments") || S.ops[0];
  const body = bodyExample(op);
  return h("div", {}, h("h1", { text: "Quickstart" }),
    h("p", { class: "lead", text: "Score one unit in three steps." }),
    h("h3", { text: "1. Export your key" }), h("div", { class: "panel" }, h("pre", { text: 'export RMTI_API_KEY="rmti_…"' })),
    h("h3", { text: "2. Send an assessment" }), codePanel(snippets(op, body)),
    h("h3", { text: "3. Read the result" }),
    h("p", {}, "The response contains ", code("residual_risk"), " (R), ", code("tier"), " (1–5), ", code("tier_label"), ", the decision ", code("posture"), ", and — when ", code("resilience_after"), " is supplied — the scenario result and ", code("risk_reduction_pct"), ". ", code("margin"), " shows how far a one-parameter error is from changing the tier."),
    h("p", {}, "Full parameter reference: ", h("a", { href: "#/op/" + op.slug, text: op.method.toUpperCase() + " " + op.path }), "."));
};

P.reference = () => h("div", {}, h("h1", { text: "API reference" }),
  tagsInOrder().map((t) => h("div", {}, h("h2", { text: t }),
    h("table", {}, h("tbody", {}, S.ops.filter((o) => o.tag === t).map((o) => h("tr", {}, h("td", {}, methodPill(o.method)), h("td", { class: "n" }, h("a", { href: "#/op/" + o.slug, text: o.path })),
      h("td", { text: o.summary }), h("td", {}, h("span", { class: "scope", text: o.scope || "public" })))))))));

function opPage(slugv) {
  const op = S.ops.find((o) => o.slug === slugv); if (!op) return notFound();
  const body = bodyExample(op);
  const resp = Object.entries(op.responses).map(([c, r]) => h("tr", {}, h("td", { class: "n", text: c }), h("td", { text: r.description || "" })));
  return h("div", { class: "grid" },
    h("div", {}, h("h1", { text: op.summary }), h("p", {}, methodPill(op.method), " ", code(op.path), " ", h("span", { class: "scope", text: op.scope ? "scope: " + op.scope : "public" })),
      op.description ? h("p", { text: op.description }) : null,
      op.schema ? [h("h2", { text: op.multipart ? "Form fields" : "Request body" }), op.multipart ? multipartTable(op) : schemaTable(op.schema)] : null,
      h("h2", { text: "Responses" }), h("table", {}, h("tbody", {}, resp))),
    h("div", {}, codePanel(snippets(op, body)), tryIt(op, body)));
}
function multipartTable(op) {
  const props = (nn(op.schema) || {}).properties || {}; const req = (nn(op.schema) || {}).required || [];
  return h("table", {}, h("tbody", {}, Object.entries(props).map(([k, p]) => h("tr", {}, h("td", { class: "n" }, k, req.includes(k) ? h("span", { class: "req", text: " required" }) : null), h("td", { class: "n", text: k === "file" ? "file" : typeOf(p) }), h("td", { text: (nn(p) || {}).description || "" })))));
}

P.schemas = () => h("div", {}, h("h1", { text: "Schemas" }),
  Object.entries(S.spec.components.schemas).filter(([n]) => !/^(Body_|HTTPValidationError|ValidationError)/.test(n)).map(([n, s]) =>
    h("div", {}, h("h2", { id: "s-" + n, text: n }), s.description ? h("p", { text: s.description }) : null, schemaTable({ $ref: "#/components/schemas/" + n }))));

P.methodology = () => {
  const m = S.meth;
  return h("div", {}, h("h1", { text: "Methodology" }),
    h("p", { class: "lead", text: "The engine is the open-source rmti-py library (Apache-2.0). This page is generated from the running service." }),
    h("h2", { text: "Equations" }), h("table", { class: "kv" }, h("tbody", {}, Object.entries(m.equations).map(([k, v]) => h("tr", {}, h("td", { text: k.replace(/_/g, " ") }), h("td", { class: "n", text: v }))))),
    h("h2", { text: "Parameters" }), h("table", { class: "kv" }, h("tbody", {}, Object.entries(m.parameters).map(([k, v]) => h("tr", {}, h("td", { class: "n", text: k }), h("td", { text: v }))))),
    h("h2", { text: "Decision tiers" }),
    h("p", { text: "Fixed and pre-registered; never re-derived from a sample. Colour is decorative; the tier number and label carry the meaning." }),
    h("table", {}, h("thead", {}, h("tr", {}, ["Tier", "Label", "Range of R", "Posture"].map((x) => h("th", { text: x })))),
      h("tbody", {}, m.tiers.map((t) => h("tr", {}, h("td", {}, h("span", { class: "sw", style: "background:" + TIER_COL[t.tier - 1] }), String(t.tier)), h("td", { text: t.label }), h("td", { class: "n", text: t.range }), h("td", { text: t.posture }))))),
    h("h2", { text: "Assumptions you must carry into any report" }),
    h("p", {}, "The simulation endpoint maps each Weight-of-Evidence grade to a Beta concentration. These values are ", h("strong", { text: "assumed" }), ", not derived from the source rubric, and tier probabilities depend on them."),
    h("table", { class: "kv" }, h("tbody", {}, Object.entries(m.evidence_grade_concentration_ASSUMED).map(([k, v]) => h("tr", {}, h("td", { class: "n", text: k }), h("td", { class: "n", text: "concentration " + v }))))),
    h("h2", { text: "Limitations" }), h("ul", { class: "clean" }, m.limitations.map((x) => h("li", { text: x }))),
    h("h2", { text: "Citation" }), h("p", { text: m.citation }));
};

P.fhir = () => {
  const f = S.meth.fhir;
  const map = [["RiskAssessment.status", "always “preliminary” (research prototype)"], ["RiskAssessment.method", "“Risk Mechanism Theory Index (RMTI)”"],
    ["RiskAssessment.subject.identifier", "record_id (de-identified); system urn:rmti:record-id"], ["RiskAssessment.occurrenceDateTime", "time of scoring (UTC)"],
    ["prediction[0].qualitativeRisk", "tier code 1–5 in urn:rmti:codesystem:residual-risk-tier"], ["prediction[1]", "tier after the proposed intervention, when resilience_after is supplied"],
    ["extension …:residual-risk", "R as a decimal — an index, deliberately NOT probabilityDecimal"], ["extension …:inherent-risk, …:expected-annual-loss-index", "IR and EAL index"], ["note", "statement that R is an index, not a probability"]];
  return h("div", {}, h("h1", { text: "FHIR R4 output" }),
    h("p", { class: "lead", text: "Results can be returned as HL7 FHIR " + f.version + " RiskAssessment resources, or as a collection Bundle for cohorts." }),
    h("div", { class: "callout warn" }, h("strong", { text: "Not a FHIR server. " }), "This API produces RiskAssessment resources from posted inputs. It offers no read, search, history or capability statement, and stores no patient data. The code system and extension URLs are project URNs (placeholders until canonical URLs are published). Structure is tested against the fhir.resources R4B models; the output has not been run through the official HL7 validator or a conformance profile."),
    h("h2", { text: "Mapping" }), h("table", {}, h("thead", {}, h("tr", {}, ["FHIR element", "Content"].map((x) => h("th", { text: x })))), h("tbody", {}, map.map(([a, b]) => h("tr", {}, h("td", { class: "n", text: a }), h("td", { text: b }))))),
    h("h2", { text: "Example resource" }), codePanel({ "FHIR JSON": JSON.stringify(f.example, null, 2) }),
    h("h2", { text: "Endpoints" }), h("ul", { class: "clean" }, S.ops.filter((o) => o.tag === "FHIR R4").map((o) => h("li", {}, methodPill(o.method), " ", h("a", { href: "#/op/" + o.slug, text: o.path })))));
};

P.compliance = () => {
  const d = S.meth.data_handling, c = d.certifications;
  const yn = (v) => (v ? "Yes" : "No");
  return h("div", {}, h("h1", { text: "Data handling and compliance status" }),
    h("p", { class: "lead", text: "A plain statement of what this deployment does and does not provide. Read it before connecting any health-related data." }),
    h("h2", { text: "What the service does" }),
    h("table", { class: "kv" }, h("tbody", {}, ["persistence", "payload_logging", "api_keys", "transport_security", "phi"].map((k) => h("tr", {}, h("td", { text: k.replace(/_/g, " ") }), h("td", { text: d[k] }))))),
    h("h2", { text: "Certifications and agreements" }),
    h("table", { class: "kv" }, h("tbody", {}, [["HIPAA Business Associate Agreement available", c.hipaa_baa_available], ["SOC 2 report", c.soc2], ["ISO/IEC 27001 certificate", c.iso27001], ["Regulated medical device", c.medical_device]].map(([a, b]) => h("tr", {}, h("td", { text: a }), h("td", { text: yn(b) }))))),
    h("div", { class: "callout" }, h("strong", { text: "Therefore: " }), "send only de-identified, non-sensitive inputs; run your own deployment inside your security boundary if you need stronger guarantees; do not use results to make individual patient-care decisions."),
    h("p", { class: "muted", text: "Operators: values above come from the running service (GET /v1/methodology). If you add logging, a database, or certifications, update that endpoint so this page stays true." }));
};

P.errors = () => h("div", {}, h("h1", { text: "Errors and limits" }),
  h("p", { class: "lead" }, "Errors use ", code("application/problem+json"), " (RFC 7807 style). They never include submitted values."),
  h("div", { class: "panel" }, h("pre", { text: JSON.stringify({ type: "about:blank", title: "Validation failed", status: 422, detail: "request body or parameters are invalid", request_id: "9f3c…", errors: [{ loc: ["body", "likelihood"], msg: "Input should be less than or equal to 1", type: "less_than_equal" }] }, null, 2) })),
  h("p", {}, "Quote the ", code("request_id"), " (also returned in the ", code("X-Request-ID"), " header) when reporting a problem. You may supply your own ", code("X-Request-ID"), " (8–64 characters)."),
  h("h2", { text: "Limits" }), h("table", { class: "kv" }, h("tbody", {}, [["Rows per cohort request or file", S.meth.limits.max_rows_per_request], ["Upload size (bytes)", S.meth.limits.max_upload_bytes]].map(([a, b]) => h("tr", {}, h("td", { text: a }), h("td", { class: "n", text: String(b) }))))),
  h("h2", { text: "Upload validation" }), h("p", { text: "Files are validated all-or-nothing. A 422 lists up to 20 problems as row and column numbers (data rows counted from 1, excluding the header). Extra columns are ignored and never returned." }));

P.changelog = () => h("div", {}, h("h1", { text: "Changelog" }),
  h("h3", { text: "v1 (library 3.3.0)" }),
  h("ul", { class: "clean" }, ["Versioned /v1 API with scoped, hashed API keys and per-key rate limits; fails closed when no keys are configured.", "Cohort scoring via JSON and CSV/Parquet upload, with strict row-level validation.", "FHIR R4 RiskAssessment and Bundle output.", "Problem-style errors that never echo submitted values; request ids on every response.", "This documentation portal, generated from the live OpenAPI schema."].map((x) => h("li", { text: x }))));

function notFound() { return h("div", {}, h("h1", { text: "Not found" }), h("p", {}, "Return to ", h("a", { href: "#/overview", text: "the overview" }), ".")); }
const tagsInOrder = () => { const t = (S.spec.tags || []).map((x) => x.name); const have = [...new Set(S.ops.map((o) => o.tag))]; return [...t.filter((x) => have.includes(x)), ...have.filter((x) => !t.includes(x))]; };

/* ---------------------------------------------------------------- nav, router, boot */
function buildNav() {
  const nav = $("#nav"); nav.replaceChildren();
  const link = (href, label, pre) => h("a", { href, "data-h": href }, pre ? h("span", { class: "m", text: pre }) : null, label);
  nav.append(h("h4", { text: "Guide" }), link("#/overview", "Overview"), link("#/authentication", "Authentication"), link("#/quickstart", "Quickstart"));
  nav.append(h("h4", { text: "API reference" }), link("#/reference", "All endpoints"));
  for (const t of tagsInOrder()) { nav.append(h("h4", { text: t })); S.ops.filter((o) => o.tag === t).forEach((o) => nav.append(link("#/op/" + o.slug, o.summary, o.method.toUpperCase()))); }
  nav.append(h("h4", { text: "Concepts" }), link("#/methodology", "Methodology"), link("#/fhir", "FHIR R4 output"), link("#/compliance", "Data handling & compliance"), link("#/errors", "Errors and limits"), link("#/schemas", "Schemas"), link("#/changelog", "Changelog"));
}
function route() {
  const hash = location.hash || "#/overview"; const m = hash.match(/^#\/([^/]+)(?:\/(.+))?$/);
  const name = m ? m[1] : "overview", arg = m && m[2];
  let node;
  try { node = name === "op" ? opPage(arg) : (P[name] ? P[name]() : notFound()); } catch (e) { node = h("div", {}, h("h1", { text: "Error" }), h("p", { text: "This page could not be rendered: " + e.message })); }
  const main = $("#main"); main.replaceChildren(node, h("footer", { class: "f", text: "RMTI API · engine rmti-py " + (S.meth ? S.meth.engine.version : "") + " · Apache-2.0 · research prototype" }));
  $("#nav").querySelectorAll("a").forEach((a) => a.removeAttribute("aria-current"));
  const cur = $("#nav").querySelector('a[data-h="' + hash + '"]'); if (cur) cur.setAttribute("aria-current", "page");
  main.querySelectorAll("table").forEach((t) => { const w = document.createElement("div"); w.className = "tw"; t.replaceWith(w); w.append(t); });
  window.scrollTo(0, 0); document.title = "RMTI API · " + (name === "op" ? ((S.ops.find((o) => o.slug === arg) || {}).summary || "Endpoint") : name);
}
async function health() {
  const el = $("#status");
  try { const r = await fetch(base() + "/v1/health"); const j = await r.json(); el.textContent = "operational · engine " + j.version + " · auth " + j.auth; el.className = "status ok"; }
  catch (_) { el.textContent = "unreachable at " + base(); el.className = "status bad"; }
}
async function boot() {
  S.base = /^https?:/.test(location.origin) ? location.origin : "http://127.0.0.1:8000";
  const b = $("#base"), k = $("#key"); b.value = S.base;
  b.addEventListener("change", () => { S.base = b.value.trim(); health(); route(); });
  k.addEventListener("input", () => { S.key = k.value.trim(); });
  try {
    const [spec, meth] = await Promise.all([fetch(base() + "/openapi.json").then((r) => r.json()), fetch(base() + "/v1/methodology").then((r) => r.json())]);
    S.spec = spec; S.meth = meth; S.ops = parseOps(spec);
  } catch (e) {
    $("#main").replaceChildren(h("h1", { text: "Cannot reach the API" }), h("p", {}, "Set the Base URL in the Connection panel to a running RMTI API (", code("rmti serve"), "). If this page is hosted separately, the API must allow its origin via RMTI_CORS_ORIGINS."));
    health(); return;
  }
  buildNav(); health(); route(); window.addEventListener("hashchange", route);
}
window.__RMTI_PORTAL__ = { S, boot };
if (document.readyState !== "loading") boot(); else document.addEventListener("DOMContentLoaded", boot);
