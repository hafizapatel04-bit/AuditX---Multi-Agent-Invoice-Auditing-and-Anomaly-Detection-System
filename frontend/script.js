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

// green = fine, red = problem, amber = needs a human
function tone(text) {
  const l = String(text ?? "").replace(/_/g, " ").toLowerCase();
  if (/no duplicate|not a duplicate|no anomal/.test(l)) return "green";
  if (/reject|fail|duplicate|flag|anomal|unapproved|not approved|blocked/.test(l)) return "red";
  if (/\b(approved|pass|passed|normal|clear|ok)\b/.test(l)) return "green";
  return "amber";
}

function label(text) {
  return String(text ?? "unknown").replace(/_/g, " ");
}

function badge(text) {
  return `<span class="badge ${tone(text)}">${esc(label(text))}</span>`;
}

function stamp(text) {
  return `<div class="stamp ${tone(text)}">${esc(label(text))}</div>`;
}

function toneColor(text) {
  const t = tone(text);
  return t === "green" ? "#1F6B52" : t === "red" ? "#B8352A" : "#D9A21B";
}

// ---------- Server connection light ----------
async function checkServer() {
  const box = $("conn");
  try {
    const res = await fetch(API_BASE + "/health");
    if (!res.ok) throw new Error("bad status");
    box.dataset.state = "up";
    $("connText").textContent = "Server connected";
  } catch (_) {
    box.dataset.state = "down";
    $("connText").textContent = "Server offline";
  }
}

// ---------- Totals and charts (calculated from the invoice list) ----------
let statusChart = null;
let categoryChart = null;

function countBy(items, getKey) {
  const counts = {};
  items.forEach((item) => {
    const key = label(getKey(item));
    counts[key] = (counts[key] || 0) + 1;
  });
  return counts;
}

function drawChart(existing, canvasId, counts, colors, horizontal) {
  if (typeof Chart === "undefined") return existing;   // chart library did not load
  if (existing) existing.destroy();
  Chart.defaults.font.family = '"Libre Franklin", "Segoe UI", sans-serif';
  Chart.defaults.color = "#5E6C79";
  const valueAxis = horizontal ? "x" : "y";
  const nameAxis = horizontal ? "y" : "x";
  return new Chart($(canvasId), {
    type: "bar",
    data: {
      labels: Object.keys(counts),
      datasets: [{ data: Object.values(counts), backgroundColor: colors, borderRadius: 2, maxBarThickness: 34 }],
    },
    options: {
      indexAxis: horizontal ? "y" : "x",
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        [valueAxis]: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: "#E3E8EC" } },
        [nameAxis]: { grid: { display: false } },
      },
    },
  });
}

function renderDashboard(invoices) {
  $("mTotal").textContent = invoices.length;
  $("mReview").textContent = invoices.filter((i) => /review/i.test(String(i.status))).length;
  $("mUnknown").textContent = invoices.filter((i) => i.vendor_name === "UNKNOWN").length;

  const empty = invoices.length === 0;
  document.querySelectorAll(".chart").forEach((f) => f.classList.toggle("empty", empty));
  if (empty) {
    if (statusChart) { statusChart.destroy(); statusChart = null; }
    if (categoryChart) { categoryChart.destroy(); categoryChart = null; }
    return;
  }

  const byStatus = countBy(invoices, (i) => i.status);
  const byCategory = countBy(invoices, (i) => i.category || "uncategorized");
  statusChart = drawChart(statusChart, "statusChart", byStatus, Object.keys(byStatus).map(toneColor), false);
  categoryChart = drawChart(categoryChart, "categoryChart", byCategory, "#34495C", true);
}

// ---------- Upload ----------
let selectedFile = null;
const dropZone = $("dropZone");

function setFile(file) {
  selectedFile = file || null;
  $("uploadBtn").disabled = !selectedFile;
  dropZone.classList.toggle("has-file", !!selectedFile);
  $("uploadStatus").className = "status";
  $("uploadStatus").textContent = selectedFile ? `Selected: ${selectedFile.name}` : "";
}

$("fileInput").addEventListener("change", (e) => setFile(e.target.files[0]));

["dragenter", "dragover"].forEach((ev) =>
  dropZone.addEventListener(ev, (e) => { e.preventDefault(); dropZone.classList.add("over"); })
);
["dragleave", "drop"].forEach((ev) =>
  dropZone.addEventListener(ev, (e) => { e.preventDefault(); dropZone.classList.remove("over"); })
);
dropZone.addEventListener("drop", (e) => {
  const file = e.dataTransfer.files[0];
  if (!file) return;
  if (!/\.(pdf|png|jpe?g)$/i.test(file.name)) {
    $("uploadStatus").className = "status error";
    $("uploadStatus").textContent = "Only PDF, PNG or JPG files can be uploaded.";
    return;
  }
  const transfer = new DataTransfer();
  transfer.items.add(file);
  $("fileInput").files = transfer.files;
  setFile(file);
});

$("uploadBtn").addEventListener("click", async () => {
  if (!selectedFile) return;
  const btn = $("uploadBtn");
  btn.disabled = true;
  btn.textContent = "Processing...";
  $("uploadStatus").className = "status";
  $("uploadStatus").textContent = "Reading the invoice. This can take a minute...";

  try {
    const form = new FormData();
    form.append("file", selectedFile);   // "file" must match the backend's parameter name
    const inv = await api("/upload-invoice", { method: "POST", body: form });

    $("fileInput").value = "";
    setFile(null);
    $("uploadStatus").className = "status ok";
    $("uploadStatus").textContent = inv.vendor_name === "UNKNOWN"
      ? "Uploaded, but the invoice could not be read. It is marked for manual review."
      : "Invoice processed.";

    await loadInvoices();
    showDetail(inv.id);
  } catch (err) {
    $("uploadStatus").className = "status error";
    $("uploadStatus").textContent = `Upload failed: ${err.message}`;
  } finally {
    btn.textContent = "Upload and analyze";
    btn.disabled = !selectedFile;
  }
});

// ---------- Invoice list ----------
let selectedId = null;

function markSelected() {
  document.querySelectorAll("#invoiceRows tr").forEach((tr) =>
    tr.classList.toggle("selected", String(tr.dataset.id) === String(selectedId))
  );
}

async function loadInvoices() {
  const rows = $("invoiceRows");
  const msg = $("listMessage");
  msg.className = "status pad";
  msg.textContent = "";
  try {
    const invoices = await api("/invoices");
    renderDashboard(invoices);
    if (invoices.length === 0) {
      rows.innerHTML = "";
      msg.textContent = "No invoices yet. Add one with the upload panel.";
      return;
    }
    rows.innerHTML = invoices.map((inv) => `
      <tr data-id="${inv.id}">
        <td>${inv.id}</td>
        <td>${esc(inv.invoice_number) || "-"}</td>
        <td>${esc(inv.vendor_name)}</td>
        <td>${esc(fmtDate(inv.invoice_date))}</td>
        <td class="num">${esc(money(inv.amount, inv.currency))}</td>
        <td>${badge(inv.status)}</td>
      </tr>`).join("");
    markSelected();
  } catch (err) {
    msg.className = "status pad error";
    msg.textContent = `Could not load invoices: ${err.message}`;
  }
}

$("invoiceRows").addEventListener("click", (e) => {
  const tr = e.target.closest("tr");
  if (tr) showDetail(tr.dataset.id);
});
$("refreshBtn").addEventListener("click", loadInvoices);

// ---------- Invoice details ----------
async function showDetail(id) {
  const card = $("detailCard");
  const body = $("detailBody");
  selectedId = id;
  markSelected();
  card.hidden = false;
  body.innerHTML = "<p class='muted'>Loading...</p>";
  const smooth = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  card.scrollIntoView({ behavior: smooth ? "smooth" : "auto", block: "start" });

  try {
    const inv = await api(`/invoice/${id}`);
    const items = (inv.line_items || []).map((li) => `
      <tr>
        <td>${esc(li.description)}</td>
        <td class="num">${li.quantity ?? ""}</td>
        <td class="num">${li.unit_price ?? ""}</td>
        <td class="num">${li.total ?? ""}</td>
      </tr>`).join("");

    const subtitle = inv.invoice_number
      ? `Invoice ${esc(inv.invoice_number)}, dated ${esc(fmtDate(inv.invoice_date))}`
      : "Invoice number not found";

    body.innerHTML = `
      <div class="detail-head">
        <div>
          <h3 class="doc-title">${esc(inv.vendor_name)}</h3>
          <p class="doc-sub">${subtitle}</p>
        </div>
        ${stamp(inv.status)}
      </div>
      <div class="grid">
        <div><span class="label">Invoice date</span>${esc(fmtDate(inv.invoice_date))}</div>
        <div><span class="label">Due date</span>${esc(fmtDate(inv.due_date))}</div>
        <div><span class="label">Category</span>${esc(inv.category) || "-"}</div>
        <div><span class="label">Subtotal</span>${esc(money(inv.subtotal, inv.currency))}</div>
        <div><span class="label">Tax</span>${esc(money(inv.tax_amount, inv.currency))}</div>
        <div><span class="label">Total</span><strong>${esc(money(inv.amount, inv.currency))}</strong></div>
      </div>
      ${items ? `
        <h3 class="section">Line items</h3>
        <div class="table-wrap"><table>
          <thead><tr><th>Description</th><th class="num">Qty</th><th class="num">Unit price</th><th class="num">Total</th></tr></thead>
          <tbody>${items}</tbody>
        </table></div>` : ""}
      <div id="auditBox"></div>`;

    loadAudit(id);
  } catch (err) {
    body.innerHTML = `<p class="status error">Could not load invoice: ${esc(err.message)}</p>`;
  }
}

// Starts working automatically once Person B adds GET /audit/{invoice_id}
async function loadAudit(id) {
  const box = $("auditBox");
  try {
    const a = await api(`/audit/${id}`);
    const reasons = (a.reasons || []).map((r) => `<li>${esc(r)}</li>`).join("");
    box.innerHTML = `
      <h3 class="section">Audit result</h3>
      <div class="checks">
        <div><span class="label">Vendor check</span>${badge(a.vendor_check)}</div>
        <div><span class="label">Policy check</span>${badge(a.policy_check)}</div>
        <div><span class="label">Duplicate check</span>${badge(a.duplicate_check)}</div>
        <div><span class="label">Anomaly score</span>${a.anomaly_score ?? "-"}</div>
        <div><span class="label">Final status</span>${badge(a.final_status)}</div>
      </div>
      ${reasons ? `<ul class="reasons">${reasons}</ul>` : ""}
      ${a.report ? `<h3 class="section">Audit report</h3><pre class="report">${esc(a.report)}</pre>` : ""}`;
  } catch (err) {
    box.innerHTML = err.status === 404
      ? `<p class="muted" style="margin-top:24px">No audit result for this invoice yet.</p>`
      : "";
  }
}

// ---------- Start ----------
checkServer();
setInterval(checkServer, 15000);
loadInvoices();