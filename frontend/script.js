// Works from FastAPI (port 8000) or from the small dev server (port 5500).
const API_BASE = window.location.port === "8000" ? "" : "http://localhost:8000";

const $ = (id) => document.getElementById(id);

// Makes text safe to put inside HTML
function esc(value) {
    const div = document.createElement("div");
    div.textContent = value ?? "";
    return div.innerHTML;
}

// One place for all server calls, with readable errors
async function api(path, options) {
    let res;
    try {
        res = await fetch(API_BASE + path, options);
    } catch (e) {
        throw new Error("Cannot reach the server. Start the backend (uvicorn on port 8000) and try again.");
    }
    if (!res.ok) {
        let detail = res.statusText;
        try {
            const body = await res.json();
            detail = body.detail || detail;
            if (typeof detail !== "string") detail = JSON.stringify(detail);
        } catch (_) {}
        const err = new Error(`${detail} (${res.status})`);
        err.status = res.status;
        throw err;
    }
    return res.json();
}

// ---------- Theme ----------
function applyTheme(dark) {
    document.documentElement.classList.toggle("dark", dark);
    $("theme-icon").innerHTML = `<i data-lucide="${dark ? "sun" : "moon"}" class="w-4 h-4"></i>`;
    lucide.createIcons();
}

function toggleTheme() {
    const dark = !document.documentElement.classList.contains("dark");
    try { localStorage.setItem("auditx-theme", dark ? "dark" : "light"); } catch (_) {}
    applyTheme(dark);
}

// ---------- Tabs ----------
const NAV_ACTIVE = "w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium bg-indigo-600 text-white shadow-lg shadow-indigo-600/30 transition-all";
const NAV_IDLE = "w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 transition-all";
const TITLES = { dashboard: "Overview", upload: "New audit", agents: "How the audit works" };

function switchTab(name) {
    Object.keys(TITLES).forEach((t) => {
        $("tab-" + t).classList.toggle("hidden", t !== name);
        $("nav-" + t).className = t === name ? NAV_ACTIVE : NAV_IDLE;
    });
    $("header-title").textContent = TITLES[name];
}

// ---------- Formatting ----------
function money(amount, currency) {
    if (amount === null || amount === undefined) return "-";
    const n = Number(amount).toLocaleString("en-IN", { minimumFractionDigits: 2 });
    return `${currency || ""} ${n}`.trim();
}

function fmtDate(value) {
    if (!value) return "-";
    const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(value));
    if (!m) return String(value);
    const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
    return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

function fmtDateTime(value) {
    if (!value) return "-";
    const d = new Date(value);
    if (isNaN(d)) return "-";
    return d.toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

// green = fine, red = problem, amber = needs a person
function tone(text) {
    const l = String(text ?? "").replace(/_/g, " ").toLowerCase();
    if (/no duplicate|not a duplicate|no anomal/.test(l)) return "green";
    if (/reject|fail|duplicate|flag|anomal|unapproved|not approved|blocked/.test(l)) return "red";
    if (/\b(approved|pass|passed|normal|clear|ok)\b/.test(l)) return "green";
    return "amber";
}

const PILL = {
    green: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
    red: "bg-rose-500/10 text-rose-600 dark:text-rose-400",
    amber: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
};
const NOTE = {
    green: "bg-emerald-500/5 border-emerald-500/20 text-emerald-600 dark:text-emerald-400",
    red: "bg-rose-500/5 border-rose-500/20 text-rose-600 dark:text-rose-400",
    amber: "bg-amber-500/5 border-amber-500/20 text-amber-600 dark:text-amber-400",
};
const NOTE_ICON = { green: "check", red: "alert-triangle", amber: "info" };

function label(text) {
    return String(text ?? "unknown").replace(/_/g, " ");
}

function pill(text) {
    return `<span class="px-2.5 py-1 rounded-full text-xs font-semibold capitalize whitespace-nowrap ${PILL[tone(text)]}">${esc(label(text))}</span>`;
}

function noteRow(t, text) {
    return `<div class="p-3 border rounded-xl flex items-start gap-3 text-sm ${NOTE[t]}">
        <i data-lucide="${NOTE_ICON[t]}" class="w-4 h-4 mt-0.5 shrink-0"></i><span>${esc(text)}</span></div>`;
}

// ---------- Server status ----------
async function checkServer() {
    let up = false;
    try {
        const res = await fetch(API_BASE + "/health");
        up = res.ok;
    } catch (_) {}

    $("srv-line").className = "flex items-center gap-2 text-xs font-semibold mb-1 " + (up ? "text-emerald-500" : "text-rose-500");
    $("srv-dot").className = "w-2 h-2 rounded-full " + (up ? "bg-emerald-500" : "bg-rose-500");
    $("srv-text").textContent = up ? "Server connected" : "Server offline";
    $("srv-sub").textContent = up ? "The backend is responding" : "Start the backend on port 8000";

    $("agents-server-sub").textContent = up ? "The backend is responding." : "Cannot reach the backend on port 8000.";
    $("agents-server-pill").className = "px-2.5 py-1 rounded-full text-xs font-semibold " + (up ? PILL.green : PILL.red);
    $("agents-server-pill").textContent = up ? "Connected" : "Offline";
}

// ---------- Dashboard (real data from GET /invoices) ----------
async function loadDashboard() {
    const body = $("recent-body");
    const msg = $("recent-msg");
    msg.className = "text-sm text-slate-400 py-6 text-center";
    msg.textContent = "";

    try {
        const invoices = await api("/invoices");

        $("stat-total").textContent = invoices.length;
        $("stat-review").textContent = invoices.filter((i) => /review/i.test(String(i.status))).length;
        $("stat-unread").textContent = invoices.filter((i) => i.vendor_name === "UNKNOWN").length;
        $("stat-approved").textContent = invoices.filter((i) => tone(i.status) === "green").length;

        if (invoices.length === 0) {
            body.innerHTML = "";
            msg.textContent = "No invoices yet. Upload one from New Audit.";
            return;
        }

        body.innerHTML = invoices.slice(0, 10).map((inv) => `
            <tr class="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/40" onclick="openInvoice(${inv.id})">
                <td class="py-4 font-medium text-slate-900 dark:text-slate-200">${esc(inv.invoice_number) || "-"}</td>
                <td class="py-4">${esc(inv.vendor_name)}</td>
                <td class="py-4 tabular-nums">${esc(money(inv.amount, inv.currency))}</td>
                <td class="py-4">${pill(inv.status)}</td>
                <td class="py-4 text-slate-400">${esc(fmtDateTime(inv.created_at))}</td>
            </tr>`).join("");
    } catch (err) {
        ["stat-total", "stat-review", "stat-unread", "stat-approved"].forEach((id) => { $(id).textContent = "-"; });
        body.innerHTML = "";
        msg.className = "text-sm text-rose-500 py-6 text-center";
        msg.textContent = `Could not load invoices: ${err.message}`;
    }
}

function openInvoice(id) {
    switchTab("upload");
    showResult(id);
}

// ---------- Upload (real call to POST /upload-invoice) ----------
function setPanel(state) {
    ["placeholder", "loading", "result"].forEach((s) => {
        $("audit-" + s).classList.toggle("hidden", s !== state);
    });
}

function showError(message) {
    $("audit-result").innerHTML = `<div class="p-4 border rounded-xl flex items-start gap-3 text-sm ${NOTE.red}">
        <i data-lucide="alert-triangle" class="w-4 h-4 mt-0.5 shrink-0"></i><span>${esc(message)}</span></div>`;
    setPanel("result");
    lucide.createIcons();
}

async function uploadFile(file) {
    if (!file) return;
    if (!/\.(pdf|png|jpe?g)$/i.test(file.name)) {
        showError("Only PDF, PNG or JPG files can be uploaded.");
        return;
    }

    const selected = $("selected-file");
    selected.textContent = "Selected: " + file.name;
    selected.classList.remove("hidden");

    $("loading-text").textContent = "Reading the invoice. This can take up to a minute.";
    setPanel("loading");

    try {
        const form = new FormData();
        form.append("file", file);   // "file" must match the backend's parameter name
        const inv = await api("/upload-invoice", { method: "POST", body: form });
        await showResult(inv.id, inv);
        loadDashboard();
    } catch (err) {
        showError(`Upload failed: ${err.message}`);
    }
}

function handleFileUpload(event) {
    const file = event.target.files[0];
    event.target.value = "";   // lets the same file be chosen again
    uploadFile(file);
}

// Drag and drop
const dropZone = $("drop-zone");
["dragenter", "dragover"].forEach((ev) =>
    dropZone.addEventListener(ev, (e) => {
        e.preventDefault();
        dropZone.classList.add("border-indigo-500");
    })
);
["dragleave", "drop"].forEach((ev) =>
    dropZone.addEventListener(ev, (e) => {
        e.preventDefault();
        dropZone.classList.remove("border-indigo-500");
    })
);
dropZone.addEventListener("drop", (e) => uploadFile(e.dataTransfer.files[0]));

// ---------- Result panel: only facts that come from the server ----------
let currentId = null;

// Notes come straight from what was (or was not) extracted. Nothing is invented.
function extractionNotes(inv) {
    if (inv.vendor_name === "UNKNOWN") {
        return [["red", "The invoice could not be read, so no checks were run. It is marked for manual review."]];
    }
    const notes = [];
    if (!inv.invoice_number) notes.push(["amber", "No invoice number was found."]);
    if (!inv.invoice_date) notes.push(["amber", "No invoice date was found."]);
    if (inv.amount === null || inv.amount === undefined) notes.push(["amber", "No total amount was found."]);
    if (notes.length === 0) notes.push(["green", "Vendor, invoice number, date and total were all extracted."]);
    return notes;
}

async function showResult(id, known) {
    currentId = id;
    let inv = known;

    if (!inv) {
        $("loading-text").textContent = "Loading invoice...";
        setPanel("loading");
        try {
            inv = await api(`/invoice/${id}`);
        } catch (err) {
            showError(`Could not load the invoice: ${err.message}`);
            return;
        }
    }

    const items = inv.line_items || [];
    const itemsHtml = items.length ? `
        <details class="rounded-xl border border-slate-200 dark:border-slate-700/50">
            <summary class="cursor-pointer px-4 py-3 text-sm font-medium text-slate-700 dark:text-slate-300">Line items (${items.length})</summary>
            <div class="max-h-64 overflow-auto px-4 pb-3">
                <table class="w-full text-sm text-slate-600 dark:text-slate-300">
                    <thead class="text-xs text-slate-400"><tr>
                        <th class="text-left pb-2 font-semibold">Description</th>
                        <th class="text-right pb-2 font-semibold">Qty</th>
                        <th class="text-right pb-2 font-semibold">Total</th>
                    </tr></thead>
                    <tbody class="divide-y divide-slate-100 dark:divide-slate-800/60">
                        ${items.map((li) => `<tr>
                            <td class="py-2 pr-2">${esc(li.description)}</td>
                            <td class="py-2 text-right tabular-nums">${li.quantity ?? ""}</td>
                            <td class="py-2 text-right tabular-nums">${li.total ?? ""}</td>
                        </tr>`).join("")}
                    </tbody>
                </table>
            </div>
        </details>` : "";

    $("audit-result").innerHTML = `
        <div class="p-4 rounded-xl border border-slate-200 dark:border-slate-700/50 bg-slate-50 dark:bg-slate-800/50 flex items-start justify-between gap-4">
            <div class="min-w-0">
                <p class="text-xs text-slate-400">Invoice</p>
                <p class="font-bold text-slate-900 dark:text-slate-200 truncate">${esc(inv.invoice_number) || "Number not found"}</p>
                <p class="text-sm text-slate-500 dark:text-slate-400 truncate">${esc(inv.vendor_name)}</p>
            </div>
            ${pill(inv.status)}
        </div>

        <dl class="grid grid-cols-2 gap-4 text-sm">
            <div><dt class="text-xs text-slate-400">Total</dt><dd class="font-semibold text-slate-900 dark:text-slate-200">${esc(money(inv.amount, inv.currency))}</dd></div>
            <div><dt class="text-xs text-slate-400">Category</dt><dd class="font-semibold text-slate-900 dark:text-slate-200">${esc(inv.category) || "-"}</dd></div>
            <div><dt class="text-xs text-slate-400">Invoice date</dt><dd class="font-semibold text-slate-900 dark:text-slate-200">${esc(fmtDate(inv.invoice_date))}</dd></div>
            <div><dt class="text-xs text-slate-400">Due date</dt><dd class="font-semibold text-slate-900 dark:text-slate-200">${esc(fmtDate(inv.due_date))}</dd></div>
        </dl>

        <div class="space-y-3">
            <p class="text-sm font-semibold text-slate-700 dark:text-slate-300">Extraction notes</p>
            ${extractionNotes(inv).map(([t, text]) => noteRow(t, text)).join("")}
        </div>

        ${itemsHtml}
        <div id="audit-checks"></div>`;

    setPanel("result");
    lucide.createIcons();
    loadAudit(id);
}

// Fills in automatically once Person B adds GET /audit/{invoice_id}
async function loadAudit(id) {
    const box = $("audit-checks");
    try {
        const a = await api(`/audit/${id}`);
        if (id !== currentId) return;   // user already opened another invoice

        const check = (name, value) => `
            <div class="flex items-center justify-between py-2">
                <span class="text-sm text-slate-600 dark:text-slate-300">${name}</span>${pill(value ?? "not run")}
            </div>`;
        const reasons = (a.reasons || []).map((r) => `<li>${esc(r)}</li>`).join("");

        box.innerHTML = `
            <div class="space-y-3">
                <p class="text-sm font-semibold text-slate-700 dark:text-slate-300">Audit checks</p>
                <div class="divide-y divide-slate-100 dark:divide-slate-800/60">
                    ${check("Vendor check", a.vendor_check)}
                    ${check("Policy check", a.policy_check)}
                    ${check("Duplicate check", a.duplicate_check)}
                    <div class="flex items-center justify-between py-2">
                        <span class="text-sm text-slate-600 dark:text-slate-300">Anomaly score</span>
                        <span class="text-sm font-medium text-slate-900 dark:text-slate-200">${a.anomaly_score ?? "not run"}</span>
                    </div>
                    ${check("Final status", a.final_status)}
                </div>
                ${reasons ? `<ul class="list-disc pl-5 text-sm text-slate-600 dark:text-slate-300">${reasons}</ul>` : ""}
                ${a.report ? `<pre class="whitespace-pre-wrap text-xs leading-relaxed p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/50 text-slate-700 dark:text-slate-300 font-mono">${esc(a.report)}</pre>` : ""}
            </div>`;
    } catch (err) {
        if (id !== currentId) return;
        box.innerHTML = err.status === 404
            ? `<p class="text-sm text-slate-400">No audit result is available for this invoice yet.</p>`
            : "";
    }
}

// ---------- Start ----------
let savedTheme = null;
try { savedTheme = localStorage.getItem("auditx-theme"); } catch (_) {}
applyTheme(savedTheme === "dark");

checkServer();
setInterval(checkServer, 15000);
loadDashboard();