// Chart.js pie chart for investment breakdown
// Usage: call renderInvestmentPieChart(data) with {invested, returns}

function renderInvestmentPieChart(data, canvasId) {
  const ctx = document.getElementById(canvasId).getContext('2d');
  if (ctx._chartInstance) {
    ctx._chartInstance.destroy();
  }
  ctx._chartInstance = new Chart(ctx, {
    type: 'pie',
    data: {
      labels: ['Amount Invested', 'Investment Returns'],
      datasets: [{
        data: [data.invested, data.returns],
        backgroundColor: ['#0b5cff', '#4ad991'],
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'bottom' },
        title: { display: true, text: 'Investment Balance Breakdown' },
        datalabels: {
          color: '#111',
          font: { weight: 'bold', size: 16 },
          formatter: function(value, context) {
            const total = context.dataset.data.reduce((a, b) => a + b, 0);
            const percent = total > 0 ? (value / total * 100) : 0;
            return '$' + value.toLocaleString(undefined, {maximumFractionDigits:0}) + '\n' + percent.toFixed(1) + '%';
          },
          anchor: 'end',
          align: 'center',
        }
      }
    },
    plugins: [ChartDataLabels]
  });
}
