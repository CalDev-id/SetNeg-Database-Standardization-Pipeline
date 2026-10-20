const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

class Element {
  constructor() {
    this.children = [];
    this.hidden = false;
    this.disabled = false;
    this.textContent = "";
    this.firstChild = { textContent: "" };
    this.classList = { add() {}, toggle() {}, remove() {} };
  }
  append(child) { this.children.push(child); }
  insertCell() { const child = new Element(); this.append(child); return child; }
  replaceChildren(...children) { this.children = children; }
  addEventListener() {}
  setAttribute() {}
}

const html = fs.readFileSync("static/index.html", "utf8");
const script = fs.readFileSync("static/app.js", "utf8");
const auditCardEnd = html.indexOf('<section id="oldDictionaryResults"');
for (const id of ["nextDdlButton", "dictionaryProgressBar", "dictionaryElapsed"]) {
  assert(html.indexOf(`id="${id}"`) < auditCardEnd, `${id} harus berada di card Berkas audit`);
}
const progressMarkup = html.slice(html.indexOf('<section id="dictionaryProgressBox"'), auditCardEnd);
assert.equal((progressMarkup.match(/<progress\b/g) || []).length, 1, "Data Dictionary hanya memakai satu progress bar");
const oldResult = { thing: { jenis_tabel: "Transaksi/relasi", deskripsi_tabel: "Tabel", kolom: { id: { tipe_data: "INT" } } } };
const newResult = { thing: { jenis_tabel: "Transaksi/relasi", deskripsi_tabel: "Tabel", kolom_baru: [
  { no_kolom: 1, nama_kolom: "id", tipe_data: "INT", log: { no_lama: 1 } },
] } };
const logResult = { log_perubahan: [
  { no_baru: 1, no_lama: 1, jenis_perubahan: "Dipertahankan", nama_tabel: "thing",
    objek_temuan: "-", aturan_playbook: "-", posisi_sisipan: null, uraian_baru: null },
] };

async function scenario(first) {
  const ids = new Map([...html.matchAll(/<[^>]*\bid="([^"]+)"[^>]*>/g)].map((match) => {
    const element = new Element();
    element.hidden = /\shidden(?:\s|>)/.test(match[0]);
    element.disabled = /\sdisabled(?:\s|>)/.test(match[0]);
    return [match[1], element];
  }));
  const document = {
    getElementById(id) { assert(ids.has(id), id); return ids.get(id); },
    querySelector() { return new Element(); },
    querySelectorAll() { return []; },
    createElement() { return new Element(); },
    createDocumentFragment() { return new Element(); },
  };
  let classificationStatus = first === "old" ? "running" : "completed";
  let oldStatus = first === "old" ? "completed" : "running";
  let now = 0;
  let nextTimer = 0;
  const timers = new Map();
  const calls = [];
  async function fetch(url, options = {}) {
    calls.push([url, options.method || "GET"]);
    let body;
    if (url.endsWith("/classification") && options.method === "POST") body = { job_id: "classification", status_url: "/classification" };
    else if (url.endsWith("/old-dictionary") && options.method === "POST") body = { job_id: "old", status_url: "/old" };
    else if (url.endsWith("/new-dictionary") && options.method === "POST") body = { job_id: "new", status_url: "/new" };
    else if (url.endsWith("/log-perubahan") && options.method === "POST") body = { job_id: "log", status_url: "/log" };
    else if (url === "/api/v1/ddl-standard" && options.method === "POST") body = { job_id: "ddl", status_url: "/ddl" };
    else if (url === "/classification") body = { status: classificationStatus, total_tables: 1, completed_tables: 0 };
    else if (url === "/old") body = { status: oldStatus, result: oldResult, total_objects: 1, completed_objects: 0 };
    else if (url === "/new") body = { status: "completed", result: newResult };
    else if (url === "/log") body = { status: "completed", result: logResult };
    else if (url === "/ddl") body = { status: "completed", elapsed_seconds: 8,
      result: { ddl_alter: "ALTER TABLE `thing` ADD COLUMN `new` INT;", ddl_create: "CREATE TABLE `thing` (`id` INT);" } };
    else throw new Error(`Unexpected request: ${url}`);
    return { ok: true, json: async () => body };
  }
  const context = vm.createContext({ document, fetch, URLSearchParams, location: { search: "" },
    Date: { now() { return now; } },
    setInterval(callback) { const id = ++nextTimer; timers.set(id, callback); return id; },
    clearInterval(id) { timers.delete(id); },
    sessionStorage: { removeItem() {}, getItem() { return null; } }, setTimeout() {} });
  vm.runInContext(script, context);
  vm.runInContext("state.handoff={auditJobId:'audit',sourceFilename:'schema.sql'}", context);
  async function flush() { for (let i = 0; i < 30; i++) await Promise.resolve(); }
  await vm.runInContext("startClassification()", context);
  await flush();
  assert.equal(ids.get("dictionaryProgressBox").hidden, false);
  assert.match(ids.get("dictionaryStatusText").textContent, /Tahap [12]\/3/);
  now = 2000;
  for (const tick of timers.values()) tick();
  assert.equal(ids.get("dictionaryElapsed").textContent, "00:02");
  assert(calls.some(([url, method]) => url.endsWith("/classification") && method === "POST"));
  assert(calls.some(([url, method]) => url.endsWith("/old-dictionary") && method === "POST"));

  if (first === "old") {
    assert.equal(ids.get("oldDictionaryResults").hidden, false);
    assert.equal(ids.get("dictionaryNewTable").hidden, true);
    assert.match(ids.get("dictionaryStatusText").textContent, /Tahap 1\/3/);
    assert.equal(ids.get("dictionaryProgressPercent").textContent, "25%");
    assert(!calls.some(([url, method]) => url.endsWith("/new-dictionary") && method === "POST"));
    classificationStatus = "completed";
    await vm.runInContext("pollClassification('/classification',state.classificationRequestId)", context);
    await flush();
  } else {
    assert.equal(ids.get("oldDictionaryResults").hidden, false);
    assert.equal(ids.get("dictionaryNewTable").hidden, false);
    assert.equal(ids.get("oldDictionaryTable").hidden, true);
    assert.equal(ids.get("oldDictionaryPending").hidden, false);
    assert.match(ids.get("dictionaryStatusText").textContent, /Tahap 2\/3 · Menyusun Dictionary Baru/);
    assert.equal(ids.get("dictionaryProgressPercent").textContent, "50%");
    assert(!calls.some(([url, method]) => url.endsWith("/log-perubahan") && method === "POST"));
    oldStatus = "completed";
    await vm.runInContext("pollOldDictionary('/old',state.oldDictionaryRequestId)", context);
    await flush();
  }
  assert.equal(ids.get("dictionaryNewTable").hidden, false);
  assert.equal(ids.get("oldDictionaryTable").hidden, false);
  assert.equal(ids.get("dictionaryLogTable").hidden, false,
    `${first} first: ${JSON.stringify(calls)} state=${vm.runInContext("JSON.stringify({old:state.oldDictionaryReady,new:state.newDictionaryReady,log:state.logPerubahanRequested})", context)}`);
  assert.equal(ids.get("dictionaryProgressPercent").textContent, "100%");
  assert.equal(ids.get("dictionaryProgressBar").value, 100);
  assert.match(ids.get("dictionaryStatusText").textContent, /Data Dictionary selesai/);
  assert.equal(ids.get("dictionaryTimeLabel").textContent, "Durasi proses");
  assert.equal(timers.size, 0);
  assert.equal(calls.filter(([url, method]) => url.endsWith("/log-perubahan") && method === "POST").length, 1);
  assert.equal(ids.get("dictionaryLogBody").children[0].children[0].children.length, 8);
  assert.equal(ids.get("nextDdlButton").hidden, false);
  assert.equal(ids.get("dictionaryElapsed").textContent, "00:02");
  await vm.runInContext("selectFeature('ddl')", context);
  assert.equal(ids.get("ddlInputs").hidden, false);
  assert.equal(ids.get("ddlSourceName").textContent, "schema.sql");
  await vm.runInContext("startDdlStandard()", context);
  await flush();
  assert.equal(ids.get("ddlResults").hidden, false);
  assert.equal(ids.get("ddlDownloadActions").hidden, false);
  assert.equal(ids.get("ddlProgressBox").hidden, false);
  assert.equal(ids.get("ddlTimeLabel").textContent, "Durasi proses");
  assert.equal(ids.get("ddlAlterPreview").textContent, "ALTER TABLE `thing` ADD COLUMN `new` INT;");
  assert.equal(ids.get("ddlCreateDownload").href, "/api/v1/ddl-standard/ddl/download/create");
  await vm.runInContext("selectDdlSheet('create')", context);
  assert.equal(ids.get("ddlAlterPanel").hidden, true);
  assert.equal(ids.get("ddlCreatePanel").hidden, false);
  console.log(`OK: ${first} selesai lebih dulu`);
}

(async () => { await scenario("old"); await scenario("new"); })().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
