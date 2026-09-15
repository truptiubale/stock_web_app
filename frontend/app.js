// frontend/app.js
// Calls the FastAPI backend at localhost:8000 and renders the response.
// No build step, no framework - plain fetch + DOM updates.

const API_BASE = "http://localhost:8000";

const refreshBtn = document.getElementById("refreshBtn");
const statusRow = document.getElementById("statusRow");
const resultsBody = document.getElementById("resultsBody");
const biasValue = document.getElementById("biasValue");

refreshBtn.addEventListener("click", runScreen);

async function runScreen() {
  setLoading(true);
  statusRow.textContent = "Fetching data from Yahoo Finance — this can take 10-20 seconds...";
  resultsBody.innerHTML = "";

  try {
    const response = await fetch(`${API_BASE}/api/screener`);
    if (!response.ok) {
      throw new Error(`Server responded with ${response.status}`);
    }
    const data = await response.json();
    renderResults(data);
  } catch (err) {
    statusRow.textContent =
      `Couldn't reach the backend. Is it running? Start it with: ` +
      `uvicorn backend.api:app --reload --port 8000  (error: ${err.message})`;
  } finally {
    setLoading(false);
  }
}

function setLoading(isLoading) {
  refreshBtn.disabled = isLoading;
  refreshBtn.textContent = isLoading ? "Running..." : "Run screen";
}

function renderResults(data) {
  if (!data.results || data.results.length === 0) {
    statusRow.textContent = "No results returned. Check ticker symbols in config.py and your internet connection.";
    biasValue.textContent = "—";
    biasValue.className = "bias-value";
    return;
  }

  statusRow.textContent = `${data.results.length} sector(s) screened.`;

  biasValue.textContent = data.bias || "—";
  biasValue.className = "bias-value " + (data.bias === "bullish" ? "bullish" : data.bias === "bearish" ? "bearish" : "");

  resultsBody.innerHTML = data.results.map(rowToHtml).join("");
}

function rowToHtml(row) {
  const pctClass = row.pct_change >= 0 ? "pct-positive" : "pct-negative";
  const pctSign = row.pct_change >= 0 ? "+" : "";
  const alignedClass = row.timeframe_aligned ? "bool-true" : "bool-false";
  const volumeClass = row.volume_confirmed ? "bool-true" : "bool-false";
  const verdictClass = "verdict-pill verdict-" + (row.verdict || "insufficient_data");

  return `
    <tr>
      <td>${escapeHtml(row.name)}</td>
      <td class="numeric ${pctClass}">${pctSign}${row.pct_change}%</td>
      <td class="${alignedClass}">${row.timeframe_aligned ? "Yes" : "No"}</td>
      <td class="numeric">${row.rsi ?? "—"}</td>
      <td>${escapeHtml(row.bollinger_status || "—")}</td>
      <td class="${volumeClass}">${row.volume_confirmed ? "Yes" : "No"}</td>
      <td><span class="${verdictClass}">${escapeHtml((row.verdict || "").replaceAll("_", " "))}</span></td>
    </tr>
  `;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}
