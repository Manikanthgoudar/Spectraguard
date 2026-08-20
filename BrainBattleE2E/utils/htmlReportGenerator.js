const fs = require('fs');
const path = require('path');

function generateHtmlReport(testResults, outputPath = 'Test_Results/HTML/execution-report.html') {
  const total = testResults.length;
  const passed = testResults.filter(r => r.status === 'PASSED').length;
  const failed = total - passed;
  const passRate = total > 0 ? ((passed / total) * 100).toFixed(1) : 100.0;
  const totalDuration = testResults.reduce((acc, r) => acc + (r.duration || 5), 0);

  const categoriesMap = {};
  testResults.forEach(r => {
    const cat = r.category || 'Functional';
    if (!categoriesMap[cat]) categoriesMap[cat] = { total: 0, passed: 0, failed: 0 };
    categoriesMap[cat].total++;
    if (r.status === 'PASSED') categoriesMap[cat].passed++;
    else categoriesMap[cat].failed++;
  });

  const categoryRows = Object.keys(categoriesMap).map(cat => {
    const c = categoriesMap[cat];
    const rate = ((c.passed / c.total) * 100).toFixed(1);
    return `
      <tr>
        <td><strong>${cat}</strong></td>
        <td>${c.total}</td>
        <td><span class="badge pass">${c.passed}</span></td>
        <td><span class="badge ${c.failed > 0 ? 'fail' : 'pass'}">${c.failed}</span></td>
        <td><strong>${rate}%</strong></td>
      </tr>
    `;
  }).join('');

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>BrainBattle E2E Web Execution Report</title>
  <style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #121212; color: #e0e0e0; margin: 0; padding: 20px; }
    .container { max-width: 1200px; margin: 0 auto; }
    .header { background: linear-gradient(135deg, #1f4e79, #2f5597); padding: 25px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
    h1 { margin: 0; color: #ffffff; font-size: 28px; }
    p.subtitle { margin: 5px 0 0 0; color: #b0c4de; font-size: 14px; }
    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 25px 0; }
    .card { background: #1e1e1e; border: 1px solid #333; border-radius: 8px; padding: 20px; text-align: center; }
    .card .val { font-size: 32px; font-weight: bold; margin-top: 5px; }
    .val.pass { color: #4caf50; }
    .val.fail { color: #f44336; }
    .val.info { color: #2196f3; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; background: #1e1e1e; border-radius: 8px; overflow: hidden; }
    th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #333; }
    th { background-color: #252525; color: #90caf9; }
    tr:hover { background-color: #2a2a2a; }
    .badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    .badge.pass { background-color: #1b5e20; color: #a5d6a7; }
    .badge.fail { background-color: #b71c1c; color: #ef9a9a; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🌐 BrainBattle E2E Web Execution Dashboard</h1>
      <p class="subtitle">Automated Selenium E2E Web Test Report • Generated ${new Date().toLocaleString()}</p>
    </div>

    <div class="stats-grid">
      <div class="card"><div class="title">Total Assertions</div><div class="val info">${total}</div></div>
      <div class="card"><div class="title">Passed</div><div class="val pass">${passed}</div></div>
      <div class="card"><div class="title">Failed</div><div class="val fail">${failed}</div></div>
      <div class="card"><div class="title">Pass Rate</div><div class="val pass">${passRate}%</div></div>
      <div class="card"><div class="title">Total Duration</div><div class="val info">${(totalDuration / 1000).toFixed(2)}s</div></div>
    </div>

    <h2>📊 Category Breakdown Summary</h2>
    <table>
      <thead>
        <tr>
          <th>Category / Testing Type</th>
          <th>Total Assertions</th>
          <th>Passed</th>
          <th>Failed</th>
          <th>Pass Rate</th>
        </tr>
      </thead>
      <tbody>
        ${categoryRows}
      </tbody>
    </table>
  </div>
</body>
</html>`;

  const targetDir = path.dirname(outputPath);
  if (!fs.existsSync(targetDir)) {
    fs.mkdirSync(targetDir, { recursive: true });
  }

  fs.writeFileSync(outputPath, html, 'utf-8');
  console.log(`[HtmlReporter] Generated HTML execution report at ${outputPath}`);
}

module.exports = generateHtmlReport;
