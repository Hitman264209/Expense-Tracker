const API = "/api/expenses";
let categoryChart = null;

const el = (id) => document.getElementById(id);

document.addEventListener("DOMContentLoaded", () => {
  el("date").valueAsDate = new Date();
  el("expenseForm").addEventListener("submit", onSubmit);
  el("filterCategory").addEventListener("change", refreshTable);
  refreshAll();
});

async function refreshAll() {
  await Promise.all([refreshTable(), refreshSummary()]);
}

async function onSubmit(e) {
  e.preventDefault();
  el("formError").textContent = "";

  const payload = {
    title: el("title").value,
    amount: parseFloat(el("amount").value),
    category: el("category").value,
    date: el("date").value,
    note: el("note").value || null,
  };

  try {
    const res = await fetch(API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Failed to add expense.");

    el("expenseForm").reset();
    el("date").valueAsDate = new Date();
    await refreshAll();
  } catch (err) {
    el("formError").textContent = err.message;
  }
}

async function deleteExpense(id) {
  await fetch(`${API}/${id}`, { method: "DELETE" });
  await refreshAll();
}

async function refreshTable() {
  const category = el("filterCategory").value;
  const url = category ? `${API}?category=${encodeURIComponent(category)}` : API;
  const res = await fetch(url);
  const data = await res.json();

  const tbody = el("expenseTableBody");
  tbody.innerHTML = "";

  if (data.expenses.length === 0) {
    el("emptyState").style.display = "block";
    el("expenseTable").style.display = "none";
    return;
  }
  el("emptyState").style.display = "none";
  el("expenseTable").style.display = "table";

  for (const exp of data.expenses) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${exp.date}</td>
      <td>${escapeHtml(exp.title)}</td>
      <td>${exp.category}</td>
      <td>${exp.note ? escapeHtml(exp.note) : "—"}</td>
      <td class="amount-cell">₹${exp.amount.toFixed(2)}</td>
      <td><button class="delete-btn" onclick="deleteExpense(${exp.id})">✕</button></td>
    `;
    tbody.appendChild(tr);
  }
}

async function refreshSummary() {
  const res = await fetch("/api/analytics/summary");
  const data = await res.json();

  el("totalSpent").textContent = `₹${data.total_spent.toFixed(2)}`;
  const totalCount = data.by_category.reduce((sum, c) => sum + c.count, 0);
  el("totalCount").textContent = totalCount;
  el("topCategory").textContent = data.by_category.length
    ? data.by_category[0].category
    : "–";

  renderChart(data.by_category);
}

function renderChart(byCategory) {
  const ctx = document.getElementById("categoryChart");
  const labels = byCategory.map((c) => c.category);
  const totals = byCategory.map((c) => c.total);

  if (categoryChart) categoryChart.destroy();

  categoryChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{
        data: totals,
        backgroundColor: [
          "#1f6f4a", "#2f9e6b", "#b1452e", "#d9a441",
          "#4a6f9e", "#7a5ca8", "#c46b8f", "#5c8a5c",
          "#a87f4a", "#6b6558",
        ],
        borderColor: "#f6f4ee",
        borderWidth: 2,
      }],
    },
    options: {
      plugins: {
        legend: { position: "bottom", labels: { font: { size: 11 } } },
      },
    },
  });
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}
