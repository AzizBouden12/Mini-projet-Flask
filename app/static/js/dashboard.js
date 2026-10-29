(function () {
  "use strict";
  if (!window.Chart || !window.STATS) return;

  var stats = window.STATS;
  var css = getComputedStyle(document.documentElement);
  var gridColor = "rgba(15,23,42,.07)";

  Chart.defaults.font.family = "'Fira Sans', system-ui, sans-serif";
  Chart.defaults.color = css.getPropertyValue("--c-muted").trim() || "#475569";
  Chart.defaults.animation = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? false : { duration: 500 };

  var COLORS = { blue: "#2563EB", red: "#DC2626", green: "#16A34A", slate: "#64748B" };

  var months = stats.loans_per_month;
  new Chart(document.getElementById("chart-months"), {
    type: "line",
    data: {
      labels: months.map(function (m) { return m.label; }),
      datasets: [
        { label: "Emprunts", data: months.map(function (m) { return m.borrowed; }), borderColor: COLORS.blue,
          backgroundColor: "rgba(37,99,235,.12)", fill: true, tension: .35, pointRadius: 4, pointHoverRadius: 6 },
        { label: "Retours", data: months.map(function (m) { return m.returned; }), borderColor: COLORS.green,
          backgroundColor: "transparent", borderDash: [6, 4], tension: .35, pointRadius: 4, pointStyle: "rectRot" }
      ]
    },
    options: {
      maintainAspectRatio: false, interaction: { mode: "index", intersect: false },
      plugins: { legend: { position: "bottom", labels: { usePointStyle: true } } },
      scales: { y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: gridColor } },
                x: { grid: { display: false } } }
    }
  });

  var s = stats.loans_by_status;
  new Chart(document.getElementById("chart-status"), {
    type: "doughnut",
    data: {
      labels: ["En cours", "En retard", "Rendus"],
      datasets: [{ data: [s.en_cours, s.en_retard, s.rendu], backgroundColor: [COLORS.blue, COLORS.red, COLORS.green],
                   borderColor: "#fff", borderWidth: 3 }]
    },
    options: { maintainAspectRatio: false, cutout: "68%", plugins: { legend: { display: false } } }
  });

  var cats = stats.categories;
  new Chart(document.getElementById("chart-categories"), {
    type: "bar",
    data: {
      labels: cats.map(function (c) { return c.name; }),
      datasets: [
        { label: "Livres", data: cats.map(function (c) { return c.books; }), backgroundColor: COLORS.slate, borderRadius: 4 },
        { label: "Emprunts", data: cats.map(function (c) { return c.loans; }),
          backgroundColor: cats.map(function (c) { return c.color; }), borderRadius: 4 }
      ]
    },
    options: {
      maintainAspectRatio: false,
      plugins: { legend: { position: "bottom" } },
      scales: { y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: gridColor } },
                x: { grid: { display: false } } }
    }
  });
})();
