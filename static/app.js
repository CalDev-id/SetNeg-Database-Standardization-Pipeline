const elements = {
  form: document.getElementById("uploadForm"),
  fileInput: document.getElementById("file"),
  modelSelect: document.getElementById("model"),
  fileName: document.getElementById("fileName"),
  filePrompt: document.getElementById("filePrompt"),
  fileAction: document.getElementById("fileAction"),
  uploadArea: document.querySelector(".upload-area"),
  submitButton: document.getElementById("submitButton"),
  nextProcessButton: document.getElementById("nextProcessButton"),
  progressBox: document.getElementById("progressBox"),
  progressBar: document.getElementById("progressBar"),
  progressPercent: document.getElementById("progressPercent"),
  statusText: document.getElementById("statusText"),
  completionMeta: document.getElementById("completionMeta"),
  elapsedTime: document.getElementById("elapsedTime"),
  errorText: document.getElementById("error"),
  downloadLink: document.getElementById("downloadLink"),
  completedActions: document.getElementById("completedActions"),
  auditWorkspace: document.getElementById("auditWorkspace"),
  auditResults: document.getElementById("auditResults"),
  resultsLoading: document.getElementById("resultsLoading"),
  resultsError: document.getElementById("resultsError"),
  resultsRetry: document.getElementById("resultsRetry"),
  resultsContent: document.getElementById("resultsContent"),
  resultTableCount: document.getElementById("resultTableCount"),
  resultColumnCount: document.getElementById("resultColumnCount"),
  resultFindingCount: document.getElementById("resultFindingCount"),
  noFindings: document.getElementById("noFindings"),
  sheetHint: document.getElementById("sheetHint"),
  sheetViewport: document.getElementById("sheetViewport"),
  findingsBody: document.getElementById("findingsBody"),
  dictionaryWorkspace: document.getElementById("dictionaryWorkspace"),
  dictionaryEmpty: document.getElementById("dictionaryEmpty"),
  dictionaryLoading: document.getElementById("dictionaryLoading"),
  dictionaryInputs: document.getElementById("dictionaryInputs"),
  dictionaryError: document.getElementById("dictionaryError"),
  dictionaryProgressBox: document.getElementById("dictionaryProgressBox"),
  dictionaryStatusText: document.getElementById("dictionaryStatusText"),
  dictionaryProgressPercent: document.getElementById("dictionaryProgressPercent"),
  dictionaryProgressBar: document.getElementById("dictionaryProgressBar"),
  dictionaryTimeLabel: document.getElementById("dictionaryTimeLabel"),
  dictionaryElapsed: document.getElementById("dictionaryElapsed"),
  dictionaryProcessHint: document.getElementById("dictionaryProcessHint"),
  classifyButton: document.getElementById("classifyButton"),
  oldDictionaryButton: document.getElementById("oldDictionaryButton"),
  oldDictionaryResults: document.getElementById("oldDictionaryResults"),
  oldDictionaryPending: document.getElementById("oldDictionaryPending"),
  oldDictionaryTable: document.getElementById("oldDictionaryTable"),
  oldDictionaryBody: document.getElementById("oldDictionaryBody"),
  newDictionaryButton: document.getElementById("newDictionaryButton"),
  newDictionarySetup: document.getElementById("dictionaryNewSetup"),
  dictionaryNewEmpty: document.getElementById("dictionaryNewEmpty"),
  newDictionaryTable: document.getElementById("dictionaryNewTable"),
  newDictionaryBody: document.getElementById("newDictionaryBody"),
  dictionaryLogEmpty: document.getElementById("dictionaryLogEmpty"),
  dictionaryLogSetup: document.getElementById("dictionaryLogSetup"),
  logPerubahanButton: document.getElementById("logPerubahanButton"),
  dictionaryLogTable: document.getElementById("dictionaryLogTable"),
  dictionaryLogBody: document.getElementById("dictionaryLogBody"),
  dictionarySheetTabs: document.querySelectorAll("[data-dictionary-sheet]"),
  nextDdlButton: document.getElementById("nextDdlButton"),
  dictionarySheetPanels: {
    old: document.getElementById("dictionaryOldPanel"),
    new: document.getElementById("dictionaryNewPanel"),
    log: document.getElementById("dictionaryLogPanel"),
  },
  sourceDdlName: document.getElementById("sourceDdlName"),
  findingsFileName: document.getElementById("findingsFileName"),
  ddlWorkspace: document.getElementById("ddlWorkspace"),
  ddlInputStatus: document.getElementById("ddlInputStatus"),
  ddlInputs: document.getElementById("ddlInputs"),
  ddlSourceName: document.getElementById("ddlSourceName"),
  ddlRetentionNote: document.getElementById("ddlRetentionNote"),
  ddlGenerateButton: document.getElementById("ddlGenerateButton"),
  ddlProgressBox: document.getElementById("ddlProgressBox"),
  ddlProgressText: document.getElementById("ddlProgressText"),
  ddlProgressPercent: document.getElementById("ddlProgressPercent"),
  ddlProgress: document.getElementById("ddlProgress"),
  ddlTimeLabel: document.getElementById("ddlTimeLabel"),
  ddlElapsed: document.getElementById("ddlElapsed"),
  ddlProcessHint: document.getElementById("ddlProcessHint"),
  ddlDownloadActions: document.getElementById("ddlDownloadActions"),
  ddlError: document.getElementById("ddlError"),
  ddlResults: document.getElementById("ddlResults"),
  ddlAlterPreview: document.getElementById("ddlAlterPreview"),
  ddlCreatePreview: document.getElementById("ddlCreatePreview"),
  ddlAlterDownload: document.getElementById("ddlAlterDownload"),
  ddlCreateDownload: document.getElementById("ddlCreateDownload"),
  ddlSheetTabs: document.querySelectorAll("[data-ddl-sheet]"),
  ddlSheetPanels: {
    alter: document.getElementById("ddlAlterPanel"),
    create: document.getElementById("ddlCreatePanel"),
  },
  featureButtons: document.querySelectorAll("[data-feature]"),
};

const PENDING_STATUS_KEY = "auditDatabaseStatusUrl";
const EXCEL_FILENAME = "temuan_standardisasi.xlsx";
const FINDING_COLUMNS = [
  "no", "nama_database", "nama_tabel", "objek_temuan", "aturan_playbook",
  "uraian_ketidaksesuaian", "solusi", "status", "catatan",
];
const JOB_ID_PATTERN = /^[0-9a-f]{32}$/;
const DICTIONARY_STAGE_NAMES = ["classification", "old", "new", "log"];
const statusJobId = new URLSearchParams(location.search).get("job_id");
const statusUrlFromUrl = JOB_ID_PATTERN.test(statusJobId || "")
  ? `/api/v1/audit/spreadsheet/${statusJobId}`
  : null;

const state = {
  elapsedStartedAt: null,
  elapsedTimer: null,
  handoff: null,
  nextProcessInputs: null,
  handoffLoadPromise: null,
  activeFeature: "audit",
  resultsAvailable: false,
  findingsUrl: null,
  resultsRequestId: 0,
  classificationRequestId: 0,
  classificationJobId: null,
  classificationReady: false,
  dictionaryStages: Object.fromEntries(DICTIONARY_STAGE_NAMES.map((name) => [name, {
    status: "idle", completed: 0, total: 1, error: null,
  }])),
  dictionaryActiveStages: new Set(),
  dictionaryElapsedMs: 0,
  dictionaryTickStartedAt: null,
  dictionaryTimer: null,
  oldDictionaryRequestId: 0,
  oldDictionaryJobId: null,
  oldDictionaryReady: false,
  newDictionaryRequestId: 0,
  newDictionaryJobId: null,
  newDictionaryReady: false,
  logPerubahanRequestId: 0,
  logPerubahanRequested: false,
  ddlRequestId: 0,
  ddlJobId: null,
  ddlRunning: false,
  ddlElapsedStartedAt: null,
  ddlElapsedTimer: null,
};

function formatElapsed(seconds) {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(remainingSeconds).padStart(2, "0")}`;
}

function startElapsed(seconds = 0) {
  state.elapsedStartedAt = Date.now() - seconds * 1000;
  if (state.elapsedTimer) return;

  const updateElapsed = () => {
    const elapsed = Math.floor((Date.now() - state.elapsedStartedAt) / 1000);
    elements.elapsedTime.textContent = formatElapsed(elapsed);
  };
  updateElapsed();
  state.elapsedTimer = setInterval(updateElapsed, 1000);
}

function stopElapsed() {
  clearInterval(state.elapsedTimer);
  state.elapsedTimer = null;
}

function startDdlElapsed(seconds = 0) {
  state.ddlElapsedStartedAt = Date.now() - seconds * 1000;
  if (state.ddlElapsedTimer !== null) return;
  const update = () => {
    elements.ddlElapsed.textContent = formatElapsed(
      Math.floor((Date.now() - state.ddlElapsedStartedAt) / 1000),
    );
  };
  update();
  state.ddlElapsedTimer = setInterval(update, 1000);
}

function stopDdlElapsed(finalSeconds = null) {
  clearInterval(state.ddlElapsedTimer);
  state.ddlElapsedTimer = null;
  if (finalSeconds !== null) elements.ddlElapsed.textContent = formatElapsed(finalSeconds);
}

function updateDictionaryElapsed() {
  const runningMs = state.dictionaryTickStartedAt === null
    ? 0 : Date.now() - state.dictionaryTickStartedAt;
  elements.dictionaryElapsed.textContent = formatElapsed(
    Math.floor((state.dictionaryElapsedMs + runningMs) / 1000),
  );
}

function updateDictionaryStage(name, status, completed = 0, total = 1, error = null) {
  state.dictionaryStages[name] = {
    status,
    completed: Number.isFinite(completed) ? completed : 0,
    total: Number.isFinite(total) ? Math.max(1, total) : 1,
    error,
  };
  renderDictionaryProgress();
}

function failDictionaryStage(name, message) {
  const { completed, total } = state.dictionaryStages[name];
  updateDictionaryStage(name, "failed", completed, total, message);
}

function renderDictionaryProgress() {
  const stages = state.dictionaryStages;
  const progress = DICTIONARY_STAGE_NAMES.reduce((sum, name) => {
    const stage = stages[name];
    return sum + (stage.status === "completed" ? 1 : Math.min(1, stage.completed / stage.total));
  }, 0);
  const percent = Math.round(progress * 25);
  elements.dictionaryProgressBar.value = percent;
  elements.dictionaryProgressPercent.textContent = `${percent}%`;

  const failed = DICTIONARY_STAGE_NAMES.find((name) => stages[name].status === "failed");
  const complete = DICTIONARY_STAGE_NAMES.every((name) => stages[name].status === "completed");
  elements.dictionaryTimeLabel.textContent = complete ? "Durasi proses" : "Waktu berjalan";
  elements.dictionaryProgressBox.classList.toggle("is-error", Boolean(failed));
  elements.dictionaryProgressBox.classList.toggle("is-complete", complete);
  elements.dictionaryProcessHint.textContent = "";
  if (failed) {
    elements.dictionaryStatusText.textContent = stages[failed].error;
  } else if (complete) {
    elements.dictionaryStatusText.textContent = "Data Dictionary selesai. Semua sheet siap ditinjau.";
  } else if (stages.log.status !== "idle") {
    elements.dictionaryStatusText.textContent = "Tahap 3/3 · Menyusun Log Perubahan";
  } else if (stages.new.status !== "idle") {
    elements.dictionaryStatusText.textContent = "Tahap 2/3 · Menyusun Dictionary Baru";
  } else {
    elements.dictionaryStatusText.textContent = "Tahap 1/3 · Klasifikasi Tabel";
  }
}

function resetDictionaryProgress() {
  clearInterval(state.dictionaryTimer);
  state.dictionaryTimer = null;
  state.dictionaryActiveStages.clear();
  state.dictionaryElapsedMs = 0;
  state.dictionaryTickStartedAt = null;
  state.dictionaryStages = Object.fromEntries(DICTIONARY_STAGE_NAMES.map((name) => [name, {
    status: "idle", completed: 0, total: 1, error: null,
  }]));
  elements.dictionaryElapsed.textContent = "00:00";
  elements.dictionaryTimeLabel.textContent = "Waktu berjalan";
  elements.dictionaryProgressBar.value = 0;
  elements.dictionaryProgressPercent.textContent = "0%";
  elements.dictionaryStatusText.textContent = "";
  elements.dictionaryProcessHint.textContent = "";
  elements.dictionaryProgressBox.classList.remove("is-error", "is-complete");
  elements.dictionaryProgressBox.hidden = true;
}

function setDictionaryStageRunning(stage, running) {
  if (running) {
    elements.dictionaryProgressBox.hidden = false;
    state.dictionaryActiveStages.add(stage);
    if (state.dictionaryTimer === null) {
      state.dictionaryTickStartedAt = Date.now();
      state.dictionaryTimer = setInterval(updateDictionaryElapsed, 1000);
    }
  } else {
    state.dictionaryActiveStages.delete(stage);
    if (state.dictionaryActiveStages.size === 0 && state.dictionaryTimer !== null) {
      state.dictionaryElapsedMs += Date.now() - state.dictionaryTickStartedAt;
      state.dictionaryTickStartedAt = null;
      clearInterval(state.dictionaryTimer);
      state.dictionaryTimer = null;
    }
  }
  updateDictionaryElapsed();
}

function clearTracking() {
  sessionStorage.removeItem(PENDING_STATUS_KEY);
  if (statusUrlFromUrl) history.replaceState(null, "", location.pathname);
}

function clearHandoff() {
  state.handoff = null;
  state.nextProcessInputs = null;
  state.handoffLoadPromise = null;
  elements.dictionaryLoading.hidden = true;
  elements.dictionaryError.textContent = "";
  elements.completedActions.hidden = true;
  elements.nextProcessButton.hidden = true;
  clearAuditResults();
  clearClassification();
}

function clearClassification() {
  resetDictionaryProgress();
  state.classificationRequestId += 1;
  state.classificationJobId = null;
  state.classificationReady = false;
  elements.classifyButton.disabled = false;
  elements.classifyButton.hidden = false;
  elements.classifyButton.textContent = "Proses Data Dictionary";
  clearOldDictionary();
}

function clearOldDictionary() {
  clearDdlStandard();
  state.oldDictionaryRequestId += 1;
  state.oldDictionaryJobId = null;
  state.oldDictionaryReady = false;
  clearNewDictionary();
  elements.oldDictionaryButton.hidden = true;
  elements.oldDictionaryButton.disabled = false;
  elements.oldDictionaryButton.textContent = "Coba lagi Old Dictionary";
  elements.oldDictionaryResults.hidden = true;
  elements.oldDictionaryPending.hidden = true;
  elements.oldDictionaryTable.hidden = false;
  elements.oldDictionaryBody.replaceChildren();
  selectDictionarySheet("old");
}

function clearNewDictionary() {
  clearDdlStandard();
  state.newDictionaryRequestId += 1;
  state.newDictionaryJobId = null;
  state.newDictionaryReady = false;
  updateDdlReadiness();
  clearLogPerubahan();
  elements.newDictionaryButton.disabled = false;
  elements.newDictionaryButton.hidden = true;
  elements.newDictionaryButton.textContent = "Coba lagi Dictionary New";
  elements.newDictionarySetup.hidden = false;
  elements.dictionaryNewEmpty.textContent = "Dictionary New menunggu hasil klasifikasi tabel.";
  elements.newDictionaryTable.hidden = true;
  elements.newDictionaryBody.replaceChildren();
}

function clearLogPerubahan() {
  if (state.dictionaryActiveStages.has("log")) setDictionaryStageRunning("log", false);
  state.logPerubahanRequestId += 1;
  state.logPerubahanRequested = false;
  elements.dictionaryLogSetup.hidden = false;
  elements.dictionaryLogEmpty.textContent = "Log Perubahan akan disusun setelah Dictionary New selesai.";
  elements.logPerubahanButton.disabled = true;
  elements.logPerubahanButton.hidden = true;
  elements.logPerubahanButton.textContent = "Coba lagi Log Perubahan";
  updateDictionaryStage("log", "idle");
  elements.dictionaryLogTable.hidden = true;
  elements.dictionaryLogBody.replaceChildren();
}

function clearDdlStandard() {
  stopDdlElapsed(0);
  state.ddlRequestId += 1;
  state.ddlJobId = null;
  state.ddlRunning = false;
  elements.ddlGenerateButton.disabled = false;
  elements.ddlGenerateButton.textContent = "Buat DDL Standar";
  elements.ddlProgressText.textContent = "";
  elements.ddlProgressBox.hidden = true;
  elements.ddlProgressBox.classList.remove("is-complete");
  elements.ddlProgressPercent.textContent = "0%";
  elements.ddlProgress.max = 1;
  elements.ddlProgress.value = 0;
  elements.ddlTimeLabel.textContent = "Waktu berjalan";
  elements.ddlProcessHint.textContent = "";
  elements.ddlDownloadActions.hidden = true;
  elements.ddlError.textContent = "";
  elements.ddlResults.hidden = true;
  elements.ddlAlterPreview.textContent = "";
  elements.ddlCreatePreview.textContent = "";
  selectDdlSheet("alter");
  updateDdlReadiness();
}

function updateDdlReadiness() {
  const ready = Boolean(state.handoff?.auditJobId && state.oldDictionaryReady && state.newDictionaryReady);
  elements.ddlInputStatus.textContent = ready
    ? "DDL asli dan hasil Data Dictionary siap digunakan untuk menyusun DDL Standar."
    : "Selesaikan Dictionary Old dan Dictionary New terlebih dahulu.";
  elements.ddlInputs.hidden = !ready;
  elements.ddlRetentionNote.hidden = !ready;
  elements.ddlSourceName.textContent = ready ? state.handoff.sourceFilename : "";
  elements.ddlGenerateButton.hidden = !ready || state.ddlRunning || !elements.ddlResults.hidden;
  elements.nextDdlButton.hidden = !ready;
}

function selectDictionarySheet(sheetName) {
  elements.dictionarySheetTabs.forEach((tab) => {
    const selected = tab.dataset.dictionarySheet === sheetName;
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
  });
  for (const [name, panel] of Object.entries(elements.dictionarySheetPanels)) {
    panel.hidden = name !== sheetName;
  }
}

function selectDdlSheet(sheetName) {
  elements.ddlSheetTabs.forEach((tab) => {
    const selected = tab.dataset.ddlSheet === sheetName;
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
  });
  for (const [name, panel] of Object.entries(elements.ddlSheetPanels)) {
    panel.hidden = name !== sheetName;
  }
}

function clearAuditResults() {
  state.resultsRequestId += 1;
  state.resultsAvailable = false;
  state.findingsUrl = null;
  elements.auditResults.hidden = true;
  elements.resultsContent.hidden = true;
  elements.resultsRetry.hidden = true;
  elements.resultsError.textContent = "";
  elements.findingsBody.replaceChildren();
}

function saveHandoff(job) {
  if (!job.source_url || !job.download_url || !job.source_filename) return;

  state.handoff = {
    auditJobId: job.job_id,
    sourceUrl: job.source_url,
    findingsUrl: job.download_url,
    sourceFilename: job.source_filename,
  };
  elements.nextProcessButton.hidden = false;
}

function showProcessing() {
  elements.progressBox.classList.remove("is-complete");
  elements.completionMeta.hidden = true;
  elements.submitButton.hidden = true;
  elements.submitButton.disabled = true;
  elements.fileInput.disabled = true;
  elements.modelSelect.disabled = true;
  elements.progressBox.hidden = false;
  elements.downloadLink.hidden = true;
  elements.nextProcessButton.hidden = true;
  startElapsed();
}

function showRetry() {
  elements.submitButton.hidden = false;
  elements.submitButton.disabled = false;
  elements.fileInput.disabled = false;
  elements.modelSelect.disabled = false;
  elements.progressBox.hidden = true;
  stopElapsed();
}

async function responseDetail(response) {
  try {
    const body = await response.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail.map((item) => item.msg || "Data permintaan tidak valid.").join(" ");
    }
    return "Permintaan gagal.";
  } catch {
    return `Permintaan gagal (HTTP ${response.status}).`;
  }
}

function updateProgress(job) {
  elements.progressBar.max = job.total_batches || 1;
  elements.progressBar.value = job.completed_batches;
  elements.progressPercent.textContent = `${Math.round(
    100 * elements.progressBar.value / elements.progressBar.max,
  )}%`;
  startElapsed(job.elapsed_seconds || 0);
}

function finishAudit(job) {
  clearTracking();
  elements.statusText.textContent = "Analisis selesai. Excel siap diunduh.";
  elements.completionMeta.textContent = `Durasi analisis: ${formatElapsed(job.elapsed_seconds || 0)}`;
  elements.completionMeta.hidden = false;
  elements.progressBar.value = elements.progressBar.max;
  elements.progressPercent.textContent = "100%";
  stopElapsed();
  elements.progressBox.classList.add("is-complete");
  elements.downloadLink.href = job.download_url;
  elements.completedActions.hidden = false;
  elements.downloadLink.hidden = false;
  elements.fileInput.disabled = false;
  elements.modelSelect.disabled = false;
  saveHandoff(job);
  loadAuditResults(job.findings_url);
}

function findingHighlight(finding) {
  const objectName = String(finding.objek_temuan || "").toLowerCase();
  const detail = String(finding.uraian_ketidaksesuaian || "").toLowerCase();
  const solution = String(finding.solusi || "").toLowerCase();
  const combined = objectName + detail + solution;

  if (combined.includes("drop") || combined.includes("hapus")) return "is-removal";
  if (["comment", "foreign key", "index", "check"].some((word) => objectName.includes(word))) return "";

  const addsObject = ["tambah", "penambahan"].some((word) => objectName.includes(word))
    && ["kolom", "tabel"].some((word) => objectName.includes(word));
  const addsFromSolution = [
    "tambahkan kolom", "tambahkan tabel", "tambahkan satu tabel", "tambahkan satu set audit trail",
  ].some((phrase) => solution.includes(phrase));
  const addsFromDescription = ["penambahan kolom", "penambahan tabel"]
    .some((phrase) => (detail + solution).includes(phrase));

  if (objectName.includes("audit trail") || objectName.includes("tabel metadata")
      || addsObject || addsFromSolution || addsFromDescription) return "is-addition";
  return "";
}

function renderFinding(finding) {
  const row = document.createElement("tr");
  const highlight = findingHighlight(finding);
  if (highlight) row.classList.add(highlight);
  for (const key of FINDING_COLUMNS) {
    const cell = document.createElement(key === "no" ? "th" : "td");
    if (key === "no") cell.scope = "row";
    cell.textContent = finding[key] ?? "-";
    row.append(cell);
  }
  return row;
}

function renderAuditResults(audit) {
  elements.resultTableCount.textContent = audit.summary.table_count;
  elements.resultColumnCount.textContent = audit.summary.column_count;
  elements.resultFindingCount.textContent = audit.findings.length;
  elements.noFindings.hidden = audit.findings.length !== 0;
  elements.sheetHint.hidden = audit.findings.length === 0;
  elements.sheetViewport.hidden = audit.findings.length === 0;

  const findings = document.createDocumentFragment();
  for (const finding of audit.findings) findings.append(renderFinding(finding));
  elements.findingsBody.replaceChildren(findings);
  elements.resultsLoading.hidden = true;
  elements.resultsContent.hidden = false;
}

async function loadAuditResults(url) {
  state.findingsUrl = url;
  state.resultsAvailable = true;
  const requestId = ++state.resultsRequestId;
  elements.auditResults.hidden = state.activeFeature !== "audit";
  elements.resultsLoading.hidden = false;
  elements.resultsContent.hidden = true;
  elements.resultsError.textContent = "";
  elements.resultsRetry.hidden = true;

  try {
    if (!url) throw new Error("Hasil audit tidak tersedia.");
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) throw new Error(await responseDetail(response));
    const audit = await response.json();
    if (requestId !== state.resultsRequestId) return;
    renderAuditResults(audit);
  } catch (error) {
    if (requestId !== state.resultsRequestId) return;
    elements.resultsLoading.hidden = true;
    elements.resultsError.textContent = `Temuan belum bisa ditampilkan: ${error.message}`;
    elements.resultsRetry.hidden = !url;
  }
}

async function checkStatus(statusUrl) {
  let response;
  try {
    response = await fetch(statusUrl, { cache: "no-store" });
  } catch {
    elements.statusText.textContent = "Koneksi terputus. Mencoba lagi...";
    setTimeout(() => checkStatus(statusUrl), 3000);
    return;
  }

  if (response.status === 404) {
    clearTracking();
    elements.errorText.textContent = "Proses tidak ditemukan. Server mungkin telah direstart; unggah ulang file.";
    showRetry();
    return;
  }
  if (!response.ok) {
    elements.statusText.textContent = "Status belum bisa dibaca. Mencoba lagi...";
    setTimeout(() => checkStatus(statusUrl), 3000);
    return;
  }

  let job;
  try {
    job = await response.json();
  } catch {
    elements.statusText.textContent = "Status belum bisa dibaca. Mencoba lagi...";
    setTimeout(() => checkStatus(statusUrl), 3000);
    return;
  }

  updateProgress(job);
  if (job.status === "completed") {
    finishAudit(job);
    return;
  }
  if (job.status === "failed") {
    clearTracking();
    elements.errorText.textContent = job.error || "Analisis gagal.";
    showRetry();
    return;
  }

  elements.statusText.textContent = job.status === "queued"
    ? "Menunggu giliran audit..."
    : `Mengaudit batch ${job.completed_batches} dari ${job.total_batches}...`;
  setTimeout(() => checkStatus(statusUrl), 3000);
}

async function fetchFile(url, filename, type) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) throw new Error(await responseDetail(response));
  return new File([await response.blob()], filename, { type });
}

async function loadNextProcessInputs() {
  if (!state.handoff) throw new Error("Selesaikan Audit Database terlebih dahulu.");
  if (state.nextProcessInputs) return state.nextProcessInputs;
  if (state.handoffLoadPromise) return state.handoffLoadPromise;

  state.handoffLoadPromise = Promise.all([
    fetchFile(state.handoff.sourceUrl, state.handoff.sourceFilename, "application/sql"),
    fetchFile(state.handoff.findingsUrl, EXCEL_FILENAME, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
  ]).then(([ddlFile, findingsFile]) => {
    state.nextProcessInputs = { ddlFile, findingsFile };
    return state.nextProcessInputs;
  }).finally(() => {
    state.handoffLoadPromise = null;
  });
  return state.handoffLoadPromise;
}

function setActiveFeature(featureName) {
  elements.featureButtons.forEach((button) => {
    const active = button.dataset.feature === featureName;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
}

function showWorkspace(workspaceName) {
  elements.auditWorkspace.hidden = workspaceName !== "audit";
  elements.auditResults.hidden = workspaceName !== "audit" || !state.resultsAvailable;
  elements.dictionaryWorkspace.hidden = workspaceName !== "dictionary";
  elements.ddlWorkspace.hidden = workspaceName !== "ddl";
}

function renderDictionaryInputs(inputs) {
  elements.dictionaryEmpty.hidden = true;
  elements.dictionaryLoading.hidden = true;
  elements.dictionaryError.textContent = "";
  elements.sourceDdlName.textContent = inputs.ddlFile.name;
  elements.findingsFileName.textContent = inputs.findingsFile.name;
  elements.dictionaryInputs.hidden = false;
}

async function pollClassification(statusUrl, requestId) {
  try {
    const response = await fetch(statusUrl, { cache: "no-store" });
    if (!response.ok) throw new Error(await responseDetail(response));
    const job = await response.json();
    if (requestId !== state.classificationRequestId) return;
    if (job.status === "completed") {
      state.classificationReady = true;
      updateDictionaryStage("classification", "completed", job.total_tables, job.total_tables);
      elements.classifyButton.hidden = true;
      startNewDictionary();
      setDictionaryStageRunning("classification", false);
      return;
    }
    if (job.status === "failed") throw new Error(job.error || "Klasifikasi gagal.");
    updateDictionaryStage("classification", job.status, job.completed_tables, job.total_tables);
    setTimeout(() => pollClassification(statusUrl, requestId), 3000);
  } catch (error) {
    if (requestId !== state.classificationRequestId) return;
    setDictionaryStageRunning("classification", false);
    failDictionaryStage("classification", `Klasifikasi tidak selesai: ${error.message}`);
    elements.classifyButton.disabled = false;
  }
}

async function startClassification() {
  if (!state.handoff?.auditJobId) return;
  const rerunAll = state.classificationReady;
  if (rerunAll) resetDictionaryProgress();
  state.classificationJobId = null;
  state.classificationReady = false;
  if (rerunAll) clearOldDictionary();
  if (!state.oldDictionaryJobId) startOldDictionary();
  const requestId = ++state.classificationRequestId;
  setDictionaryStageRunning("classification", true);
  updateDictionaryStage("classification", "running");
  elements.classifyButton.disabled = true;
  try {
    const response = await fetch("/api/v1/data-dictionary/classification", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ audit_job_id: state.handoff.auditJobId, model: elements.modelSelect.value }),
    });
    if (!response.ok) throw new Error(await responseDetail(response));
    const job = await response.json();
    if (requestId === state.classificationRequestId) {
      state.classificationJobId = job.job_id;
      pollClassification(job.status_url, requestId);
    }
  } catch (error) {
    if (requestId !== state.classificationRequestId) return;
    setDictionaryStageRunning("classification", false);
    failDictionaryStage("classification", `Klasifikasi tidak dapat dimulai: ${error.message}`);
    elements.classifyButton.disabled = false;
    elements.classifyButton.hidden = false;
  }
}

function renderOldDictionary(result) {
  const rows = document.createDocumentFragment();
  Object.entries(result).forEach(([tableName, table], tableIndex) => {
    Object.entries(table.kolom).forEach(([columnName, column], columnIndex) => {
      const row = document.createElement("tr");
      if (columnIndex === 0) row.classList.add("dictionary-table-start");
      const number = document.createElement("th");
      number.scope = "row";
      number.textContent = String(tableIndex + 1);
      row.append(number);
      for (const value of [
        tableName, "Existing", table.jenis_tabel, table.deskripsi_tabel,
        columnIndex + 1, columnName, column.tipe_data, column.boleh_null,
        column.key, column.referensi_fk, column.default, column.comment,
        column.fk_constraint, column.unique_constraint, column.check_constraint,
        column.index,
      ]) {
        const cell = row.insertCell();
        cell.textContent = value ?? "";
      }
      rows.append(row);
    });
  });
  elements.oldDictionaryBody.replaceChildren(rows);
  elements.oldDictionaryResults.hidden = false;
  elements.oldDictionaryPending.hidden = true;
  elements.oldDictionaryTable.hidden = false;
  elements.oldDictionaryButton.hidden = true;
  state.oldDictionaryReady = true;
  updateDdlReadiness();
  if (!state.newDictionaryReady) {
    elements.dictionaryLogEmpty.textContent = "Menunggu Dictionary New selesai.";
  }
}

function renderNewDictionary(result) {
  const newRows = document.createDocumentFragment();
  Object.entries(result).forEach(([tableName, table], tableIndex) => {
    table.kolom_baru.forEach((column, columnIndex) => {
      const row = document.createElement("tr");
      if (columnIndex === 0) row.classList.add("dictionary-table-start");
      if (column._row_status === "KUNING") row.classList.add("is-addition");
      if (column._row_status === "HIJAU") row.classList.add("is-new-table");
      const number = document.createElement("th");
      number.scope = "row";
      number.textContent = String(tableIndex + 1);
      row.append(number);
      for (const value of [
        tableName, "New", table.jenis_tabel, table.deskripsi_tabel,
        column.no_kolom, column.nama_kolom, column.tipe_data, column.boleh_null,
        column.key, column.referensi_fk, column.default, column.comment,
        column.fk_constraint, column.unique_constraint, column.check_constraint,
        column.index, column.pii,
      ]) {
        row.insertCell().textContent = value ?? "";
      }
      newRows.append(row);
    });
  });
  elements.newDictionaryBody.replaceChildren(newRows);
  if (!state.oldDictionaryReady) {
    elements.oldDictionaryResults.hidden = false;
    elements.oldDictionaryPending.hidden = false;
    elements.oldDictionaryTable.hidden = true;
    selectDictionarySheet("new");
  }
  elements.newDictionarySetup.hidden = true;
  elements.newDictionaryTable.hidden = false;
  state.newDictionaryReady = true;
  updateDdlReadiness();
  if (!state.oldDictionaryReady) {
    elements.dictionaryLogEmpty.textContent = "Menunggu Dictionary Old selesai.";
  }
}

function startLogWhenReady() {
  if (!state.oldDictionaryReady || !state.newDictionaryReady || state.logPerubahanRequested) return;
  elements.logPerubahanButton.disabled = false;
  startLogPerubahan();
}

async function pollNewDictionary(statusUrl, requestId) {
  try {
    const response = await fetch(statusUrl, { cache: "no-store" });
    if (!response.ok) throw new Error(await responseDetail(response));
    const job = await response.json();
    if (requestId !== state.newDictionaryRequestId) return;
    if (job.status === "completed") {
      renderNewDictionary(job.result);
      updateDictionaryStage("new", "completed", job.total_batches, job.total_batches);
      startLogWhenReady();
      setDictionaryStageRunning("new", false);
      return;
    }
    if (job.status === "failed") throw new Error(job.error || "Dictionary New gagal.");
    updateDictionaryStage("new", job.status, job.completed_batches, job.total_batches);
    setTimeout(() => pollNewDictionary(statusUrl, requestId), 3000);
  } catch (error) {
    if (requestId !== state.newDictionaryRequestId) return;
    setDictionaryStageRunning("new", false);
    failDictionaryStage("new", `Dictionary New tidak selesai: ${error.message}`);
    elements.dictionaryNewEmpty.textContent = "Dictionary New belum selesai. Coba proses ulang.";
    elements.newDictionaryButton.disabled = false;
    elements.newDictionaryButton.hidden = false;
    elements.newDictionaryButton.textContent = "Coba lagi Dictionary New";
  }
}

async function startNewDictionary() {
  if (!state.handoff?.auditJobId || !state.classificationReady || !state.classificationJobId) return;
  clearDdlStandard();
  clearLogPerubahan();
  state.newDictionaryJobId = null;
  state.newDictionaryReady = false;
  updateDdlReadiness();
  const requestId = ++state.newDictionaryRequestId;
  setDictionaryStageRunning("new", true);
  updateDictionaryStage("new", "running");
  elements.newDictionaryButton.disabled = true;
  elements.newDictionaryButton.hidden = true;
  elements.dictionaryNewEmpty.textContent = "Dictionary New sedang disusun dari hasil audit.";
  try {
    const response = await fetch("/api/v1/data-dictionary/new-dictionary", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        audit_job_id: state.handoff.auditJobId,
        classification_job_id: state.classificationJobId,
        model: elements.modelSelect.value,
      }),
    });
    if (!response.ok) throw new Error(await responseDetail(response));
    const job = await response.json();
    if (requestId === state.newDictionaryRequestId) {
      state.newDictionaryJobId = job.job_id;
      pollNewDictionary(job.status_url, requestId);
    }
  } catch (error) {
    if (requestId !== state.newDictionaryRequestId) return;
    setDictionaryStageRunning("new", false);
    failDictionaryStage("new", `Dictionary New tidak dapat dimulai: ${error.message}`);
    elements.dictionaryNewEmpty.textContent = "Dictionary New belum selesai. Coba proses ulang.";
    elements.newDictionaryButton.disabled = false;
    elements.newDictionaryButton.hidden = false;
    elements.newDictionaryButton.textContent = "Coba lagi Dictionary New";
  }
}

function renderLogPerubahan(result) {
  const rows = document.createDocumentFragment();
  for (const item of result.log_perubahan) {
    const row = document.createElement("tr");
    const number = document.createElement("th");
    number.scope = "row";
    number.textContent = String(item.no_baru);
    row.append(number);
    if (item.jenis_perubahan === "Baru") row.classList.add("is-addition");
    for (const value of [
      item.no_lama, item.jenis_perubahan, item.nama_tabel, item.objek_temuan,
      item.aturan_playbook, item.posisi_sisipan, item.uraian_baru,
    ]) {
      row.insertCell().textContent = value ?? "";
    }
    rows.append(row);
  }
  elements.dictionaryLogBody.replaceChildren(rows);
  elements.dictionaryLogSetup.hidden = true;
  elements.dictionaryLogTable.hidden = false;
  elements.classifyButton.hidden = false;
  elements.classifyButton.disabled = false;
  elements.classifyButton.textContent = "Proses ulang Data Dictionary";
}

async function pollLogPerubahan(statusUrl, requestId) {
  try {
    const response = await fetch(statusUrl, { cache: "no-store" });
    if (!response.ok) throw new Error(await responseDetail(response));
    const job = await response.json();
    if (requestId !== state.logPerubahanRequestId) return;
    if (job.status === "completed") {
      renderLogPerubahan(job.result);
      updateDictionaryStage("log", "completed", job.total_batches, job.total_batches);
      setDictionaryStageRunning("log", false);
      return;
    }
    if (job.status === "failed") throw new Error(job.error || "Log Perubahan gagal.");
    updateDictionaryStage("log", job.status, job.completed_batches, job.total_batches);
    setTimeout(() => pollLogPerubahan(statusUrl, requestId), 3000);
  } catch (error) {
    if (requestId !== state.logPerubahanRequestId) return;
    setDictionaryStageRunning("log", false);
    failDictionaryStage("log", `Log Perubahan tidak selesai: ${error.message}`);
    elements.dictionaryLogEmpty.textContent = "Log Perubahan belum selesai. Coba proses ulang.";
    elements.logPerubahanButton.disabled = false;
    elements.logPerubahanButton.hidden = false;
    elements.logPerubahanButton.textContent = "Coba lagi Log Perubahan";
  }
}

async function startLogPerubahan() {
  if (!state.handoff?.auditJobId || !state.oldDictionaryReady || !state.newDictionaryReady
      || !state.oldDictionaryJobId || !state.newDictionaryJobId
      || elements.logPerubahanButton.disabled) return;
  state.logPerubahanRequested = true;
  const requestId = ++state.logPerubahanRequestId;
  setDictionaryStageRunning("log", true);
  updateDictionaryStage("log", "running");
  elements.logPerubahanButton.disabled = true;
  elements.logPerubahanButton.hidden = true;
  elements.dictionaryLogEmpty.textContent = "Log Perubahan sedang disusun dari kedua dictionary.";
  try {
    const response = await fetch("/api/v1/data-dictionary/log-perubahan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        audit_job_id: state.handoff.auditJobId,
        old_dictionary_job_id: state.oldDictionaryJobId,
        new_dictionary_job_id: state.newDictionaryJobId,
        model: elements.modelSelect.value,
      }),
    });
    if (!response.ok) throw new Error(await responseDetail(response));
    const job = await response.json();
    if (requestId === state.logPerubahanRequestId) pollLogPerubahan(job.status_url, requestId);
  } catch (error) {
    if (requestId !== state.logPerubahanRequestId) return;
    setDictionaryStageRunning("log", false);
    failDictionaryStage("log", `Log Perubahan tidak dapat dimulai: ${error.message}`);
    elements.dictionaryLogEmpty.textContent = "Log Perubahan belum selesai. Coba proses ulang.";
    elements.logPerubahanButton.disabled = false;
    elements.logPerubahanButton.hidden = false;
    elements.logPerubahanButton.textContent = "Coba lagi Log Perubahan";
  }
}

async function pollOldDictionary(statusUrl, requestId) {
  try {
    const response = await fetch(statusUrl, { cache: "no-store" });
    if (!response.ok) throw new Error(await responseDetail(response));
    const job = await response.json();
    if (requestId !== state.oldDictionaryRequestId) return;
    if (job.status === "completed") {
      renderOldDictionary(job.result);
      updateDictionaryStage("old", "completed", job.total_objects, job.total_objects);
      startLogWhenReady();
      setDictionaryStageRunning("old", false);
      return;
    }
    if (job.status === "failed") throw new Error(job.error || "Old Dictionary gagal.");
    updateDictionaryStage("old", job.status, job.completed_objects, job.total_objects);
    setTimeout(() => pollOldDictionary(statusUrl, requestId), 3000);
  } catch (error) {
    if (requestId !== state.oldDictionaryRequestId) return;
    setDictionaryStageRunning("old", false);
    failDictionaryStage("old", `Old Dictionary tidak selesai: ${error.message}`);
    elements.oldDictionaryPending.textContent = "Dictionary Old belum selesai. Coba proses ulang.";
    elements.oldDictionaryButton.disabled = false;
    elements.oldDictionaryButton.hidden = false;
  }
}

async function startOldDictionary() {
  clearDdlStandard();
  if (!state.handoff?.auditJobId) return;
  state.oldDictionaryJobId = null;
  state.oldDictionaryReady = false;
  updateDdlReadiness();
  const requestId = ++state.oldDictionaryRequestId;
  setDictionaryStageRunning("old", true);
  updateDictionaryStage("old", "running");
  elements.oldDictionaryButton.disabled = true;
  elements.oldDictionaryButton.hidden = true;
  elements.oldDictionaryResults.hidden = !state.newDictionaryReady;
  elements.oldDictionaryPending.textContent = "Dictionary Old sedang disusun...";
  elements.oldDictionaryPending.hidden = !state.newDictionaryReady;
  elements.oldDictionaryTable.hidden = state.newDictionaryReady;
  try {
    const response = await fetch("/api/v1/data-dictionary/old-dictionary", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ audit_job_id: state.handoff.auditJobId, model: elements.modelSelect.value }),
    });
    if (!response.ok) throw new Error(await responseDetail(response));
    const job = await response.json();
    if (requestId === state.oldDictionaryRequestId) {
      state.oldDictionaryJobId = job.job_id;
      pollOldDictionary(job.status_url, requestId);
    }
  } catch (error) {
    if (requestId !== state.oldDictionaryRequestId) return;
    setDictionaryStageRunning("old", false);
    failDictionaryStage("old", `Old Dictionary tidak dapat dimulai: ${error.message}`);
    elements.oldDictionaryButton.disabled = false;
    elements.oldDictionaryButton.hidden = false;
  }
}

async function showDictionary() {
  showWorkspace("dictionary");
  if (!state.handoff) {
    elements.dictionaryEmpty.hidden = false;
    elements.dictionaryLoading.hidden = true;
    elements.dictionaryInputs.hidden = true;
    elements.dictionaryError.textContent = "";
    return;
  }

  elements.dictionaryEmpty.hidden = true;
  elements.dictionaryInputs.hidden = true;
  elements.dictionaryLoading.hidden = false;
  elements.dictionaryError.textContent = "";
  try {
    renderDictionaryInputs(await loadNextProcessInputs());
  } catch (error) {
    elements.dictionaryLoading.hidden = true;
    elements.dictionaryError.textContent = `Input tidak dapat disiapkan: ${error.message}`;
  }
}

function showDdlStandard() {
  updateDdlReadiness();
  showWorkspace("ddl");
}

async function pollDdlStandard(statusUrl, requestId) {
  try {
    const response = await fetch(statusUrl, { cache: "no-store" });
    if (!response.ok) throw new Error(await responseDetail(response));
    const job = await response.json();
    if (requestId !== state.ddlRequestId) return;
    if (job.status === "completed") {
      state.ddlRunning = false;
      stopDdlElapsed(job.elapsed_seconds || 0);
      elements.ddlProgressBox.classList.add("is-complete");
      elements.ddlProgressBox.hidden = false;
      elements.ddlProgressText.textContent = "DDL Standar selesai. SQL siap ditinjau.";
      elements.ddlProgressPercent.textContent = "100%";
      elements.ddlProgress.max = 1;
      elements.ddlProgress.value = 1;
      elements.ddlTimeLabel.textContent = "Durasi proses";
      elements.ddlProcessHint.textContent = "";
      elements.ddlAlterPreview.textContent = job.result.ddl_alter;
      elements.ddlCreatePreview.textContent = job.result.ddl_create;
      elements.ddlAlterDownload.href = `/api/v1/ddl-standard/${state.ddlJobId}/download/alter`;
      elements.ddlCreateDownload.href = `/api/v1/ddl-standard/${state.ddlJobId}/download/create`;
      elements.ddlDownloadActions.hidden = false;
      elements.ddlResults.hidden = false;
      selectDdlSheet("alter");
      updateDdlReadiness();
      return;
    }
    if (job.status === "failed") throw new Error(job.error || "DDL Standar gagal diproses.");
    elements.ddlProgress.max = job.total_objects || 1;
    elements.ddlProgress.value = job.completed_objects;
    elements.ddlProgressPercent.textContent = `${Math.round(
      100 * elements.ddlProgress.value / elements.ddlProgress.max,
    )}%`;
    elements.ddlProgressText.textContent = "Menyusun DDL Standar";
    startDdlElapsed(job.elapsed_seconds || 0);
    setTimeout(() => pollDdlStandard(statusUrl, requestId), 3000);
  } catch (error) {
    if (requestId !== state.ddlRequestId) return;
    state.ddlRunning = false;
    stopDdlElapsed();
    elements.ddlProgressBox.hidden = true;
    elements.ddlProgressText.textContent = "";
    elements.ddlError.textContent = `DDL Standar tidak selesai: ${error.message}`;
    elements.ddlGenerateButton.textContent = "Coba lagi";
    updateDdlReadiness();
  }
}

async function startDdlStandard() {
  if (!state.handoff?.auditJobId || !state.oldDictionaryReady || !state.newDictionaryReady) return;
  const requestId = ++state.ddlRequestId;
  state.ddlRunning = true;
  elements.ddlGenerateButton.hidden = true;
  elements.ddlError.textContent = "";
  elements.ddlProgressBox.classList.remove("is-complete");
  elements.ddlProgressBox.hidden = false;
  elements.ddlProgressText.textContent = "Menyiapkan DDL Standar...";
  elements.ddlProgressPercent.textContent = "0%";
  elements.ddlTimeLabel.textContent = "Waktu berjalan";
  elements.ddlProcessHint.textContent = "";
  elements.ddlProgress.value = 0;
  elements.ddlDownloadActions.hidden = true;
  startDdlElapsed();
  try {
    const response = await fetch("/api/v1/ddl-standard", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        audit_job_id: state.handoff.auditJobId,
        old_dictionary_job_id: state.oldDictionaryJobId,
        new_dictionary_job_id: state.newDictionaryJobId,
        model: elements.modelSelect.value,
      }),
    });
    if (!response.ok) throw new Error(await responseDetail(response));
    const job = await response.json();
    if (requestId !== state.ddlRequestId) return;
    state.ddlJobId = job.job_id;
    pollDdlStandard(job.status_url, requestId);
  } catch (error) {
    if (requestId !== state.ddlRequestId) return;
    state.ddlRunning = false;
    stopDdlElapsed();
    elements.ddlProgressBox.hidden = true;
    elements.ddlProgressText.textContent = "";
    elements.ddlError.textContent = `DDL Standar tidak dapat dimulai: ${error.message}`;
    updateDdlReadiness();
  }
}

async function selectFeature(featureName) {
  state.activeFeature = featureName;
  setActiveFeature(featureName);
  if (featureName === "audit") {
    showWorkspace("audit");
    return;
  }
  if (featureName === "dictionary") {
    await showDictionary();
    return;
  }
  showDdlStandard();
}

elements.ddlGenerateButton.addEventListener("click", startDdlStandard);
elements.nextDdlButton.addEventListener("click", () => selectFeature("ddl"));

elements.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(elements.form);
  clearHandoff();
  elements.errorText.textContent = "";
  showProcessing();
  elements.progressBar.value = 0;
  elements.progressPercent.textContent = "0%";
  elements.statusText.textContent = "Mengunggah file...";

  try {
    const response = await fetch("/api/v1/audit/spreadsheet", {
      method: "POST",
      body: formData,
    });
    if (!response.ok) throw new Error(await responseDetail(response));
    const job = await response.json();
    sessionStorage.setItem(PENDING_STATUS_KEY, job.status_url);
    checkStatus(job.status_url);
  } catch (error) {
    elements.errorText.textContent = error.message;
    showRetry();
  }
});

elements.fileInput.addEventListener("change", () => {
  const selectedFile = elements.fileInput.files[0];
  elements.fileName.textContent = selectedFile?.name || "Format .sql atau .ddl";
  elements.filePrompt.textContent = selectedFile ? "File siap dianalisis" : "Pilih file dari perangkat";
  elements.fileAction.textContent = selectedFile ? "Ganti file" : "Jelajahi";
  elements.uploadArea.classList.toggle("has-file", Boolean(selectedFile));
  elements.errorText.textContent = "";
  elements.downloadLink.hidden = true;
  elements.progressBox.hidden = true;
  elements.completedActions.hidden = true;
  elements.submitButton.hidden = false;
  elements.submitButton.disabled = false;
  clearHandoff();
});

elements.nextProcessButton.addEventListener("click", async () => {
  elements.nextProcessButton.disabled = true;
  const originalText = elements.nextProcessButton.firstChild;
  originalText.textContent = "Menyiapkan proses berikutnya";
  await selectFeature("dictionary");
  originalText.textContent = "Lanjut ke Data Dictionary";
  elements.nextProcessButton.disabled = false;
});

elements.resultsRetry.addEventListener("click", () => loadAuditResults(state.findingsUrl));
elements.classifyButton.addEventListener("click", startClassification);
elements.oldDictionaryButton.addEventListener("click", startOldDictionary);
elements.newDictionaryButton.addEventListener("click", startNewDictionary);
elements.logPerubahanButton.addEventListener("click", startLogPerubahan);
elements.dictionarySheetTabs.forEach((tab, index) => {
  tab.addEventListener("click", () => selectDictionarySheet(tab.dataset.dictionarySheet));
  tab.addEventListener("keydown", (event) => {
    const tabs = elements.dictionarySheetTabs;
    let nextIndex;
    if (event.key === "ArrowRight") nextIndex = (index + 1) % tabs.length;
    if (event.key === "ArrowLeft") nextIndex = (index - 1 + tabs.length) % tabs.length;
    if (event.key === "Home") nextIndex = 0;
    if (event.key === "End") nextIndex = tabs.length - 1;
    if (nextIndex === undefined) return;
    event.preventDefault();
    tabs[nextIndex].focus();
    selectDictionarySheet(tabs[nextIndex].dataset.dictionarySheet);
  });
});
elements.ddlSheetTabs.forEach((tab, index) => {
  tab.addEventListener("click", () => selectDdlSheet(tab.dataset.ddlSheet));
  tab.addEventListener("keydown", (event) => {
    const tabs = elements.ddlSheetTabs;
    let nextIndex;
    if (event.key === "ArrowRight") nextIndex = (index + 1) % tabs.length;
    if (event.key === "ArrowLeft") nextIndex = (index - 1 + tabs.length) % tabs.length;
    if (event.key === "Home") nextIndex = 0;
    if (event.key === "End") nextIndex = tabs.length - 1;
    if (nextIndex === undefined) return;
    event.preventDefault();
    tabs[nextIndex].focus();
    selectDdlSheet(tabs[nextIndex].dataset.ddlSheet);
  });
});

elements.featureButtons.forEach((button) => {
  button.addEventListener("click", () => selectFeature(button.dataset.feature));
});

sessionStorage.removeItem("auditDatabaseHandoff");
const pendingUrl = statusUrlFromUrl || sessionStorage.getItem(PENDING_STATUS_KEY);
if (pendingUrl) {
  sessionStorage.setItem(PENDING_STATUS_KEY, pendingUrl);
  showProcessing();
  checkStatus(pendingUrl);
}
