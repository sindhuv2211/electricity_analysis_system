// static/js/charts.js — Dark glowing Chart.js theme

// Global Chart.js defaults for dark theme
Chart.defaults.color = '#888';
Chart.defaults.borderColor = '#ffffff11';

const GLOW_COLORS = [
  '#00cfff', '#00ff88', '#ff4466', '#ffcc00',
  '#aa66ff', '#ff8800', '#00ffcc', '#ff66aa'
];

// Build rgba from hex for backgrounds
function hexAlpha(hex, alpha) {
  const r = parseInt(hex.slice(1,3),16);
  const g = parseInt(hex.slice(3,5),16);
  const b = parseInt(hex.slice(5,7),16);
  return `rgba(${r},${g},${b},${alpha})`;
}

/**
 * initCharts() — Line, Bar, Pie on dashboard
 */
function initCharts() {
  // ── Line Chart ──
  new Chart(document.getElementById('lineChart'), {
    type: 'line',
    data: {
      labels: lineLabels,
      datasets: [{
        label: 'Usage (kWh)',
        data: lineData,
        borderColor: '#00cfff',
        backgroundColor: hexAlpha('#00cfff', 0.08),
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointBackgroundColor: '#00cfff',
        pointBorderColor: '#00cfff',
        borderWidth: 2,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#111',
          borderColor: '#00cfff44',
          borderWidth: 1,
          titleColor: '#00cfff',
          bodyColor: '#ccc',
        }
      },
      scales: {
        x: { ticks: { color: '#666' }, grid: { color: '#ffffff0a' } },
        y: { ticks: { color: '#666' }, grid: { color: '#ffffff0a' } }
      }
    }
  });

  // ── Bar Chart ──
  new Chart(document.getElementById('barChart'), {
    type: 'bar',
    data: {
      labels: barLabels,
      datasets: [{
        label: 'Avg Usage (kWh)',
        data: barData,
        backgroundColor: barLabels.map((_, i) => hexAlpha(GLOW_COLORS[i % GLOW_COLORS.length], 0.5)),
        borderColor:     barLabels.map((_, i) => GLOW_COLORS[i % GLOW_COLORS.length]),
        borderWidth: 1,
        borderRadius: 6,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#111',
          borderColor: '#ffffff22',
          borderWidth: 1,
          titleColor: '#00cfff',
          bodyColor: '#ccc',
        }
      },
      scales: {
        x: { ticks: { color: '#666' }, grid: { color: '#ffffff0a' } },
        y: { ticks: { color: '#666' }, grid: { color: '#ffffff0a' } }
      }
    }
  });

  // ── Pie Chart ──
  new Chart(document.getElementById('pieChart'), {
    type: 'pie',
    data: {
      labels: pieLabels,
      datasets: [{
        data: pieData,
        backgroundColor: pieLabels.map((_, i) => hexAlpha(GLOW_COLORS[i % GLOW_COLORS.length], 0.6)),
        borderColor:     pieLabels.map((_, i) => GLOW_COLORS[i % GLOW_COLORS.length]),
        borderWidth: 1,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { labels: { color: '#aaa', padding: 14 } },
        tooltip: {
          backgroundColor: '#111',
          borderColor: '#ffffff22',
          borderWidth: 1,
          titleColor: '#00cfff',
          bodyColor: '#ccc',
        }
      }
    }
  });
}

/**
 * initTrendChart() — Monthly trend on analytics page
 */
function initTrendChart() {
  new Chart(document.getElementById('trendChart'), {
    type: 'line',
    data: {
      labels: trendLabels,
      datasets: [{
        label: 'Monthly Avg (kWh)',
        data: trendData,
        borderColor: '#00ff88',
        backgroundColor: hexAlpha('#00ff88', 0.08),
        fill: true,
        tension: 0.4,
        pointRadius: 5,
        pointBackgroundColor: '#00ff88',
        borderWidth: 2,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { labels: { color: '#aaa' } },
        tooltip: {
          backgroundColor: '#111',
          borderColor: '#00ff8844',
          borderWidth: 1,
          titleColor: '#00ff88',
          bodyColor: '#ccc',
        }
      },
      scales: {
        x: { ticks: { color: '#666' }, grid: { color: '#ffffff0a' } },
        y: { ticks: { color: '#666' }, grid: { color: '#ffffff0a' } }
      }
    }
  });
}
