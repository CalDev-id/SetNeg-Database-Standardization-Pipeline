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
  auditProcessLogToggle: document.getElementById("auditProcessLogToggle"),
  auditProcessLog: document.getElementById("auditProcessLog"),
  auditRetryButton: document.getElementById("auditRetryButton"),
  errorText: document.getElementById("error"),
  downloadLink: document.getElementById("downloadLink"),
  completedActions: document.getElementById("completedActions"),
  auditWorkspace: document.getElementById("auditWorkspace"),
  normalizationInputs: document.getElementById("normalizationInputs"),
  normalizationStartButton: document.getElementById("normalizationStartButton"),
  normalizationError: document.getElementById("normalizationError"),
  normalizationResults: document.getElementById("normalizationResults"),
  normalizationNoFindings: document.getElementById("normalizationNoFindings"),
  normalizationSheetHint: document.getElementById("normalizationSheetHint"),
  normalizationSheet: document.getElementById("normalizationSheet"),
  normalizationBody: document.getElementById("normalizationBody"),
  resultSheetTabs: document.querySelectorAll("[data-result-sheet]"),
  auditResultPanel: document.getElementById("auditResultPanel"),
  auditResults: document.getElementById("auditResults"),
  resultsLoading: document.getElementById("resultsLoading"),
  resultsError: document.getElementById("resultsError"),
  resultsRetry: document.getElementById("resultsRetry"),
  resultsContent: document.getElementById("resultsContent"),
  resultTableCount: document.getElementById("resultTableCount"),
  resultColumnCount: document.getElementById("resultColumnCount"),
  resultFindingCount: document.getElementById("resultFindingCount"),
  resultFindingLabel: document.getElementById("resultFindingLabel"),
  auditFindingCount: document.getElementById("auditFindingCount"),
  normalizationFindingCount: document.getElementById("normalizationFindingCount"),
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
  dictionaryCurrentStageDuration: document.getElementById("dictionaryCurrentStageDuration"),
  dictionaryTimeLabel: document.getElementById("dictionaryTimeLabel"),
  dictionaryElapsed: document.getElementById("dictionaryElapsed"),
  dictionaryProcessHint: document.getElementById("dictionaryProcessHint"),
  dictionaryProcessLogToggle: document.getElementById("dictionaryProcessLogToggle"),
  dictionaryProcessLog: document.getElementById("dictionaryProcessLog"),
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
  ddlProcessLogToggle: document.getElementById("ddlProcessLogToggle"),
  ddlProcessLog: document.getElementById("ddlProcessLog"),
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
const COMPLETED_AUDIT_KEY = "auditDatabaseCompletedStatusUrl";
const NORMALIZATION_STATUS_KEY = "normalizationStatusUrl";
const WORKFLOW_SESSION_KEY = "databaseWorkflowSession";
const EXCEL_FILENAME = "temuan_audit_normalisasi.xlsx";
const FINDING_COLUMNS = [
  "no", "nama_database", "nama_tabel", "objek_temuan", "aturan_playbook",
  "uraian_ketidaksesuaian", "solusi", "status", "catatan", "jenis_temuan",
];
const JOB_ID_PATTERN = /^[0-9a-f]{32}$/;
const DICTIONARY_STAGE_NAMES = ["classification", "old", "new", "log"];
const DICTIONARY_STAGE_LABELS = {
  classification: "Klasifikasi tabel",
  old: "Dictionary Old",
  new: "Dictionary New",
  log: "Log Perubahan",
};
const DICTIONARY_FAILURE_MESSAGES = {
  classification: "Klasifikasi gagal.",
  old: "Dictionary Old gagal.",
  new: "Dictionary New gagal.",
  log: "Log Perubahan gagal.",
};
const statusJobId = new URLSearchParams(location.search).get("job_id");
const statusUrlFromUrl = JOB_ID_PATTERN.test(statusJobId || "")
  ? `/api/v1/audit/spreadsheet/${statusJobId}`
  : null;
const resetWorkflowOnLoad = globalThis.__resetWorkflowOnLoad === true;

function createDictionaryStages() {
  return Object.fromEntries(DICTIONARY_STAGE_NAMES.map((name) => [name, {
    status: "idle", completed: 0, total: 1, error: null, elapsedSeconds: 0, startedAt: null,
  }]));
}

const state = {
  elapsedStartedAt: null,
  elapsedTimer: null,
  auditProgress: { status: "idle", completed: 0, total: 1 },
  auditEvents: [],
  normalizationStatus: "idle",
  handoff: null,
  auditJobId: null,
  normalizationTrackingUrl: null,
  normalizationIgnoredJobIds: new Set(),
  normalizationStarting: false,
  nextProcessInputs: null,
  activeFeature: "audit",
  resultsAvailable: false,
  activeResultSheet: "audit",
  resultCounts: { audit: 0, normalization: 0 },
  auditRequestId: 0,
  findingsUrl: null,
  normalizationJobId: null,
  normalizationReady: false,
  normalizationRequestId: 0,
  resultsRequestId: 0,
  classificationRequestId: 0,
  classificationJobId: null,
  classificationReady: false,
  dictionaryStages: createDictionaryStages(),
  dictionaryActiveStages: new Set(),
  dictionaryEvents: [],
  dictionaryElapsedMs: 0,
  dictionaryTickStartedAt: null,
  dictionaryTimer: null,
  oldDictionaryRequestId: 0,
  oldDictionaryJobId: null,
  oldDictionaryReady: false,
  newDictionaryRequestId: 0,
  newDictionaryJobId: null,
  newDictionaryRetryJobId: null,
  newDictionaryReady: false,
  logPerubahanRequestId: 0,
  logPerubahanJobId: null,
  logPerubahanRequested: false,
  ddlRequestId: 0,
  ddlJobId: null,
  ddlRunning: false,
  ddlElapsedStartedAt: null,
  ddlElapsedTimer: null,
  ddlProcessEvents: [],
  ddlPastEvents: [],
  activeDictionarySheet: "old",
  activeDdlSheet: "alter",
  savedWorkflow: null,
  restoringWorkflow: false,
  workflowRestoreStarted: false,
};

function saveWorkflowSession() {
  if (state.restoringWorkflow) return;
  const auditJobId = state.auditJobId || state.handoff?.auditJobId;
  if (!auditJobId) {
    sessionStorage.removeItem(WORKFLOW_SESSION_KEY);
    return;
  }
  sessionStorage.setItem(WORKFLOW_SESSION_KEY, JSON.stringify({
    auditJobId,
    model: elements.modelSelect.value,
    feature: state.activeFeature,
    resultSheet: state.activeResultSheet,
    dictionarySheet: state.activeDictionarySheet,
    ddlSheet: state.activeDdlSheet,
    dictionaryElapsedMs: state.dictionaryElapsedMs +
      (state.dictionaryTickStartedAt === null ? 0 : Date.now() - state.dictionaryTickStartedAt),
    dictionaryEvents: state.dictionaryEvents,
    ddlPastEvents: state.ddlPastEvents,
    classificationJobId: state.classificationJobId,
    oldDictionaryJobId: state.oldDictionaryJobId,
    newDictionaryJobId: state.newDictionaryJobId,
    logPerubahanJobId: state.logPerubahanJobId,
    ddlJobId: state.ddlJobId,
  }));
}

function readWorkflowSession(auditJobId) {
  try {
    const saved = JSON.parse(sessionStorage.getItem(WORKFLOW_SESSION_KEY));
    return saved?.auditJobId === auditJobId ? saved : null;
  } catch {
    return null;
  }
}

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
    if (!elements.auditProcessLog.hidden) renderAuditProcessLog();
  };
  updateElapsed();
  state.elapsedTimer = setInterval(updateElapsed, 1000);
}

function stopElapsed() {
  if (state.elapsedStartedAt !== null && state.elapsedTimer !== null) {
    elements.elapsedTime.textContent = formatElapsed(
      Math.floor((Date.now() - state.elapsedStartedAt) / 1000),
    );
  }
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
    if (!elements.ddlProcessLog.hidden) renderDdlProcessLog();
  };
  update();
  state.ddlElapsedTimer = setInterval(update, 1000);
}

function stopDdlElapsed(finalSeconds = null) {
  clearInterval(state.ddlElapsedTimer);
  state.ddlElapsedTimer = null;
  if (finalSeconds !== null) elements.ddlElapsed.textContent = formatElapsed(finalSeconds);
}

function renderDdlProcessLog() {
  const entries = [];
  const active = new Map();
  for (const event of [...state.ddlPastEvents, ...state.ddlProcessEvents]) {
    const step = event.step === "alter" ? "ALTER" : "CREATE";
    const elapsed = Number(event.elapsed_seconds) || 0;
    if (event.kind === "retry") {
      const reason = String(event.message || "").trim();
      entries.push({ kind: "retry", label: `Mengulang DDL ${step}${reason ? `: ${reason.slice(0, 90)}` : ""}`,
        start: elapsed, end: elapsed });
      continue;
    }
    if (event.kind === "started") {
      const entry = { kind: "started", label: `DDL ${step}`, start: elapsed };
      entries.push(entry);
      active.set(step, entry);
      continue;
    }
    if (event.kind === "completed" || event.kind === "failed") {
      const entry = active.get(step) || { start: elapsed, label: `DDL ${step}` };
      if (!active.has(step)) entries.push(entry);
      entry.kind = event.kind;
      entry.end = elapsed;
      entry.label = event.kind === "completed" ? `DDL ${step} selesai`
        : `DDL ${step} gagal: ${String(event.message || "periksa log server").slice(0, 120)}`;
      active.delete(step);
    }
  }
  const rows = document.createDocumentFragment();
  if (!entries.length) {
    const row = document.createElement("li");
    row.textContent = "Menunggu DDL dimulai.";
    rows.append(row);
  }
  const currentElapsed = state.ddlElapsedStartedAt === null ? 0
    : Math.max(0, Math.floor((Date.now() - state.ddlElapsedStartedAt) / 1000));
  for (const entry of entries) {
    const row = document.createElement("li");
    if (["completed", "failed", "retry"].includes(entry.kind)) row.classList.add(`is-${entry.kind}`);
    row.textContent = `${formatElapsed(Math.max(0, (entry.end ?? currentElapsed) - entry.start))} · ${entry.label}`;
    rows.append(row);
  }
  elements.ddlProcessLog.replaceChildren(rows);
}

function updateDdlProcessLog(events) {
  if (!Array.isArray(events)) return;
  state.ddlProcessEvents = events;
  renderDdlProcessLog();
}

function toggleDdlProcessLog() {
  const open = elements.ddlProcessLog.hidden;
  elements.ddlProcessLog.hidden = !open;
  elements.ddlProcessLogToggle.setAttribute("aria-expanded", String(open));
  if (open) renderDdlProcessLog();
}

function updateDictionaryElapsed() {
  const runningMs = state.dictionaryTickStartedAt === null
    ? 0 : Date.now() - state.dictionaryTickStartedAt;
  elements.dictionaryElapsed.textContent = formatElapsed(
    Math.floor((state.dictionaryElapsedMs + runningMs) / 1000),
  );
  renderDictionaryProcessLog();
  saveWorkflowSession();
}

function dictionaryProgressUnit(name) {
  return name === "classification" ? "tabel" : name === "old" ? "objek" : "batch";
}

function dictionaryFailureReason(detail) {
  const text = String(detail || "").toLowerCase();
  if (text.includes("checkpoint") && text.includes("kedaluwarsa")) return "Checkpoint sudah kedaluwarsa; unggah ulang file.";
  if (text.includes("kedaluwarsa") || text.includes("tidak ditemukan")) return "Sesi sumber sudah habis; unggah ulang file.";
  if (text.includes("input atau model berubah")) return "Input atau prompt berubah; checkpoint lama tidak cocok.";
  if (text.includes("model berubah")) return "Pilih model semula untuk melanjutkan batch.";
  if (text.includes("checkpoint")) return "Checkpoint tidak tersedia untuk sesi ini.";
  if (text.includes("batas token")) return "Batas token respons LLM tercapai.";
  if (text.includes("respons kosong")) return "Layanan LLM mengembalikan respons kosong.";
  if (text.includes("membatasi jumlah permintaan")) return "Layanan LLM membatasi jumlah permintaan.";
  if (text.includes("layanan llm sedang bermasalah")) return "Layanan LLM sedang bermasalah.";
  if (text.includes("failed to fetch") || text.includes("network")) return "Koneksi ke server terputus.";
  if (text.includes("timeout") || text.includes("batas waktu")) return "Batas waktu layanan terlewati.";
  if (text.includes("koneksi")) return "Koneksi ke layanan LLM gagal.";
  if (text.includes("kesalahan internal")) return "Kesalahan internal saat memproses batch.";
  if (text.includes("struktur respons")) return "Output LLM tidak sesuai struktur yang diperlukan.";
  if (/(json|format|kolom|tabel|valid)/.test(text)) return "Output LLM tidak sesuai struktur yang diperlukan.";
  return "Respons LLM atau layanan tidak dapat diproses; detail tersedia pada log server.";
}

function dictionarySessionExpired(detail) {
  return /(tidak ditemukan|kedaluwarsa)/i.test(String(detail || ""));
}

function addDictionaryEvent(stage, kind, message, details = {}) {
  const previous = state.dictionaryEvents[state.dictionaryEvents.length - 1];
  if (previous?.stage === stage && previous.message === message) return;
  state.dictionaryEvents.push({ stage, kind, message, ...details });
  if (state.dictionaryEvents.length > 500) state.dictionaryEvents.shift();
  renderDictionaryProcessLog();
}

function updateDictionaryStage(name, status, completed = 0, total = 1, error = null,
                               elapsedSeconds = null, failureDetail = null) {
  const previous = state.dictionaryStages[name];
  const active = ["queued", "running"].includes(status);
  const terminal = ["completed", "failed"].includes(status);
  const restarted = active && !["queued", "running"].includes(previous.status);
  const startedAt = active
    ? restarted ? Date.now() : previous.startedAt || Date.now()
    : previous.startedAt;
  const measuredSeconds = startedAt === null ? 0 : Math.floor((Date.now() - startedAt) / 1000);
  const next = {
    status,
    completed: Number.isFinite(completed) ? completed : 0,
    total: Number.isFinite(total) ? Math.max(1, total) : 1,
    error,
    elapsedSeconds: restarted ? 0 : Number.isFinite(elapsedSeconds)
      ? Math.max(0, elapsedSeconds)
      : terminal ? Math.max(previous.elapsedSeconds || 0, measuredSeconds) : previous.elapsedSeconds || 0,
    startedAt,
  };
  state.dictionaryStages[name] = next;
  const unit = dictionaryProgressUnit(name);
  const details = { completed: next.completed, total: next.total,
    elapsedSeconds: stageElapsedSeconds(next) };
  if (restarted) {
    addDictionaryEvent(name, "started", `${DICTIONARY_STAGE_LABELS[name]} dimulai.`, details);
  } else if (active && next.completed > previous.completed) {
    addDictionaryEvent(name, "progress", `${DICTIONARY_STAGE_LABELS[name]} ${next.completed}/${next.total} ${unit}.`, details);
  } else if (terminal && status !== previous.status) {
    if (status === "completed") {
      addDictionaryEvent(name, "completed", `${DICTIONARY_STAGE_LABELS[name]} selesai.`, details);
    } else {
      const failedAt = Math.min(next.total, Math.max(1, next.completed + 1));
      addDictionaryEvent(name, "failed", `${DICTIONARY_STAGE_LABELS[name]} ${unit} ${failedAt}/${next.total} gagal: ${dictionaryFailureReason(failureDetail || error)}`, details);
    }
  }
  renderDictionaryProgress();
}

function failDictionaryStage(name, detail = null) {
  const { completed, total } = state.dictionaryStages[name];
  updateDictionaryStage(name, "failed", completed, total, DICTIONARY_FAILURE_MESSAGES[name], null, detail);
}

function stageElapsedSeconds(stage) {
  if (!["queued", "running"].includes(stage.status) || stage.startedAt === null) {
    return stage.elapsedSeconds || 0;
  }
  return Math.max(stage.elapsedSeconds || 0, Math.floor((Date.now() - stage.startedAt) / 1000));
}

function renderDictionaryProcessLog() {
  const entries = [];
  const active = new Map();
  for (const event of state.dictionaryEvents) {
    if (event.kind === "retry") {
      const batch = event.message.match(/batch (\d+) dari (\d+)/)?.slice(1).join("/");
      entries.push({ kind: "retry", label: batch ? `Mengulang Dictionary New batch ${batch}` : event.message,
        seconds: 0 });
      continue;
    }
    if (event.kind === "started") {
      active.set(event.stage, { completed: event.completed || 0, total: event.total || 1,
        lastSeconds: 0 });
      continue;
    }
    const entry = active.get(event.stage);
    if (!entry) continue;
    if (Number.isFinite(event.completed)) entry.completed = event.completed;
    if (Number.isFinite(event.total)) entry.total = event.total;
    const elapsed = Number.isFinite(event.elapsedSeconds) ? event.elapsedSeconds : 0;
    const duration = Math.max(0, elapsed - entry.lastSeconds);
    if (event.kind === "progress") {
      entries.push({ kind: "completed", label: `${DICTIONARY_STAGE_LABELS[event.stage]} ${entry.completed}/${entry.total} ${dictionaryProgressUnit(event.stage)} selesai`,
        seconds: duration });
      entry.lastSeconds = elapsed;
      continue;
    }
    if (event.kind === "completed" || event.kind === "failed") {
      const label = event.kind === "completed" ? `${DICTIONARY_STAGE_LABELS[event.stage]} selesai`
        : `${DICTIONARY_STAGE_LABELS[event.stage]} ${Math.min(entry.total, entry.completed + 1)}/${entry.total} ${dictionaryProgressUnit(event.stage)} gagal: ${event.message.split("gagal:").at(-1).trim()}`;
      entries.push({ kind: event.kind, label, seconds: duration });
      active.delete(event.stage);
    }
  }
  for (const [stage, entry] of active) {
    entries.push({ kind: "started", stage,
      label: `${DICTIONARY_STAGE_LABELS[stage]} ${Math.min(entry.total, entry.completed + 1)}/${entry.total} ${dictionaryProgressUnit(stage)}`,
      lastSeconds: entry.lastSeconds });
  }
  const rows = document.createDocumentFragment();
  if (!entries.length) {
    const row = document.createElement("li");
    row.textContent = "Belum ada proses yang dijalankan.";
    rows.append(row);
  } else {
    for (const entry of entries) {
      const row = document.createElement("li");
      if (["completed", "failed", "retry"].includes(entry.kind)) row.classList.add(`is-${entry.kind}`);
      const seconds = entry.kind === "started"
        ? Math.max(0, stageElapsedSeconds(state.dictionaryStages[entry.stage]) - entry.lastSeconds)
        : entry.seconds || 0;
      row.textContent = `${formatElapsed(seconds)} · ${entry.label}`;
      rows.append(row);
    }
  }
  elements.dictionaryProcessLog.replaceChildren(rows);
}

function toggleDictionaryProcessLog() {
  const open = elements.dictionaryProcessLog.hidden;
  elements.dictionaryProcessLog.hidden = !open;
  elements.dictionaryProcessLogToggle.setAttribute("aria-expanded", String(open));
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
  const current = failed || [...DICTIONARY_STAGE_NAMES].reverse().find((name) =>
    ["queued", "running"].includes(stages[name].status),
  );
  elements.dictionaryCurrentStageDuration.textContent = current
    ? formatElapsed(stageElapsedSeconds(stages[current])) : formatElapsed(
      Math.floor(state.dictionaryElapsedMs / 1000),
    );
  elements.dictionaryTimeLabel.textContent = complete ? "Durasi proses" : "Waktu berjalan";
  elements.dictionaryProgressBox.classList.toggle("is-error", Boolean(failed));
  elements.dictionaryProgressBox.classList.toggle("is-complete", complete);
  elements.dictionaryProcessHint.textContent = "";
  if (failed) {
    elements.dictionaryStatusText.textContent = stages[failed].error;
  } else if (complete) {
    elements.dictionaryStatusText.textContent = "Data Dictionary selesai";
  } else if (stages.log.status !== "idle") {
    elements.dictionaryStatusText.textContent = "Log Perubahan · Tahap 3/3";
  } else if (stages.new.status !== "idle") {
    elements.dictionaryStatusText.textContent = "Dictionary New · Tahap 2/3";
  } else {
    elements.dictionaryStatusText.textContent = "Klasifikasi · Tahap 1/3";
  }
}

function resetDictionaryProgress() {
  clearInterval(state.dictionaryTimer);
  state.dictionaryTimer = null;
  state.dictionaryActiveStages.clear();
  state.dictionaryElapsedMs = 0;
  state.dictionaryTickStartedAt = null;
  state.dictionaryStages = createDictionaryStages();
  state.dictionaryEvents = [];
  elements.dictionaryElapsed.textContent = "00:00";
  elements.dictionaryTimeLabel.textContent = "Waktu berjalan";
  elements.dictionaryProgressBar.value = 0;
  elements.dictionaryProgressPercent.textContent = "0%";
  elements.dictionaryStatusText.textContent = "";
  elements.dictionaryProcessHint.textContent = "";
  elements.dictionaryCurrentStageDuration.textContent = "00:00";
  elements.dictionaryProcessLog.hidden = true;
  elements.dictionaryProcessLogToggle.setAttribute("aria-expanded", "false");
  renderDictionaryProcessLog();
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

function clearExpiredAuditTracking() {
  clearTracking();
  sessionStorage.removeItem(COMPLETED_AUDIT_KEY);
  sessionStorage.removeItem(NORMALIZATION_STATUS_KEY);
  sessionStorage.removeItem(WORKFLOW_SESSION_KEY);
  state.savedWorkflow = null;
  state.restoringWorkflow = false;
  state.normalizationRequestId += 1;
  state.normalizationTrackingUrl = null;
  state.normalizationJobId = null;
  state.normalizationReady = false;
  state.normalizationStatus = "idle";
  elements.auditRetryButton.hidden = true;
}

function clearHandoff() {
  state.auditRequestId += 1;
  stopElapsed();
  state.auditProgress = { status: "idle", completed: 0, total: 1 };
  state.auditEvents = [];
  elements.auditProcessLog.hidden = true;
  elements.auditProcessLogToggle.setAttribute("aria-expanded", "false");
  renderAuditProcessLog();
  elements.elapsedTime.textContent = "00:00";
  sessionStorage.removeItem(COMPLETED_AUDIT_KEY);
  sessionStorage.removeItem(NORMALIZATION_STATUS_KEY);
  sessionStorage.removeItem(PENDING_STATUS_KEY);
  state.handoff = null;
  state.auditJobId = null;
  state.normalizationTrackingUrl = null;
  state.normalizationIgnoredJobIds.clear();
  state.normalizationStarting = false;
  state.nextProcessInputs = null;
  elements.dictionaryLoading.hidden = true;
  elements.dictionaryError.textContent = "";
  elements.completedActions.hidden = true;
  elements.nextProcessButton.hidden = true;
  elements.auditRetryButton.hidden = true;
  elements.auditRetryButton.disabled = false;
  clearAuditResults();
  clearNormalization();
  clearClassification();
  state.savedWorkflow = null;
  state.restoringWorkflow = false;
  state.workflowRestoreStarted = false;
  sessionStorage.removeItem(WORKFLOW_SESSION_KEY);
}

function clearNormalization() {
  state.normalizationRequestId += 1;
  state.normalizationJobId = null;
  state.normalizationReady = false;
  state.normalizationStatus = "idle";
  elements.normalizationInputs.hidden = true;
  elements.normalizationStartButton.hidden = true;
  elements.normalizationStartButton.disabled = false;
  elements.normalizationStartButton.textContent = "Coba lagi Normalisasi";
  elements.normalizationBody.replaceChildren();
  elements.normalizationError.textContent = "";
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
  saveWorkflowSession();
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
  saveWorkflowSession();
}

function clearNewDictionary() {
  clearDdlStandard();
  state.newDictionaryRequestId += 1;
  state.newDictionaryJobId = null;
  state.newDictionaryRetryJobId = null;
  state.newDictionaryReady = false;
  updateDdlReadiness();
  clearLogPerubahan();
  elements.newDictionaryButton.disabled = false;
  elements.newDictionaryButton.hidden = true;
  elements.newDictionaryButton.textContent = "Coba Lagi";
  elements.newDictionarySetup.hidden = false;
  elements.dictionaryNewEmpty.textContent = "Dictionary New menunggu hasil klasifikasi tabel.";
  elements.newDictionaryTable.hidden = true;
  elements.newDictionaryBody.replaceChildren();
  saveWorkflowSession();
}

function clearLogPerubahan() {
  if (state.dictionaryActiveStages.has("log")) setDictionaryStageRunning("log", false);
  state.logPerubahanRequestId += 1;
  state.logPerubahanJobId = null;
  state.logPerubahanRequested = false;
  elements.dictionaryLogSetup.hidden = false;
  elements.dictionaryLogEmpty.textContent = "Log Perubahan akan disusun setelah Dictionary New selesai.";
  elements.logPerubahanButton.disabled = true;
  elements.logPerubahanButton.hidden = true;
  elements.logPerubahanButton.textContent = "Coba lagi Log Perubahan";
  updateDictionaryStage("log", "idle");
  elements.dictionaryLogTable.hidden = true;
  elements.dictionaryLogBody.replaceChildren();
  saveWorkflowSession();
}

function clearDdlStandard() {
  stopDdlElapsed(0);
  state.ddlRequestId += 1;
  state.ddlJobId = null;
  state.ddlRunning = false;
  state.ddlProcessEvents = [];
  state.ddlPastEvents = [];
  elements.ddlProcessLog.hidden = true;
  elements.ddlProcessLogToggle.setAttribute("aria-expanded", "false");
  renderDdlProcessLog();
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
  saveWorkflowSession();
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
  state.activeDictionarySheet = sheetName;
  elements.dictionarySheetTabs.forEach((tab) => {
    const selected = tab.dataset.dictionarySheet === sheetName;
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
  });
  for (const [name, panel] of Object.entries(elements.dictionarySheetPanels)) {
    panel.hidden = name !== sheetName;
  }
  saveWorkflowSession();
}

function selectDdlSheet(sheetName) {
  state.activeDdlSheet = sheetName;
  elements.ddlSheetTabs.forEach((tab) => {
    const selected = tab.dataset.ddlSheet === sheetName;
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
  });
  for (const [name, panel] of Object.entries(elements.ddlSheetPanels)) {
    panel.hidden = name !== sheetName;
  }
  saveWorkflowSession();
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
  elements.normalizationBody.replaceChildren();
  state.resultCounts = { audit: 0, normalization: 0 };
  elements.auditFindingCount.textContent = "0";
  elements.normalizationFindingCount.textContent = "0";
  selectResultSheet("audit");
}

function saveHandoff(job) {
  if (!job.job_id || !job.source_filename) return;

  state.handoff = {
    auditJobId: job.job_id,
    sourceFilename: job.source_filename,
  };
  state.auditJobId = job.job_id;
  saveWorkflowSession();
  showCombinedResultIfReady();
}

function showProcessing() {
  elements.progressBox.classList.remove("is-complete", "is-error");
  elements.completionMeta.hidden = true;
  state.auditProgress.status = "queued";
  elements.submitButton.hidden = true;
  elements.submitButton.disabled = true;
  elements.fileInput.disabled = true;
  elements.modelSelect.disabled = true;
  elements.progressBox.hidden = false;
  elements.downloadLink.hidden = true;
  elements.nextProcessButton.hidden = true;
  elements.auditRetryButton.hidden = true;
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

function renderAuditProcessLog() {
  const entries = [];
  const active = new Map();
  for (const event of state.auditEvents) {
    const elapsed = Number(event.elapsed_seconds) || 0;
    const message = String(event.message || "");
    if (event.stage === "audit") {
      const batch = message.match(/^Audit batch (\d+\/\d+(?:, bagian \d+\/\d+)?)/i)?.[1];
      if (!batch) {
        if (event.kind === "failed" && !entries.some((entry) => entry.kind === "failed" && entry.stage === "audit")) {
          entries.push({ stage: "audit", kind: "failed", start: elapsed, end: elapsed, label: "Audit gagal." });
        }
        continue;
      }
      const key = `audit:${batch}`;
      if (event.kind === "started") {
        const entry = { stage: "audit", kind: "started", start: elapsed, label: `Audit batch ${batch}` };
        entries.push(entry);
        active.set(key, entry);
      } else if (event.kind === "retry") {
        const start = active.get(key)?.start ?? elapsed;
        const detail = message.includes("penalaran dikurangi") ? "penalaran dikurangi, mengulang"
          : message.includes("batas token ditambah") ? "batas token ditambah, mengulang"
          : message.includes(": mencoba lagi") ? "mengulang batch gagal"
          : message.includes("respons kosong") ? "respons kosong, mengulang"
          : message.includes("timeout") ? "timeout GPT Setneg, mengulang per bagian"
          : message.includes("respons tidak valid") && message.includes("dipecah")
            ? "respons tidak valid, mengulang per bagian"
          : message.includes("dipecah") ? "dipecah, mengulang per bagian"
          : message.includes("diperbaiki") ? "respons diperbaiki"
            : "respons tidak valid, mengulang";
        entries.push({ stage: "audit", kind: "retry", start, end: elapsed,
          label: `Audit batch ${batch}: ${detail}.` });
      } else if (event.kind === "failed" || event.kind === "completed") {
        const entry = active.get(key) || { stage: "audit", start: elapsed, label: `Audit batch ${batch}` };
        if (!active.has(key)) entries.push(entry);
        entry.kind = event.kind;
        entry.end = elapsed;
        if (event.kind === "failed") {
          const reason = message.split("gagal:").slice(1).join("gagal:").trim().slice(0, 120);
          entry.label = `Audit batch ${batch} gagal${reason ? `: ${reason}` : "."}`;
        } else {
          entry.label = `Audit batch ${batch} selesai.`;
        }
        active.delete(key);
      }
      continue;
    }
    if (event.stage !== "normalization" || event.kind === "queued") continue;
    if (event.kind === "retry") {
      entries.push({ stage: "normalization", kind: "retry", start: elapsed, end: elapsed,
        label: "Mengulang Normalisasi." });
    } else if (event.kind === "started") {
      const entry = { stage: "normalization", kind: "started", start: elapsed, label: "Normalisasi" };
      entries.push(entry);
      active.set("normalization", entry);
    } else if (event.kind === "completed" || event.kind === "failed") {
      const entry = active.get("normalization") || { stage: "normalization", start: elapsed };
      if (!active.has("normalization")) entries.push(entry);
      entry.kind = event.kind;
      entry.end = elapsed;
      if (event.kind === "failed") {
        const reason = message.split("gagal:").slice(1).join("gagal:").trim().slice(0, 120);
        entry.label = `Normalisasi gagal${reason ? `: ${reason}` : "."}`;
      } else {
        const findings = message.match(/\d+ temuan/)?.[0];
        entry.label = `Normalisasi selesai${findings ? ` · ${findings}` : ""}.`;
      }
      active.delete("normalization");
    }
  }
  const rows = document.createDocumentFragment();
  if (!entries.length) {
    const row = document.createElement("li");
    row.textContent = "Menunggu proses dimulai.";
    rows.append(row);
  }
  const currentElapsed = state.elapsedStartedAt === null ? 0
    : Math.max(0, Math.floor((Date.now() - state.elapsedStartedAt) / 1000));
  for (const entry of entries) {
    const row = document.createElement("li");
    if (["completed", "failed", "retry"].includes(entry.kind)) row.classList.add(`is-${entry.kind}`);
    const seconds = Math.max(0, (entry.end ?? currentElapsed) - entry.start);
    row.textContent = `${formatElapsed(seconds)} · ${entry.label}`;
    rows.append(row);
  }
  elements.auditProcessLog.replaceChildren(rows);
}

function updateAuditProcessLog(events) {
  if (!Array.isArray(events) || events.length < state.auditEvents.length) return;
  state.auditEvents = events;
  renderAuditProcessLog();
}

function toggleAuditProcessLog() {
  const open = elements.auditProcessLog.hidden;
  elements.auditProcessLog.hidden = !open;
  elements.auditProcessLogToggle.setAttribute("aria-expanded", String(open));
  if (open) renderAuditProcessLog();
}

function updateCombinedProgress() {
  const { status, completed, total } = state.auditProgress;
  const auditTotal = Math.max(1, total);
  const activeBatch = Math.min(auditTotal, completed + 1);
  const auditDone = status === "completed" ? auditTotal : Math.min(auditTotal, completed);
  const allDone = status === "completed" && state.normalizationReady;
  elements.progressBar.max = auditTotal + 1;
  elements.progressBar.value = auditDone + (state.normalizationReady ? 1 : 0);
  elements.progressPercent.textContent = `${Math.round(
    100 * elements.progressBar.value / elements.progressBar.max,
  )}%`;
  elements.progressBox.classList.toggle("is-complete", allDone);
  elements.completionMeta.hidden = !allDone;
  if (allDone) {
    stopElapsed();
    elements.statusText.textContent = "Audit dan Normalisasi selesai. Hasil siap ditinjau.";
    elements.completionMeta.textContent = `Durasi proses: ${elements.elapsedTime.textContent}`;
    return;
  }
  if (status === "completed" && state.normalizationStatus === "failed") {
    stopElapsed();
    elements.statusText.textContent = "Normalisasi gagal · Coba lagi";
  } else if (state.normalizationStatus === "failed") {
    elements.statusText.textContent = status === "running"
      ? `Audit ${activeBatch}/${auditTotal} · Normalisasi gagal`
      : "Normalisasi gagal · Audit menunggu";
  } else if (status === "completed") {
    elements.statusText.textContent = state.normalizationStatus === "queued"
      ? "Audit selesai · Normalisasi antre" : "Audit selesai · Normalisasi berjalan";
  } else if (state.normalizationReady) {
    elements.statusText.textContent = `Audit ${activeBatch}/${auditTotal} · Normalisasi selesai`;
  } else if (status === "queued" || status === "idle") {
    elements.statusText.textContent = "Menunggu Audit & Normalisasi";
  } else {
    elements.statusText.textContent = `Audit ${activeBatch}/${auditTotal} · Normalisasi ${state.normalizationStatus === "queued" ? "antre" : "aktif"}`;
  }
}

function updateProgress(job) {
  updateAuditProcessLog(job.process_events);
  state.auditProgress = {
    status: job.status,
    completed: job.completed_batches || 0,
    total: job.total_batches || 1,
  };
  startElapsed(job.elapsed_seconds || 0);
  updateCombinedProgress();
}

function finishAudit(job) {
  clearTracking();
  elements.downloadLink.hidden = true;
  elements.fileInput.disabled = false;
  elements.modelSelect.disabled = false;
  saveHandoff(job);
  sessionStorage.setItem(COMPLETED_AUDIT_KEY, `/api/v1/audit/spreadsheet/${job.job_id}`);
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

function selectResultSheet(sheet) {
  state.activeResultSheet = sheet;
  elements.resultSheetTabs.forEach((tab) => {
    const selected = tab.dataset.resultSheet === sheet;
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
  });
  elements.auditResultPanel.hidden = sheet !== "audit";
  elements.normalizationResults.hidden = sheet !== "normalization";
  elements.resultFindingCount.textContent = state.resultCounts[sheet];
  elements.resultFindingLabel.textContent = sheet === "audit"
    ? "Temuan Audit Playbook" : "Temuan Normalisasi";
  saveWorkflowSession();
}

function renderCombinedResults(result) {
  const findings = result.display_findings || result.findings;
  const auditRows = findings.filter((finding) => finding.jenis_temuan === "Audit Playbook");
  const normalizationRows = findings.filter((finding) => finding.jenis_temuan === "Normalisasi");
  elements.resultTableCount.textContent = result.summary.table_count;
  elements.resultColumnCount.textContent = result.summary.column_count;
  state.resultCounts = { audit: auditRows.length, normalization: normalizationRows.length };
  elements.auditFindingCount.textContent = auditRows.length;
  elements.normalizationFindingCount.textContent = normalizationRows.length;
  selectResultSheet(state.activeResultSheet);
  elements.noFindings.textContent = result.display_findings
    ? "Hasil Audit Playbook belum tersedia." : "Tidak ada temuan Audit Playbook.";
  elements.noFindings.hidden = auditRows.length !== 0;
  elements.sheetHint.hidden = auditRows.length === 0;
  elements.sheetViewport.hidden = auditRows.length === 0;
  elements.normalizationNoFindings.hidden = normalizationRows.length !== 0;
  elements.normalizationSheetHint.hidden = normalizationRows.length === 0;
  elements.normalizationSheet.hidden = normalizationRows.length === 0;
  const auditFragment = document.createDocumentFragment();
  const normalizationFragment = document.createDocumentFragment();
  for (const finding of auditRows) auditFragment.append(renderFinding(finding));
  for (const finding of normalizationRows) normalizationFragment.append(renderFinding(finding));
  elements.findingsBody.replaceChildren(auditFragment);
  elements.normalizationBody.replaceChildren(normalizationFragment);
  elements.resultsLoading.hidden = true;
  elements.resultsContent.hidden = false;
}

async function loadCombinedResults(url) {
  state.findingsUrl = url;
  state.resultsAvailable = true;
  const requestId = ++state.resultsRequestId;
  elements.auditResults.hidden = state.activeFeature !== "audit";
  elements.resultsLoading.hidden = false;
  elements.resultsContent.hidden = true;
  elements.resultsError.textContent = "";
  elements.resultsRetry.hidden = true;

  try {
    if (!url) throw new Error("Hasil analisis tidak tersedia.");
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) throw new Error(await responseDetail(response));
    const result = await response.json();
    if (requestId !== state.resultsRequestId) return;
    renderCombinedResults(result);
  } catch (error) {
    if (requestId !== state.resultsRequestId) return;
    elements.resultsLoading.hidden = true;
    elements.resultsError.textContent = `Temuan gabungan belum bisa ditampilkan: ${error.message}`;
    elements.resultsRetry.hidden = !url;
  }
}

async function checkStatus(statusUrl, requestId = state.auditRequestId) {
  let response;
  try {
    response = await fetch(statusUrl, { cache: "no-store" });
  } catch {
    if (requestId !== state.auditRequestId) return;
    elements.statusText.textContent = "Koneksi terputus. Mencoba lagi...";
    setTimeout(() => checkStatus(statusUrl, requestId), 3000);
    return;
  }

  if (requestId !== state.auditRequestId) return;

  if (response.status === 404) {
    clearExpiredAuditTracking();
    elements.errorText.textContent = "Proses tidak ditemukan. Server mungkin telah direstart; unggah ulang file.";
    showRetry();
    return;
  }
  if (!response.ok) {
    elements.statusText.textContent = "Status belum bisa dibaca. Mencoba lagi...";
    setTimeout(() => checkStatus(statusUrl, requestId), 3000);
    return;
  }

  let job;
  try {
    job = await response.json();
  } catch {
    elements.statusText.textContent = "Status belum bisa dibaca. Mencoba lagi...";
    setTimeout(() => checkStatus(statusUrl, requestId), 3000);
    return;
  }

  if (requestId !== state.auditRequestId) return;
  observeAuditJob(job);
  updateProgress(job);
  if (job.status === "completed") {
    finishAudit(job);
    return;
  }
  if (job.status === "failed") {
    elements.errorText.textContent = job.retry_available
      ? "Audit tidak selesai. Tekan Coba Lagi untuk melanjutkan batch yang gagal."
      : "Audit tidak selesai. Unggah ulang file untuk memulai lagi.";
    showRetry();
    elements.progressBox.hidden = false;
    elements.progressBox.classList.add("is-error");
    elements.statusText.textContent = "Audit tidak selesai.";
    elements.auditRetryButton.hidden = !job.retry_available;
    return;
  }

  setTimeout(() => checkStatus(statusUrl, requestId), 3000);
}

async function retryAudit() {
  const jobId = state.auditJobId;
  if (!jobId) return;
  elements.auditRetryButton.disabled = true;
  elements.errorText.textContent = "";
  try {
    const response = await fetch(`/api/v1/audit/spreadsheet/${jobId}/retry`, { method: "POST" });
    if (!response.ok) throw new Error(await responseDetail(response));
    const job = await response.json();
    if (state.auditJobId !== jobId) return;
    const requestId = ++state.auditRequestId;
    showProcessing();
    sessionStorage.setItem(PENDING_STATUS_KEY, job.status_url);
    checkStatus(job.status_url, requestId);
  } catch (error) {
    if (state.auditJobId !== jobId) return;
    elements.auditRetryButton.disabled = false;
    elements.errorText.textContent = `Audit belum dapat dilanjutkan: ${error.message}`;
  }
}

function loadNextProcessInputs() {
  if (!state.handoff || !state.normalizationReady) {
    throw new Error("Selesaikan Audit & Normalisasi Database terlebih dahulu.");
  }
  if (state.nextProcessInputs) return state.nextProcessInputs;
  state.nextProcessInputs = {
    ddlFile: { name: state.handoff.sourceFilename },
    findingsFile: { name: EXCEL_FILENAME },
  };
  return state.nextProcessInputs;
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

function showCombinedResultIfReady() {
  if (!state.handoff || !state.normalizationReady) return;
  const jobId = state.handoff.auditJobId;
  updateCombinedProgress();
  elements.downloadLink.href = `/api/v1/audit/spreadsheet/${jobId}/download/combined`;
  elements.downloadLink.hidden = false;
  elements.completedActions.hidden = false;
  elements.nextProcessButton.hidden = false;
  const findingsUrl = `/api/v1/audit/spreadsheet/${jobId}/combined-findings`;
  if (state.findingsUrl !== findingsUrl) loadCombinedResults(findingsUrl);
  loadNextProcessInputs();
  if (state.savedWorkflow && !state.workflowRestoreStarted) restoreWorkflowJobs();
}

async function restoreWorkflowJobs() {
  const saved = state.savedWorkflow;
  if (!saved || state.workflowRestoreStarted || saved.auditJobId !== state.handoff?.auditJobId) return;
  state.workflowRestoreStarted = true;
  const validId = (value) => JOB_ID_PATTERN.test(value || "") ? value : null;
  state.classificationJobId = validId(saved.classificationJobId);
  state.oldDictionaryJobId = validId(saved.oldDictionaryJobId);
  state.newDictionaryJobId = validId(saved.newDictionaryJobId);
  state.logPerubahanJobId = validId(saved.logPerubahanJobId);
  if (Array.isArray(saved.dictionaryEvents)) {
    state.dictionaryEvents = saved.dictionaryEvents.filter((event) =>
      event && typeof event.stage === "string" && typeof event.kind === "string"
        && typeof event.message === "string",
    ).slice(-500);
    renderDictionaryProcessLog();
  }
  if (Array.isArray(saved.ddlPastEvents)) {
    state.ddlPastEvents = saved.ddlPastEvents.filter((event) =>
      event && typeof event.kind === "string" && typeof event.step === "string"
        && typeof event.message === "string",
    ).slice(-30);
  }
  state.ddlJobId = validId(saved.ddlJobId);
  state.logPerubahanRequested = Boolean(state.logPerubahanJobId);
  state.ddlRunning = Boolean(state.ddlJobId);

  if (["audit", "dictionary", "ddl"].includes(saved.feature)) {
    await selectFeature(saved.feature);
  }
  const jobs = [
    [state.classificationJobId, "classification", pollClassification, state.classificationRequestId],
    [state.oldDictionaryJobId, "old-dictionary", pollOldDictionary, state.oldDictionaryRequestId],
    [state.newDictionaryJobId, "new-dictionary", pollNewDictionary, state.newDictionaryRequestId],
    [state.logPerubahanJobId, "log-perubahan", pollLogPerubahan, state.logPerubahanRequestId],
  ];
  const requests = jobs.filter(([jobId]) => jobId).map(([jobId, path, poll, requestId]) => {
    const stage = path === "old-dictionary" ? "old" : path === "new-dictionary" ? "new"
      : path === "log-perubahan" ? "log" : "classification";
    setDictionaryStageRunning(stage, true);
    updateDictionaryStage(stage, "running");
    return poll(`/api/v1/data-dictionary/${path}/${jobId}`, requestId);
  });
  if (state.ddlJobId) {
    elements.ddlProgressBox.hidden = false;
    requests.push(pollDdlStandard(`/api/v1/ddl-standard/${state.ddlJobId}`, state.ddlRequestId));
  }
  await Promise.all(requests);
  if (state.savedWorkflow !== saved) return;
  state.restoringWorkflow = false;
  state.savedWorkflow = null;
  if (["audit", "normalization"].includes(saved.resultSheet)) selectResultSheet(saved.resultSheet);
  if (["old", "new", "log"].includes(saved.dictionarySheet)) selectDictionarySheet(saved.dictionarySheet);
  if (["alter", "create"].includes(saved.ddlSheet)) selectDdlSheet(saved.ddlSheet);
  saveWorkflowSession();

  if (state.classificationJobId && !state.oldDictionaryJobId) startOldDictionary();
  if (state.classificationReady && !state.newDictionaryJobId) startNewDictionary();
  startLogWhenReady();
}

function trackNormalization(statusUrl, jobId = null) {
  if (state.normalizationTrackingUrl === statusUrl) return;
  state.normalizationRequestId += 1;
  state.normalizationTrackingUrl = statusUrl;
  state.normalizationJobId = jobId || statusUrl.split("/").pop();
  sessionStorage.setItem(NORMALIZATION_STATUS_KEY, statusUrl);
  elements.normalizationInputs.hidden = false;
  elements.normalizationError.textContent = "";
  elements.normalizationStartButton.hidden = true;
  state.normalizationStatus = "queued";
  updateCombinedProgress();
  pollNormalization(statusUrl, state.normalizationRequestId);
}

function observeAuditJob(job) {
  if (!job.job_id) return;
  state.auditJobId = job.job_id;
  saveWorkflowSession();
  elements.normalizationInputs.hidden = false;
  if (job.normalization_status_url && !state.normalizationStarting
      && !state.normalizationIgnoredJobIds.has(job.normalization_job_id)) {
    trackNormalization(job.normalization_status_url, job.normalization_job_id);
  } else if (job.normalization_error && !state.normalizationTrackingUrl && !state.normalizationStarting) {
    state.normalizationStatus = "failed";
    elements.normalizationError.textContent = job.normalization_error;
    elements.normalizationStartButton.textContent = "Coba lagi Normalisasi";
    elements.normalizationStartButton.hidden = false;
    updateCombinedProgress();
  }
}

async function pollNormalization(statusUrl, requestId) {
  try {
    const response = await fetch(statusUrl, { cache: "no-store" });
    if (!response.ok) throw new Error(await responseDetail(response));
    const job = await response.json();
    if (requestId !== state.normalizationRequestId) return;
    if (job.audit_job_id !== (state.auditJobId || state.handoff?.auditJobId)) {
      throw new Error("Hasil normalisasi tidak berasal dari audit yang dipilih.");
    }
    state.normalizationStatus = job.status;
    updateAuditProcessLog(job.process_events);
    if (job.status === "completed") {
      state.normalizationJobId = job.job_id;
      state.normalizationReady = true;
      elements.normalizationStartButton.hidden = true;
      updateCombinedProgress();
      if (state.handoff) {
        showCombinedResultIfReady();
      } else if (job.findings_url) {
        if (!state.resultsAvailable) state.activeResultSheet = "normalization";
        loadCombinedResults(job.findings_url);
      }
      return;
    }
    if (job.status === "failed") throw new Error(job.error || "Normalisasi gagal diproses.");
    updateCombinedProgress();
    setTimeout(() => pollNormalization(statusUrl, requestId), 3000);
  } catch (error) {
    if (requestId !== state.normalizationRequestId) return;
    sessionStorage.removeItem(NORMALIZATION_STATUS_KEY);
    state.normalizationStatus = "failed";
    elements.normalizationError.textContent = `Normalisasi tidak selesai: ${error.message}`;
    elements.normalizationStartButton.textContent = "Coba lagi Normalisasi";
    elements.normalizationStartButton.hidden = false;
    elements.normalizationStartButton.disabled = false;
    updateCombinedProgress();
  }
}

async function startNormalization() {
  const auditJobId = state.auditJobId || state.handoff?.auditJobId;
  if (!auditJobId) return;
  state.savedWorkflow = null;
  state.restoringWorkflow = false;
  state.workflowRestoreStarted = false;
  if (state.normalizationJobId) state.normalizationIgnoredJobIds.add(state.normalizationJobId);
  clearClassification();
  clearAuditResults();
  elements.completedActions.hidden = true;
  elements.downloadLink.hidden = true;
  elements.nextProcessButton.hidden = true;
  state.nextProcessInputs = null;
  clearNormalization();
  state.normalizationStarting = true;
  sessionStorage.removeItem(NORMALIZATION_STATUS_KEY);
  const requestId = state.normalizationRequestId;
  elements.normalizationInputs.hidden = false;
  elements.normalizationStartButton.hidden = true;
  state.normalizationStatus = "queued";
  const [minutes, seconds] = elements.elapsedTime.textContent.split(":").map(Number);
  startElapsed(minutes * 60 + seconds);
  elements.progressBox.hidden = false;
  updateCombinedProgress();
  try {
    const response = await fetch("/api/v1/normalization", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ audit_job_id: auditJobId, model: elements.modelSelect.value }),
    });
    if (!response.ok) throw new Error(await responseDetail(response));
    const job = await response.json();
    if (requestId !== state.normalizationRequestId) return;
    state.normalizationStarting = false;
    trackNormalization(job.status_url, job.job_id);
  } catch (error) {
    if (requestId !== state.normalizationRequestId) return;
    state.normalizationStarting = false;
    state.normalizationStatus = "failed";
    elements.normalizationError.textContent = `Normalisasi tidak dapat dimulai: ${error.message}`;
    elements.normalizationStartButton.textContent = "Coba lagi Normalisasi";
    elements.normalizationStartButton.hidden = false;
    updateCombinedProgress();
  }
}

function restoreNormalization() {
  const statusUrl = sessionStorage.getItem(NORMALIZATION_STATUS_KEY);
  if (!/^\/api\/v1\/normalization\/[0-9a-f]{32}$/.test(statusUrl || "")) return;
  trackNormalization(statusUrl);
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
      updateDictionaryStage("classification", "completed", job.total_tables, job.total_tables, null,
        job.elapsed_seconds);
      elements.classifyButton.hidden = true;
      if (!state.restoringWorkflow && !state.newDictionaryJobId) startNewDictionary();
      setDictionaryStageRunning("classification", false);
      return;
    }
    if (job.status === "failed") {
      updateDictionaryStage("classification", "failed", job.completed_tables, job.total_tables,
        DICTIONARY_FAILURE_MESSAGES.classification, job.elapsed_seconds, job.error);
      throw new Error(job.error || "Klasifikasi gagal.");
    }
    updateDictionaryStage("classification", job.status, job.completed_tables, job.total_tables, null,
      job.elapsed_seconds);
    setTimeout(() => pollClassification(statusUrl, requestId), 3000);
  } catch (error) {
    if (requestId !== state.classificationRequestId) return;
    setDictionaryStageRunning("classification", false);
    failDictionaryStage("classification", error.message);
    elements.classifyButton.disabled = false;
  }
}

async function startClassification() {
  if (!state.handoff?.auditJobId || !state.normalizationReady) return;
  const rerunAll = state.classificationReady;
  if (rerunAll) resetDictionaryProgress();
  state.classificationJobId = null;
  state.classificationReady = false;
  saveWorkflowSession();
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
      body: JSON.stringify({ audit_job_id: state.handoff.auditJobId,
        normalization_job_id: state.normalizationJobId }),
    });
    if (!response.ok) throw new Error(await responseDetail(response));
    const job = await response.json();
    if (requestId === state.classificationRequestId) {
      state.classificationJobId = job.job_id;
      saveWorkflowSession();
      pollClassification(job.status_url, requestId);
    }
  } catch (error) {
    if (requestId !== state.classificationRequestId) return;
    setDictionaryStageRunning("classification", false);
    failDictionaryStage("classification", error.message);
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
  if (state.restoringWorkflow || !state.oldDictionaryReady || !state.newDictionaryReady
      || state.logPerubahanRequested || state.logPerubahanJobId) return;
  elements.logPerubahanButton.disabled = false;
  startLogPerubahan();
}

async function pollNewDictionary(statusUrl, requestId) {
  let savedBatches = 0;
  try {
    const response = await fetch(statusUrl, { cache: "no-store" });
    if (!response.ok) throw new Error(await responseDetail(response));
    const job = await response.json();
    if (requestId !== state.newDictionaryRequestId) return;
    if (job.status === "completed") {
      state.newDictionaryRetryJobId = null;
      renderNewDictionary(job.result);
      updateDictionaryStage("new", "completed", job.total_batches, job.total_batches, null,
        job.elapsed_seconds);
      startLogWhenReady();
      setDictionaryStageRunning("new", false);
      return;
    }
    if (job.status === "failed") {
      state.newDictionaryRetryJobId = state.newDictionaryJobId || statusUrl.split("/").pop();
      savedBatches = Number(job.saved_batches) || 0;
      updateDictionaryStage("new", "failed", job.completed_batches, job.total_batches,
        DICTIONARY_FAILURE_MESSAGES.new, job.elapsed_seconds, job.error_reason || job.error);
      throw new Error(job.error || "Dictionary New gagal.");
    }
    updateDictionaryStage("new", job.status, job.completed_batches, job.total_batches, null,
      job.elapsed_seconds);
    setTimeout(() => pollNewDictionary(statusUrl, requestId), 3000);
  } catch (error) {
    if (requestId !== state.newDictionaryRequestId) return;
    setDictionaryStageRunning("new", false);
    failDictionaryStage("new", error.message);
    const expired = dictionarySessionExpired(error.message);
    elements.dictionaryNewEmpty.textContent = expired
      ? "Sesi proses tidak tersedia. Unggah ulang file untuk memulai lagi."
      : savedBatches
      ? `${savedBatches} batch berhasil tersimpan. Lanjutkan dari batch yang gagal.`
      : "Dictionary New belum selesai. Coba lagi batch yang gagal.";
    elements.dictionaryProcessHint.textContent = savedBatches
      ? ` · ${savedBatches} batch tersimpan di server` : "";
    elements.newDictionaryButton.disabled = expired;
    elements.newDictionaryButton.hidden = expired;
    elements.newDictionaryButton.textContent = "Coba Lagi";
  }
}

async function startNewDictionary() {
  if (!state.handoff?.auditJobId || !state.normalizationReady
      || !state.classificationReady || !state.classificationJobId) return;
  clearDdlStandard();
  clearLogPerubahan();
  state.newDictionaryReady = false;
  saveWorkflowSession();
  updateDdlReadiness();
  if (state.newDictionaryRetryJobId) {
    const previous = state.dictionaryStages.new;
    addDictionaryEvent("new", "retry", `Dictionary New diulang · melanjutkan dari batch ${Math.min(previous.total, previous.completed + 1)} dari ${previous.total}.`);
  }
  const requestId = ++state.newDictionaryRequestId;
  setDictionaryStageRunning("new", true);
  const previousProgress = state.dictionaryStages.new;
  updateDictionaryStage("new", "running", previousProgress.completed, previousProgress.total);
  elements.newDictionaryButton.disabled = true;
  elements.newDictionaryButton.hidden = true;
  elements.dictionaryNewEmpty.textContent = "Dictionary New sedang disusun dari hasil audit.";
  try {
    const response = await fetch("/api/v1/data-dictionary/new-dictionary", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        audit_job_id: state.handoff.auditJobId,
        normalization_job_id: state.normalizationJobId,
        classification_job_id: state.classificationJobId,
        model: elements.modelSelect.value,
        ...(state.newDictionaryRetryJobId ? { retry_job_id: state.newDictionaryRetryJobId } : {}),
      }),
    });
    if (!response.ok) {
      throw new Error(await responseDetail(response));
    }
    const job = await response.json();
    if (requestId === state.newDictionaryRequestId) {
      state.newDictionaryJobId = job.job_id;
      state.newDictionaryRetryJobId = null;
      saveWorkflowSession();
      pollNewDictionary(job.status_url, requestId);
    }
  } catch (error) {
    if (requestId !== state.newDictionaryRequestId) return;
    setDictionaryStageRunning("new", false);
    failDictionaryStage("new", error.message);
    const expired = dictionarySessionExpired(error.message);
    elements.dictionaryNewEmpty.textContent = expired
      ? "Sesi proses tidak tersedia. Unggah ulang file untuk memulai lagi."
      : "Dictionary New belum selesai. Coba proses ulang.";
    elements.newDictionaryButton.disabled = expired;
    elements.newDictionaryButton.hidden = expired;
    elements.newDictionaryButton.textContent = "Coba Lagi";
  }
}

function renderLogPerubahan(result) {
  const rows = document.createDocumentFragment();
  for (const item of result.log_perubahan) {
    const row = document.createElement("tr");
    const number = document.createElement("th");
    number.scope = "row";
    number.textContent = item.no_baru == null ? "—" : String(item.no_baru);
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
      updateDictionaryStage("log", "completed", job.total_batches, job.total_batches, null,
        job.elapsed_seconds);
      setDictionaryStageRunning("log", false);
      return;
    }
    if (job.status === "failed") {
      updateDictionaryStage("log", "failed", job.completed_batches, job.total_batches,
        DICTIONARY_FAILURE_MESSAGES.log, job.elapsed_seconds, job.error);
      throw new Error(job.error || "Log Perubahan gagal.");
    }
    updateDictionaryStage("log", job.status, job.completed_batches, job.total_batches, null,
      job.elapsed_seconds);
    setTimeout(() => pollLogPerubahan(statusUrl, requestId), 3000);
  } catch (error) {
    if (requestId !== state.logPerubahanRequestId) return;
    setDictionaryStageRunning("log", false);
    failDictionaryStage("log", error.message);
    elements.dictionaryLogEmpty.textContent = "Log Perubahan belum selesai. Coba proses ulang.";
    elements.logPerubahanButton.disabled = false;
    elements.logPerubahanButton.hidden = false;
    elements.logPerubahanButton.textContent = "Coba lagi Log Perubahan";
  }
}

async function startLogPerubahan() {
  if (!state.handoff?.auditJobId || !state.normalizationReady
      || !state.oldDictionaryReady || !state.newDictionaryReady
      || !state.oldDictionaryJobId || !state.newDictionaryJobId
      || elements.logPerubahanButton.disabled) return;
  state.logPerubahanRequested = true;
  state.logPerubahanJobId = null;
  saveWorkflowSession();
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
        normalization_job_id: state.normalizationJobId,
        old_dictionary_job_id: state.oldDictionaryJobId,
        new_dictionary_job_id: state.newDictionaryJobId,
        model: elements.modelSelect.value,
      }),
    });
    if (!response.ok) throw new Error(await responseDetail(response));
    const job = await response.json();
    if (requestId === state.logPerubahanRequestId) {
      state.logPerubahanJobId = job.job_id;
      saveWorkflowSession();
      pollLogPerubahan(job.status_url, requestId);
    }
  } catch (error) {
    if (requestId !== state.logPerubahanRequestId) return;
    setDictionaryStageRunning("log", false);
    failDictionaryStage("log", error.message);
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
      updateDictionaryStage("old", "completed", job.total_objects, job.total_objects, null,
        job.elapsed_seconds);
      startLogWhenReady();
      setDictionaryStageRunning("old", false);
      return;
    }
    if (job.status === "failed") {
      updateDictionaryStage("old", "failed", job.completed_objects, job.total_objects,
        DICTIONARY_FAILURE_MESSAGES.old, job.elapsed_seconds, job.error);
      throw new Error(job.error || "Old Dictionary gagal.");
    }
    updateDictionaryStage("old", job.status, job.completed_objects, job.total_objects, null,
      job.elapsed_seconds);
    setTimeout(() => pollOldDictionary(statusUrl, requestId), 3000);
  } catch (error) {
    if (requestId !== state.oldDictionaryRequestId) return;
    setDictionaryStageRunning("old", false);
    failDictionaryStage("old", error.message);
    elements.oldDictionaryPending.textContent = "Dictionary Old belum selesai. Coba proses ulang.";
    elements.oldDictionaryButton.disabled = false;
    elements.oldDictionaryButton.hidden = false;
  }
}

async function startOldDictionary() {
  clearDdlStandard();
  if (!state.handoff?.auditJobId || !state.normalizationReady) return;
  state.oldDictionaryJobId = null;
  state.oldDictionaryReady = false;
  saveWorkflowSession();
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
      body: JSON.stringify({ audit_job_id: state.handoff.auditJobId,
        normalization_job_id: state.normalizationJobId, model: elements.modelSelect.value }),
    });
    if (!response.ok) throw new Error(await responseDetail(response));
    const job = await response.json();
    if (requestId === state.oldDictionaryRequestId) {
      state.oldDictionaryJobId = job.job_id;
      saveWorkflowSession();
      pollOldDictionary(job.status_url, requestId);
    }
  } catch (error) {
    if (requestId !== state.oldDictionaryRequestId) return;
    setDictionaryStageRunning("old", false);
    failDictionaryStage("old", error.message);
    elements.oldDictionaryButton.disabled = false;
    elements.oldDictionaryButton.hidden = false;
  }
}

function showDictionary() {
  showWorkspace("dictionary");
  if (!state.handoff || !state.normalizationReady) {
    elements.dictionaryEmpty.hidden = false;
    elements.dictionaryLoading.hidden = true;
    elements.dictionaryInputs.hidden = true;
    elements.dictionaryError.textContent = "";
    return;
  }

  elements.dictionaryEmpty.hidden = true;
  elements.dictionaryError.textContent = "";
  try {
    renderDictionaryInputs(loadNextProcessInputs());
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
    updateDdlProcessLog(job.process_events);
    if (job.status === "completed") {
      state.ddlRunning = false;
      stopDdlElapsed(job.elapsed_seconds || 0);
      elements.ddlProgressBox.classList.add("is-complete");
      elements.ddlProgressBox.hidden = false;
      elements.ddlProgressText.textContent = "DDL Standar selesai";
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
    elements.ddlProgressText.textContent = job.total_objects === 2
      ? (job.completed_objects ? "DDL ALTER" : "DDL CREATE") : "DDL Standar";
    startDdlElapsed(job.elapsed_seconds || 0);
    setTimeout(() => pollDdlStandard(statusUrl, requestId), 3000);
  } catch (error) {
    if (requestId !== state.ddlRequestId) return;
    state.ddlRunning = false;
    stopDdlElapsed();
    elements.ddlProgressBox.hidden = false;
    elements.ddlProgressBox.classList.add("is-error");
    elements.ddlProgressText.textContent = "DDL Standar gagal";
    elements.ddlError.textContent = "DDL Standar tidak selesai. Lihat detail proses.";
    elements.ddlGenerateButton.textContent = "Coba lagi";
    updateDdlReadiness();
  }
}

async function startDdlStandard() {
  if (!state.handoff?.auditJobId || !state.oldDictionaryReady || !state.newDictionaryReady) return;
  const requestId = ++state.ddlRequestId;
  if (state.ddlProcessEvents.some((event) => event.kind === "failed")) {
    const failed = state.ddlProcessEvents.filter((event) => event.kind === "failed").at(-1);
    state.ddlPastEvents.push(...state.ddlProcessEvents, {
      kind: "retry", step: failed.step, message: "", elapsed_seconds: 0,
    });
    state.ddlPastEvents = state.ddlPastEvents.slice(-30);
  }
  state.ddlProcessEvents = [];
  renderDdlProcessLog();
  state.ddlJobId = null;
  saveWorkflowSession();
  state.ddlRunning = true;
  elements.ddlGenerateButton.hidden = true;
  elements.ddlError.textContent = "";
  elements.ddlProgressBox.classList.remove("is-complete", "is-error");
  elements.ddlProgressBox.hidden = false;
  elements.ddlProgressText.textContent = "Menyiapkan DDL...";
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
    saveWorkflowSession();
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
  saveWorkflowSession();
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
  const requestId = state.auditRequestId;
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
    if (requestId !== state.auditRequestId) return;
    observeAuditJob(job);
    sessionStorage.setItem(PENDING_STATUS_KEY, job.status_url);
    checkStatus(job.status_url, requestId);
  } catch (error) {
    if (requestId !== state.auditRequestId) return;
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
elements.modelSelect.addEventListener("change", saveWorkflowSession);

elements.nextProcessButton.addEventListener("click", async () => {
  elements.nextProcessButton.disabled = true;
  const originalText = elements.nextProcessButton.firstChild;
  originalText.textContent = "Menyiapkan proses berikutnya";
  await selectFeature("dictionary");
  originalText.textContent = "Lanjut ke Data Dictionary";
  elements.nextProcessButton.disabled = false;
});

elements.normalizationStartButton.addEventListener("click", startNormalization);
elements.auditRetryButton.addEventListener("click", retryAudit);
elements.resultsRetry.addEventListener("click", () => loadCombinedResults(state.findingsUrl));
elements.resultSheetTabs.forEach((tab) => {
  tab.addEventListener("click", () => selectResultSheet(tab.dataset.resultSheet));
});
elements.classifyButton.addEventListener("click", startClassification);
elements.dictionaryProcessLogToggle.addEventListener("click", toggleDictionaryProcessLog);
elements.auditProcessLogToggle.addEventListener("click", toggleAuditProcessLog);
elements.ddlProcessLogToggle.addEventListener("click", toggleDdlProcessLog);
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
if (resetWorkflowOnLoad) {
  sessionStorage.removeItem(PENDING_STATUS_KEY);
  sessionStorage.removeItem(COMPLETED_AUDIT_KEY);
  sessionStorage.removeItem(NORMALIZATION_STATUS_KEY);
  sessionStorage.removeItem(WORKFLOW_SESSION_KEY);
  if (statusUrlFromUrl) history.replaceState(null, "", location.pathname);
}
const pendingUrl = resetWorkflowOnLoad ? null : (statusUrlFromUrl
  || sessionStorage.getItem(PENDING_STATUS_KEY)
  || sessionStorage.getItem(COMPLETED_AUDIT_KEY));
if (pendingUrl) {
  const auditId = pendingUrl.split("/").pop();
  state.savedWorkflow = readWorkflowSession(auditId);
  if (state.savedWorkflow) {
    state.restoringWorkflow = true;
    state.dictionaryElapsedMs = Math.max(0, Number(state.savedWorkflow.dictionaryElapsedMs) || 0);
    updateDictionaryElapsed();
    if (["telkom", "gemini", "gpt_setneg", "nutaraline"].includes(state.savedWorkflow.model)) {
      elements.modelSelect.value = state.savedWorkflow.model;
    }
  } else {
    sessionStorage.removeItem(WORKFLOW_SESSION_KEY);
  }
  if (JOB_ID_PATTERN.test(auditId || "")) state.auditJobId = auditId;
  sessionStorage.setItem(PENDING_STATUS_KEY, pendingUrl);
  showProcessing();
  restoreNormalization();
  checkStatus(pendingUrl);
} else {
  sessionStorage.removeItem(WORKFLOW_SESSION_KEY);
}
if (typeof globalThis.addEventListener === "function") {
  globalThis.addEventListener("pagehide", saveWorkflowSession);
}
