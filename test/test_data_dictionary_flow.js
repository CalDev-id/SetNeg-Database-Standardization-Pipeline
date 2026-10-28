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
    const classes = new Set();
    this.classList = {
      add(...names) { names.forEach((name) => classes.add(name)); },
      toggle(name, force) {
        if (force === true || (force === undefined && !classes.has(name))) classes.add(name);
        else classes.delete(name);
      },
      remove(...names) { names.forEach((name) => classes.delete(name)); },
      contains(name) { return classes.has(name); },
    };
  }
  append(child) { this.children.push(child); }
  insertCell() { const child = new Element(); this.append(child); return child; }
  replaceChildren(...children) { this.children = children; }
  addEventListener() {}
  setAttribute() {}
}

const html = fs.readFileSync("static/index.html", "utf8");
const script = fs.readFileSync("static/app.js", "utf8");
assert(html.indexOf('id="auditResultTab"') < html.indexOf('id="resultFindingCount"'),
  "tab hasil harus berada di atas ringkasan");
const auditCardEnd = html.indexOf('<section id="oldDictionaryResults"');
for (const id of ["nextDdlButton", "dictionaryProgressBar", "dictionaryElapsed"]) {
  assert(html.indexOf(`id="${id}"`) < auditCardEnd, `${id} harus berada di card Berkas audit`);
}
assert(html.indexOf('id="newDictionaryButton"') < auditCardEnd,
  "tombol retry Dictionary New harus terlihat di card progres, tidak tersembunyi di tab hasil");
assert.match(html, /id="newDictionaryButton"[^>]*>Coba Lagi<\/button>/);
assert.match(html, /<option value="nutaraline">Nutaraline · DeepSeek V4\.1 Flash 1017 LoRA<\/option>/);
assert.match(html, /id="dictionaryProcessLogToggle"[^>]*>i<\/button>/);
assert(html.indexOf('id="dictionaryStatusText"') < html.indexOf('id="dictionaryProcessLogToggle"')
  && html.indexOf('id="dictionaryProcessLogToggle"') < html.indexOf('id="dictionaryCurrentStageDuration"'),
"tombol info Data Dictionary harus di samping status proses");
assert.match(html, /id="auditProcessLogToggle"[^>]*>i<\/button>/);
assert.match(html, /id="auditRetryButton"[^>]*>Coba Lagi<\/button>/);
assert.match(html, /id="ddlProcessLogToggle"[^>]*>i<\/button>/);
assert(html.indexOf('id="statusText"') < html.indexOf('id="auditProcessLogToggle"')
  && html.indexOf('id="auditProcessLogToggle"') < html.indexOf('id="progressPercent"'),
"tombol info harus di samping status proses");
const progressMarkup = html.slice(html.indexOf('<section id="dictionaryProgressBox"'), auditCardEnd);
assert.equal((progressMarkup.match(/<progress\b/g) || []).length, 1, "Data Dictionary hanya memakai satu progress bar");
const auditProgressMarkup = html.slice(html.indexOf('<section id="progressBox"'), html.indexOf('<div id="completedActions"'));
assert.equal((auditProgressMarkup.match(/<progress\b/g) || []).length, 1,
  "Audit dan Normalisasi hanya memakai satu progress bar");
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
  ids.get("model").value = "gpt_setneg";
  const document = {
    getElementById(id) { assert(ids.has(id), id); return ids.get(id); },
    querySelector() { return new Element(); },
    querySelectorAll() { return []; },
    createElement() { return new Element(); },
    createDocumentFragment() { return new Element(); },
  };
  let classificationStatus = first === "old" ? "running" : "completed";
  let oldStatus = first === "old" ? "completed" : "running";
  let normalizationStatus = "failed";
  let auditStatus = "failed";
  let normalizationPostCount = 0;
  let now = 0;
  let nextTimer = 0;
  const timers = new Map();
  const calls = [];
  const storage = new Map();
  let normalizationId = "c".repeat(32);
  let normalStatusUrl = `/api/v1/normalization/${normalizationId}`;
  async function fetch(url, options = {}) {
    calls.push([url, options.method || "GET", options.body]);
    let body;
    if (url === "/api/v1/normalization" && options.method === "POST") {
      normalizationPostCount += 1;
      normalizationId = (normalizationPostCount === 1 ? "a" : "b").repeat(32);
      normalStatusUrl = `/api/v1/normalization/${normalizationId}`;
      body = { job_id: normalizationId, status_url: normalStatusUrl };
    } else if (url === "/api/v1/audit/spreadsheet/audit/retry" && options.method === "POST") {
      auditStatus = "running";
      body = { job_id: "audit", status_url: "/api/v1/audit/spreadsheet/audit",
        completed_batches: 1, total_batches: 2 };
    } else if (url === "/api/v1/audit/spreadsheet/audit") body = {
      job_id: "audit", source_filename: "schema.sql", status: auditStatus,
      completed_batches: 1, total_batches: 2, elapsed_seconds: 10,
      retry_available: auditStatus === "failed", process_events: [],
    };
    else if (url === normalStatusUrl) body = { job_id: normalizationId, audit_job_id: "audit", status: normalizationStatus,
      total_batches: 1, completed_batches: 1, elapsed_seconds: 2,
      findings_url: "/normal/findings", download_url: "/normal/download", error: "LLM gagal",
      process_events: [
        { stage: "audit", kind: "started", elapsed_seconds: 0, message: "Audit batch 1/2 dimulai." },
        { stage: "audit", kind: "retry", elapsed_seconds: 1, message: "Audit batch 1/2: timeout GPT Setneg; dipecah menjadi 2 bagian." },
        { stage: "audit", kind: "retry", elapsed_seconds: 2, message: "Audit batch 1/2: respons tidak valid; dipecah menjadi 2 bagian." },
        { stage: "normalization", kind: "started", elapsed_seconds: 0, message: "Normalisasi dimulai." },
        { stage: "normalization", kind: "failed", elapsed_seconds: 2, message: "Normalisasi gagal: layanan tidak tersedia." },
      ] };
    else if (url === "/api/v1/audit/spreadsheet/audit/combined-findings") body = {
      summary: { table_count: 1, column_count: 1 },
      findings: [
        { no: 1, nama_database: "db", nama_tabel: "thing", objek_temuan: "Audit", aturan_playbook: "1a",
          uraian_ketidaksesuaian: "Perlu perbaikan", solusi: "Perbaiki", status: "To Do", catatan: "-", jenis_temuan: "Audit Playbook" },
        { no: 2, nama_database: "db", nama_tabel: "thing", objek_temuan: "Audit lain", aturan_playbook: "1b",
          uraian_ketidaksesuaian: "Perlu perubahan", solusi: "Perbaiki", status: "To Do", catatan: "-", jenis_temuan: "Audit Playbook" },
        { no: 3, nama_database: "db", nama_tabel: "thing", objek_temuan: "Normalisasi", aturan_playbook: "Normalisasi Database (3NF)",
          uraian_ketidaksesuaian: "Kolom terdampak: `id`", solusi: "Hapus kolom duplikat", status: "To Do", catatan: "-", jenis_temuan: "Normalisasi" },
      ],
    };
    else if (url === "/normal/findings") body = {
      summary: { table_count: 1, column_count: 1 },
      display_findings: [{ no: 1, nama_database: "db", nama_tabel: "thing",
        objek_temuan: "Normalisasi", aturan_playbook: "Normalisasi Database (3NF)",
        uraian_ketidaksesuaian: "Kolom terdampak: `id`", solusi: "Hapus kolom duplikat",
        status: "To Do", catatan: "-", jenis_temuan: "Normalisasi" }],
    };
    else if (url.endsWith("/classification") && options.method === "POST") body = { job_id: "classification", status_url: "/classification" };
    else if (url.endsWith("/old-dictionary") && options.method === "POST") body = { job_id: "old", status_url: "/old" };
    else if (url.endsWith("/new-dictionary") && options.method === "POST") body = { job_id: "new", status_url: "/new" };
    else if (url.endsWith("/log-perubahan") && options.method === "POST") body = { job_id: "log", status_url: "/log" };
    else if (url === "/api/v1/ddl-standard" && options.method === "POST") body = { job_id: "ddl", status_url: "/ddl" };
    else if (url === "/classification") body = { status: classificationStatus, total_tables: 1, completed_tables: 0 };
    else if (url === "/old") body = { status: oldStatus, result: oldResult, total_objects: 1, completed_objects: 0 };
    else if (url === "/new") body = { status: "completed", result: newResult };
    else if (url === "/log") body = { status: "completed", result: logResult };
    else if (url === "/ddl") body = { status: "completed", elapsed_seconds: 8,
      process_events: [
        { kind: "started", step: "create", elapsed_seconds: 0, message: "DDL CREATE dimulai." },
        { kind: "retry", step: "create", elapsed_seconds: 2, message: "Respons tidak valid" },
        { kind: "completed", step: "create", elapsed_seconds: 3, message: "DDL CREATE selesai." },
        { kind: "started", step: "alter", elapsed_seconds: 3, message: "DDL ALTER dimulai." },
        { kind: "completed", step: "alter", elapsed_seconds: 8, message: "DDL ALTER selesai." },
      ],
      result: { ddl_alter: "ALTER TABLE `thing` ADD COLUMN `new` INT;", ddl_create: "CREATE TABLE `thing` (`id` INT);" } };
    else throw new Error(`Unexpected request: ${url}`);
    return { ok: true, json: async () => body };
  }
  const context = vm.createContext({ document, fetch, URLSearchParams, location: { search: "" },
    Date: { now() { return now; } },
    setInterval(callback) { const id = ++nextTimer; timers.set(id, callback); return id; },
    clearInterval(id) { timers.delete(id); },
    sessionStorage: { setItem(key, value) { storage.set(key, value); },
      removeItem(key) { storage.delete(key); }, getItem(key) { return storage.get(key) || null; } }, setTimeout() {} });
  vm.runInContext(script, context);
  vm.runInContext("state.nextProcessInputs={ddlFile:{name:'schema.sql'},findingsFile:{name:'temuan_standardisasi.xlsx'}}", context);
  async function flush() { for (let i = 0; i < 30; i++) await Promise.resolve(); }
  await vm.runInContext("selectFeature('dictionary')", context);
  assert.equal(ids.get("dictionaryInputs").hidden, true);
  vm.runInContext("showProcessing(); updateProgress({status:'running',completed_batches:0,total_batches:2,elapsed_seconds:0})", context);
  vm.runInContext(`observeAuditJob({job_id:'audit',source_filename:'schema.sql',normalization_job_id:'${normalizationId}',normalization_status_url:'${normalStatusUrl}'})`, context);
  await flush();
  assert.equal(normalizationPostCount, 0, "job Normalisasi dibuat bersama Audit, bukan POST kedua dari UI");
  assert.equal(timers.size, 1, "Audit dan Normalisasi berbagi satu penghitung waktu");
  await vm.runInContext("selectFeature('audit')", context);
  assert.equal(ids.get("normalizationInputs").hidden, false, "Normalisasi bisa dipantau saat Audit berjalan");
  assert.equal(ids.get("progressPercent").textContent, "0%");
  assert.equal(vm.runInContext("state.normalizationReady", context), false);
  assert.match(ids.get("normalizationError").textContent, /LLM gagal/);
  assert.equal(ids.get("statusText").textContent, "Audit 1/2 · Normalisasi gagal");
  vm.runInContext("toggleAuditProcessLog()", context);
  assert.equal(ids.get("auditProcessLog").hidden, false);
  const auditRows = ids.get("auditProcessLog").children[0].children;
  assert.equal(auditRows.length, 4, "log menggabungkan awal dan akhir proses menjadi satu baris");
  assert.match(auditRows[0].textContent, /Audit batch 1\/2/);
  assert.match(auditRows[1].textContent, /mengulang/);
  assert.match(auditRows[1].textContent, /timeout GPT Setneg/);
  assert.match(auditRows[2].textContent, /respons tidak valid/);
  assert.match(auditRows[3].textContent, /00:02 · Normalisasi gagal/);
  assert.equal(ids.get("normalizationStartButton").hidden, false);
  const auditFinishesFirst = first === "old";
  if (auditFinishesFirst) {
    vm.runInContext("updateProgress({status:'completed',completed_batches:2,total_batches:2,elapsed_seconds:3}); finishAudit({job_id:'audit',source_filename:'schema.sql'})", context);
    assert.equal(ids.get("progressPercent").textContent, "67%");
    assert.equal(ids.get("progressBox").classList.contains("is-complete"), false);
    assert.equal(ids.get("downloadLink").hidden, true);
  }
  normalizationStatus = "completed";
  await vm.runInContext("startNormalization()", context);
  await flush();
  assert.equal(vm.runInContext("state.normalizationReady", context), true);
  assert.equal(ids.get("progressPercent").textContent, auditFinishesFirst ? "100%" : "33%");
  assert.equal(ids.get("progressBox").classList.contains("is-complete"), auditFinishesFirst);
  assert.equal(ids.get("downloadLink").hidden, !auditFinishesFirst,
    "Unduhan gabungan menunggu Audit dan Normalisasi selesai");
  if (!auditFinishesFirst) {
    assert.equal(ids.get("auditResults").hidden, false, "hasil Normalisasi terlihat saat Audit berjalan");
    assert.equal(ids.get("normalizationResults").hidden, false);
    assert.equal(ids.get("normalizationFindingCount").textContent, 1);
    assert.equal(ids.get("auditFindingCount").textContent, 0);
    assert.equal(ids.get("noFindings").textContent, "Hasil Audit Playbook belum tersedia.");
    assert.equal(ids.get("nextProcessButton").hidden, true);
  }
  vm.runInContext("clearAuditResults(); clearNormalization(); state.normalizationTrackingUrl=null; restoreNormalization()", context);
  await flush();
  assert.equal(vm.runInContext("state.normalizationReady", context), true);
  if (!auditFinishesFirst) {
    vm.runInContext("updateProgress({status:'running',completed_batches:1,total_batches:2,elapsed_seconds:1})", context);
    assert.equal(ids.get("progressPercent").textContent, "67%");
    vm.runInContext("updateProgress({status:'completed',completed_batches:2,total_batches:2,elapsed_seconds:3}); finishAudit({job_id:'audit',source_filename:'schema.sql'})", context);
  }
  await flush();
  assert.equal(ids.get("progressPercent").textContent, "100%");
  assert.equal(ids.get("progressBox").classList.contains("is-complete"), true);
  assert.equal(ids.get("completionMeta").hidden, false);
  assert.equal(timers.size, 0, "penghitung waktu berhenti setelah keduanya selesai");
  assert.equal(ids.get("downloadLink").href, "/api/v1/audit/spreadsheet/audit/download/combined");
  assert.equal(ids.get("downloadLink").hidden, false);
  assert.equal(ids.get("nextProcessButton").hidden, false);
  assert.equal(ids.get("auditFindingCount").textContent, 2);
  assert.equal(ids.get("normalizationFindingCount").textContent, 1);
  assert.equal(ids.get("resultFindingCount").textContent, auditFinishesFirst ? 2 : 1);
  assert.equal(ids.get("resultFindingLabel").textContent,
    auditFinishesFirst ? "Temuan Audit Playbook" : "Temuan Normalisasi");
  assert.equal(ids.get("findingsBody").children[0].children.length, 2);
  assert.equal(ids.get("normalizationBody").children[0].children.length, 1);
  assert.equal(ids.get("normalizationBody").children[0].children[0].children.length, 10);
  vm.runInContext("selectResultSheet('normalization')", context);
  assert.equal(ids.get("auditResultPanel").hidden, true);
  assert.equal(ids.get("normalizationResults").hidden, false);
  assert.equal(ids.get("resultFindingCount").textContent, 1);
  assert.equal(ids.get("resultFindingLabel").textContent, "Temuan Normalisasi");
  assert.equal(vm.runInContext("renderFinding({jenis_temuan:'Normalisasi',solusi:'Hapus kolom'}).classList.contains('is-removal')", context), true);
  assert.equal(vm.runInContext("renderFinding({jenis_temuan:'Audit Playbook',solusi:'Hapus kolom'}).classList.contains('is-removal')", context), true);
  await vm.runInContext("selectFeature('dictionary')", context);
  assert.equal(ids.get("dictionaryInputs").hidden, false);
  await vm.runInContext("startClassification()", context);
  await flush();
  const classificationPost = calls.find(([url, method]) => url.endsWith("/classification") && method === "POST");
  assert.equal(JSON.parse(classificationPost[2]).normalization_job_id, "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa");
  assert.equal(JSON.parse(classificationPost[2]).model, undefined,
    "Klasifikasi tidak mengikuti pilihan model pengguna");
  const oldDictionaryPost = calls.find(([url, method]) => url.endsWith("/old-dictionary") && method === "POST");
  assert.equal(JSON.parse(oldDictionaryPost[2]).model, "gpt_setneg",
    "Proses Dictionary lain tetap memakai model pilihan pengguna");
  assert.equal(ids.get("dictionaryProgressBox").hidden, false);
  assert.match(ids.get("dictionaryStatusText").textContent, /Tahap [12]\/3/);
  now = 2000;
  for (const tick of timers.values()) tick();
  assert.equal(ids.get("dictionaryElapsed").textContent, "00:02");
  vm.runInContext("toggleDictionaryProcessLog()", context);
  assert(ids.get("dictionaryProcessLog").children[0].children.some((row) => /00:02 ·/.test(row.textContent)),
    "durasi tahap Data Dictionary yang aktif harus terus berjalan");
  vm.runInContext("toggleDictionaryProcessLog()", context);
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
    assert.match(ids.get("dictionaryStatusText").textContent, /Dictionary New · Tahap 2\/3/);
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
  vm.runInContext("toggleDictionaryProcessLog()", context);
  assert.equal(ids.get("dictionaryProcessLog").hidden, false);
  assert(ids.get("dictionaryProcessLog").children[0].children.length >= 4);
  assert.match(ids.get("dictionaryProcessLog").children[0].children.at(-1).textContent, /Log Perubahan selesai/);
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
  vm.runInContext("toggleDdlProcessLog()", context);
  const ddlRows = ids.get("ddlProcessLog").children[0].children;
  assert.equal(ddlRows.length, 3);
  assert.match(ddlRows[0].textContent, /00:03 · DDL CREATE selesai/);
  assert.match(ddlRows[1].textContent, /Mengulang DDL CREATE/);
  assert.match(ddlRows[2].textContent, /00:05 · DDL ALTER selesai/);
  assert.equal(ids.get("ddlAlterPreview").textContent, "ALTER TABLE `thing` ADD COLUMN `new` INT;");
  assert.equal(ids.get("ddlCreateDownload").href, "/api/v1/ddl-standard/ddl/download/create");
  vm.runInContext("state.ddlProcessEvents=[{kind:'started',step:'create',elapsed_seconds:0,message:'DDL CREATE dimulai.'}]; startDdlElapsed(0)", context);
  now = 4000;
  for (const tick of timers.values()) tick();
  assert.match(ids.get("ddlProcessLog").children[0].children[0].textContent, /00:02 · DDL CREATE/);
  vm.runInContext("stopDdlElapsed()", context);
  vm.runInContext("state.auditEvents=[{stage:'audit',kind:'started',elapsed_seconds:0,message:'Audit batch 1/2 dimulai.'}]; startElapsed(0)", context);
  now = 6000;
  for (const tick of timers.values()) tick();
  assert.match(ids.get("auditProcessLog").children[0].children[0].textContent, /00:02 · Audit batch 1\/2/);
  vm.runInContext("stopElapsed()", context);
  await vm.runInContext("selectDdlSheet('create')", context);
  assert.equal(ids.get("ddlAlterPanel").hidden, true);
  assert.equal(ids.get("ddlCreatePanel").hidden, false);
  storage.set("auditDatabaseStatusUrl", "/api/v1/audit/spreadsheet/audit");
  await vm.runInContext("checkStatus('/api/v1/audit/spreadsheet/audit')", context);
  assert.equal(ids.get("auditRetryButton").hidden, false);
  assert.equal(storage.get("auditDatabaseStatusUrl"), "/api/v1/audit/spreadsheet/audit",
    "job Audit yang gagal tetap dapat dipulihkan setelah refresh biasa");
  await vm.runInContext("retryAudit()", context);
  await flush();
  assert.equal(calls.filter(([url, method]) => url === "/api/v1/audit/spreadsheet/audit/retry"
    && method === "POST").length, 1);
  assert.equal(ids.get("auditRetryButton").hidden, true);
  assert.equal(vm.runInContext("state.auditProgress.status", context), "running");
  console.log(`OK: ${first} selesai lebih dulu`);
}

async function reloadScenario(mode, selectedModel = "gpt_setneg") {
  const jobIds = Object.fromEntries(["audit", "normal", "classification", "old", "new", "log", "ddl"]
    .map((name, index) => [name, String(index + 1).repeat(32)]));
  const storage = new Map([
    ["auditDatabaseCompletedStatusUrl", `/api/v1/audit/spreadsheet/${jobIds.audit}`],
    ["normalizationStatusUrl", `/api/v1/normalization/${jobIds.normal}`],
    ["databaseWorkflowSession", JSON.stringify({
      auditJobId: jobIds.audit, model: selectedModel,
      feature: mode === "running" || mode === "failed" ? "dictionary" : "ddl",
      classificationJobId: jobIds.classification, oldDictionaryJobId: jobIds.old,
      newDictionaryJobId: jobIds.new,
      logPerubahanJobId: mode === "running" || mode === "failed" ? null : jobIds.log,
      ddlJobId: mode === "running" || mode === "failed" ? null : jobIds.ddl,
    })],
  ]);
  const elements = new Map([...html.matchAll(/<[^>]*\bid="([^"]+)"[^>]*>/g)].map((match) => {
    const element = new Element();
    element.hidden = /\shidden(?:\s|>)/.test(match[0]);
    element.disabled = /\sdisabled(?:\s|>)/.test(match[0]);
    return [match[1], element];
  }));
  elements.get("model").value = "telkom";
  const document = {
    getElementById(id) { assert(elements.has(id), id); return elements.get(id); },
    querySelector() { return new Element(); },
    querySelectorAll() { return []; },
    createElement() { return new Element(); },
    createDocumentFragment() { return new Element(); },
  };
  const calls = [];
  let newStatus = mode === "running" || mode === "failed" ? mode : "completed";
  let rejectedRetries = mode === "failed" ? 1 : 0;
  async function fetch(url, options = {}) {
    const method = options.method || "GET";
    calls.push([url, method, options.body]);
    let body;
    if (url === `/api/v1/audit/spreadsheet/${jobIds.audit}`) body = {
      job_id: jobIds.audit, source_filename: "schema.sql", status: "completed",
      completed_batches: 1, total_batches: 1, elapsed_seconds: 4,
      normalization_job_id: jobIds.normal,
      normalization_status_url: `/api/v1/normalization/${jobIds.normal}`,
    };
    else if (url === `/api/v1/normalization/${jobIds.normal}`) body = {
      job_id: jobIds.normal, audit_job_id: jobIds.audit, status: "completed",
    };
    else if (url.endsWith("/combined-findings")) body = {
      summary: { table_count: 1, column_count: 1 }, findings: [],
    };
    else if (url === `/api/v1/data-dictionary/classification/${jobIds.classification}`) body = {
      status: "completed", completed_tables: 1, total_tables: 1,
    };
    else if (url === `/api/v1/data-dictionary/old-dictionary/${jobIds.old}`) body = {
      status: "completed", result: oldResult, completed_objects: 1, total_objects: 1,
    };
    else if (url === `/api/v1/data-dictionary/new-dictionary/${jobIds.new}`) body = {
      status: newStatus, result: newStatus === "completed" ? newResult : null,
      completed_batches: newStatus === "completed" ? 2 : 1, total_batches: 2,
      saved_batches: newStatus === "failed" ? 1 : 0,
      error: newStatus === "failed" ? "Nama kolom berulang" : null,
    };
    else if (url === "/api/v1/data-dictionary/new-dictionary" && method === "POST") {
      if (rejectedRetries) {
        rejectedRetries -= 1;
        return { ok: false, status: 503, json: async () => ({ detail: "Layanan LLM sedang bermasalah." }) };
      }
      body = { job_id: jobIds.new,
        status_url: `/api/v1/data-dictionary/new-dictionary/${jobIds.new}` };
    }
    else if (url === "/api/v1/data-dictionary/log-perubahan" && method === "POST") body = {
      job_id: jobIds.log, status_url: `/api/v1/data-dictionary/log-perubahan/${jobIds.log}`,
    };
    else if (url === `/api/v1/data-dictionary/log-perubahan/${jobIds.log}`) body = {
      status: "completed", result: logResult, completed_batches: 1, total_batches: 1,
    };
    else if (url === `/api/v1/ddl-standard/${jobIds.ddl}`) body = {
      status: "completed", elapsed_seconds: 8,
      result: { ddl_alter: "ALTER TABLE `thing` ADD COLUMN `new` INT;",
        ddl_create: "CREATE TABLE `thing` (`id` INT);" },
    };
    else throw new Error(`Unexpected request: ${url}`);
    return { ok: true, json: async () => body };
  }
  const context = vm.createContext({
    document, fetch, URLSearchParams, location: { search: "", pathname: "/" },
    __resetWorkflowOnLoad: mode === "hard",
    Date: { now() { return 0; } },
    setInterval() { return 1; }, clearInterval() {}, setTimeout() {},
    sessionStorage: {
      setItem(key, value) { storage.set(key, value); },
      removeItem(key) { storage.delete(key); },
      getItem(key) { return storage.get(key) || null; },
    },
  });
  vm.runInContext(script, context);
  for (let i = 0; i < 80; i++) await Promise.resolve();

  if (mode === "hard") {
    assert.equal(calls.length, 0, "force refresh tidak memulihkan atau memulai job");
    assert.equal(storage.has("databaseWorkflowSession"), false);
    assert.equal(storage.has("auditDatabaseCompletedStatusUrl"), false);
    assert.equal(elements.get("auditWorkspace").hidden, false);
    return;
  }

  assert.equal(elements.get("model").value, selectedModel);
  assert.equal(vm.runInContext("state.oldDictionaryReady", context), true);
  assert.equal(vm.runInContext("state.classificationReady", context), true);
  assert.equal(vm.runInContext("state.activeFeature", context),
    mode === "running" || mode === "failed" ? "dictionary" : "ddl");
  assert.equal(calls.some(([, method]) => method === "POST"), false,
    "refresh biasa hanya mengambil status, tidak meminta LLM mengulang");
  if (mode === "running") {
    assert.equal(vm.runInContext("state.newDictionaryReady", context), false);
    assert.equal(elements.get("dictionaryProgressPercent").textContent, "63%");
    newStatus = "completed";
    await vm.runInContext(`pollNewDictionary('/api/v1/data-dictionary/new-dictionary/${jobIds.new}', state.newDictionaryRequestId)`, context);
    for (let i = 0; i < 40; i++) await Promise.resolve();
    assert.equal(calls.filter(([url, method]) => url === "/api/v1/data-dictionary/log-perubahan" && method === "POST").length, 1);
    assert.equal(elements.get("dictionaryProgressPercent").textContent, "100%");
  } else if (mode === "failed") {
    assert.equal(vm.runInContext("state.newDictionaryReady", context), false);
    assert.equal(elements.get("dictionaryProgressPercent").textContent, "63%");
    assert.equal(elements.get("dictionaryStatusText").textContent, "Dictionary New gagal.");
    assert.doesNotMatch(elements.get("dictionaryStatusText").textContent, /Nama kolom berulang/);
    assert.equal(elements.get("newDictionaryButton").hidden, false);
    assert.equal(elements.get("newDictionaryButton").textContent, "Coba Lagi");
    assert.match(elements.get("dictionaryProcessHint").textContent, /1 batch tersimpan/);
    vm.runInContext("failDictionaryStage('new', 'Failed to fetch')", context);
    assert.equal(elements.get("dictionaryStatusText").textContent, "Dictionary New gagal.");
    newStatus = "completed";
    await vm.runInContext("startNewDictionary()", context);
    for (let i = 0; i < 40; i++) await Promise.resolve();
    assert.equal(vm.runInContext("state.dictionaryStages.new.total", context), 2,
      "POST retry yang gagal tidak boleh mengubah progres menjadi 1/1");
    assert.equal(vm.runInContext("state.newDictionaryRetryJobId", context), jobIds.new,
      "checkpoint tetap dipakai saat POST retry gagal");
    assert(elements.get("dictionaryProcessLog").children[0].children.some((row) =>
      /Dictionary New 2\/2 batch gagal: Layanan LLM sedang bermasalah/.test(row.textContent)));
    await vm.runInContext("startNewDictionary()", context);
    for (let i = 0; i < 40; i++) await Promise.resolve();
    const retries = calls.filter(([url, method]) => url === "/api/v1/data-dictionary/new-dictionary" && method === "POST");
    assert.equal(retries.length, 2);
    assert.equal(JSON.parse(retries[0][2]).retry_job_id, jobIds.new);
    assert.equal(calls.filter(([url, method]) => url.endsWith("/classification") && method === "POST").length, 0);
    assert.equal(calls.filter(([url, method]) => url.endsWith("/old-dictionary") && method === "POST").length, 0);
    assert.equal(vm.runInContext("state.newDictionaryReady", context), true);
  } else {
    assert.equal(vm.runInContext("state.newDictionaryReady", context), true);
    assert.equal(elements.get("dictionaryProgressPercent").textContent, "100%");
    assert.equal(elements.get("ddlAlterPreview").textContent, "ALTER TABLE `thing` ADD COLUMN `new` INT;");
    assert.equal(elements.get("ddlWorkspace").hidden, false);
    vm.runInContext(`state.dictionaryEvents = [
      {stage:'old',kind:'started',completed:0,total:2,elapsedSeconds:0},
      {stage:'old',kind:'progress',completed:1,total:2,elapsedSeconds:12},
      {stage:'old',kind:'completed',completed:2,total:2,elapsedSeconds:20},
      {stage:'new',kind:'started',completed:0,total:62,elapsedSeconds:0},
      {stage:'new',kind:'progress',completed:49,total:62,elapsedSeconds:2400},
      {stage:'new',kind:'failed',completed:49,total:62,elapsedSeconds:2488,
        message:'Dictionary New batch 50/62 gagal: Layanan LLM sedang bermasalah.'},
      {stage:'log',kind:'started',completed:0,total:2,elapsedSeconds:0},
      {stage:'log',kind:'progress',completed:1,total:2,elapsedSeconds:5},
      {stage:'log',kind:'completed',completed:2,total:2,elapsedSeconds:9}
    ]; renderDictionaryProcessLog();`, context);
    const logRows = elements.get("dictionaryProcessLog").children[0].children.map((row) => row.textContent).join("\n");
    assert.match(logRows, /Dictionary Old 1\/2 objek selesai/);
    assert.match(logRows, /Dictionary New 49\/62 batch selesai/);
    assert.match(logRows, /Dictionary New 50\/62 batch gagal: Layanan LLM sedang bermasalah/);
    assert.match(logRows, /Log Perubahan 1\/2 batch selesai/);
  }
}

(async () => {
  await scenario("old");
  await scenario("new");
  await reloadScenario("running");
  await reloadScenario("failed");
  await reloadScenario("completed");
  await reloadScenario("completed", "nutaraline");
  await reloadScenario("hard");
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
