const socket = io();

// Chart Configurations
const chartConfigs = {
  power: { labelConsumed: 'Power Consumed', labelGenerated: 'Power Generated' },
  voltage: { labelConsumed: 'Voltage Consumed', labelGenerated: 'Voltage Generated' },
  current: { labelConsumed: 'Current Consumed', labelGenerated: 'Current Generated' },
};

const charts = {};
const labels = [];

// Initialize charts
for (const key in chartConfigs) {
  const ctx = document.getElementById(`${key}Chart`)?.getContext('2d');
  if (!ctx) continue;

  const cfg = chartConfigs[key];
  charts[key] = new Chart(ctx, {
    type: 'line',
    data: {
      datasets: [
        {
          label: cfg.labelConsumed,
          data: [],
          borderColor: getComputedStyle(document.documentElement)
            .getPropertyValue('--color-consumed')
            .trim(),
          borderWidth: 2,
          tension: 0.4,
          pointRadius: 2,
          fill: false,
        },
        {
          label: cfg.labelGenerated,
          data: [],
          borderColor: getComputedStyle(document.documentElement)
            .getPropertyValue('--color-generated')
            .trim(),
          borderWidth: 2,
          tension: 0.4,
          pointRadius: 2,
          fill: false,
        },
      ],
    },
    options: {
      animation: { duration: 400, easing: 'easeOutQuart' },
      plugins: { legend: { labels: { color: '#fff' } } },
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          type: 'time',
          time: {
            unit: 'second',
            displayFormats: { second: 'HH:mm:ss' },
          },
          ticks: {
            color: '#aaa',
            autoSkip: true,
            maxTicksLimit: 10,
          },
          grid: { color: '#333' },
        },
        y: {
          beginAtZero: true,
          ticks: { color: '#aaa' },
          grid: { color: '#333' },
        },
      },
      spanGaps: true,
    },
  });
}

// Latest values
let latestConsumed = { voltage: 0, current: 0, power: 0 };
let latestGenerated = { voltage: 0, current: 0, power: 0 };

function updateDashboard(data) {
  if (!data) return;

  const newConsumed = data.consumed ?? null;
  const newGenerated = data.generated ?? null;

  // --- Update Table ---
  ['Voltage', 'Current', 'Power'].forEach(f => {
    const field = f.toLowerCase();
    const consumedElem = document.getElementById(`consumed${f}`);
    const generatedElem = document.getElementById(`generated${f}`);

    if (newConsumed && newConsumed[field] !== undefined && consumedElem)
      consumedElem.textContent = newConsumed[field].toFixed(2);

    if (newGenerated && newGenerated[field] !== undefined && generatedElem)
      generatedElem.textContent = newGenerated[field].toFixed(2);
  });

  // --- Net Power ---
  const netElem = document.getElementById('netPower');
  if (netElem && newConsumed && newGenerated) {
    const netPower = (newGenerated.power ?? 0) - (newConsumed.power ?? 0);
    netElem.textContent = netPower.toFixed(2);
    netElem.className =
      'net-power ' +
      (netPower > 0 ? 'positive' : netPower < 0 ? 'negative' : 'zero');
  }

  // --- Update Charts ---
  const time = new Date(
    newConsumed?.timestamp ?? newGenerated?.timestamp ?? Date.now()
  );

  Object.keys(charts).forEach(key => {
    const chart = charts[key];
    if (!chart) return;

    const consumedVal =
      newConsumed && newConsumed[key] !== undefined
        ? { x: time, y: newConsumed[key] }
        : { x: time, y: null };

    const generatedVal =
      newGenerated && newGenerated[key] !== undefined
        ? { x: time, y: newGenerated[key] }
        : { x: time, y: null };

    chart.data.datasets[0].data.push(consumedVal);
    chart.data.datasets[1].data.push(generatedVal);

    // Keep max 20 points
    chart.data.datasets.forEach(ds => {
      if (ds.data.length > 20) ds.data.shift();
    });

    // chart.options.spanGaps = true;

    chart.update('active');
  });
}

// Socket listener
socket.on('meter_reading', data => updateDashboard(data));

// Controls
function sendAction(action) {
  socket.emit('control_action', { action });
}