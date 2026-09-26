
const API = 'http://127.0.0.1:8000';
let currentUser = null;
let currentScanId = null;
let currentPage = 1;
let historyTotalPages = 1;

// ─── AUTH ──────────────────────────────────────────────────────────

function getToken() { return localStorage.getItem('access_token'); }

function authHeaders() {
  return { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getToken()}` };
}

async function apiFetch(url, opts = {}) {
  const res = await fetch(API + url, { ...opts, headers: { ...authHeaders(), ...(opts.headers || {}) } });
  if (res.status === 401) { logout(); return null; }
  return res;
}

function logout() {
  localStorage.clear();
  window.location.href = 'login.html';
}

async function selectFolder() {
  if (window.showDirectoryPicker) {
    try {
      const dirHandle = await window.showDirectoryPicker();
      const files = [];
      async function getFiles(handle, path) {
        for await (const entry of handle.values()) {
          if (entry.kind === 'file') {
            const file = await entry.getFile();
            Object.defineProperty(file, 'webkitRelativePath', { value: path + entry.name });
            files.push(file);
          } else if (entry.kind === 'directory') {
            await getFiles(entry, path + entry.name + '/');
          }
        }
      }
      await getFiles(dirHandle, dirHandle.name + '/');
      handleFileUpload(files, 'folder');
    } catch (e) {
      if (e.name !== 'AbortError') document.getElementById('folderInput').click();
    }
  } else {
    document.getElementById('folderInput').click();
  }
}

// ─── INIT ──────────────────────────────────────────────────────────
// Setup drag and drop
document.addEventListener('DOMContentLoaded', () => {
  const zone = document.getElementById('uploadZone');
  if (zone) {
    zone.addEventListener('dragenter', e => e.preventDefault());
    zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('drag'));
    zone.addEventListener('drop', e => { e.preventDefault(); zone.classList.remove('drag'); handleFileUpload(e.dataTransfer.files); });
  }
});


async function init() {
  if (!getToken()) { window.location.href = 'login.html'; return; }

  try {
    const res = await apiFetch('/api/auth/me');
    if (!res || !res.ok) { logout(); return; }
    currentUser = await res.json();
    renderUserInfo();
    loadDashboard();
  } catch { logout(); }
}

function renderUserInfo() {
  if (!currentUser) return;
  const initial = (currentUser.full_name || currentUser.username || 'U')[0].toUpperCase();
  const color = currentUser.avatar_color || '#06b6d4';

  document.getElementById('sidebarName').textContent = currentUser.full_name || currentUser.username;
  document.getElementById('sidebarOccupation').textContent = currentUser.occupation || 'Developer';
  document.getElementById('sidebarAvatar').textContent = initial;
  document.getElementById('sidebarAvatar').style.background = color;
  document.getElementById('topbarAvatar').textContent = initial;
  document.getElementById('topbarAvatar').style.background = color;
  document.getElementById('profileAvatar').textContent = initial;
  document.getElementById('profileAvatar').style.background = color;
  document.getElementById('profileName').textContent = currentUser.full_name || currentUser.username;
  document.getElementById('profileOccupationText').textContent = currentUser.occupation || 'Developer';
  document.getElementById('p-email').textContent = currentUser.email || '—';
  document.getElementById('p-username').textContent = '@' + (currentUser.username || '—');
  document.getElementById('p-org').textContent = currentUser.organization || '—';
  document.getElementById('p-occupation').textContent = currentUser.occupation || '-';
  document.getElementById('p-location').textContent = currentUser.location || '—';
  document.getElementById('p-joined').textContent = currentUser.created_at ? currentUser.created_at.slice(0,10) : '—';
  document.getElementById('p-scans').textContent = currentUser.total_scans ?? '0';
  document.getElementById('p-critical').textContent = currentUser.critical_scans ?? '0';
  document.getElementById('p-fix').textContent = '87';
}

// ─── PAGE NAVIGATION ───────────────────────────────────────────────

function showPage(name, el) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById(`page-${name}`).classList.add('active');
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  if (el) el.classList.add('active');

  const titles = { dashboard:'Dashboard', scan:'New Scan', history:'Scan History', analytics:'Analytics', profile:'Profile', settings:'Settings' };
  const subs = { dashboard:'Overview of your security pipeline', scan:'Upload and analyze code', history:'All past security scans', analytics:'Security trends & insights', profile:'Manage your account', settings:'Configure AegisFlow' };
  document.getElementById('pageTitle').textContent = titles[name] || name;
  document.getElementById('pageSubtitle').textContent = subs[name] || '';

  if (name === 'history') loadHistory();
  if (name === 'dashboard') loadDashboard();
  if (name === 'analytics') loadAnalytics();
  if (name === 'profile') loadProfileActivity();
}

// ─── DASHBOARD ─────────────────────────────────────────────────────

async function loadDashboard() {
  try {
    const res = await apiFetch('/api/dashboard');
    if (!res || !res.ok) return;
    const data = await res.json();

    document.getElementById('totalScans').textContent = data.total_scans ?? 0;
    document.getElementById('criticalIssues').textContent = data.critical_issues ?? 0;
    document.getElementById('fixRate').textContent = (data.fix_success_rate ?? 0) + '%';
    document.getElementById('avgTime').textContent = (data.avg_analysis_time ?? 2.3) + 's';
    document.getElementById('scansChange').textContent = `↑ ${data.scans_this_week ?? 0} this week`;
    document.getElementById('a-total').textContent = data.total_scans ?? 0;
    document.getElementById('a-vulns').textContent = data.total_vulnerabilities ?? 0;
    document.getElementById('a-fix').textContent = (data.fix_success_rate ?? 0) + '%';
    document.getElementById('a-crit').textContent = data.critical_issues ?? 0;

    renderRecentScans(data.recent_scans || []);
    renderDonutChart(data.vulnerability_breakdown || {});
    renderTrendChart();
    renderAnalyticsCharts(data);
  } catch (e) {
    console.error('Dashboard error:', e);
  }
}

function renderRecentScans(scans) {
  const el = document.getElementById('recentScansList');
  if (!scans.length) {
    el.innerHTML = '<div class="empty-state"><div class="empty-icon">📋</div><div class="empty-sub">No scans yet. Run your first scan!</div></div>';
    return;
  }
  el.innerHTML = scans.map(s => `
    <div style="display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid #f8fafc;cursor:pointer" onclick="viewScan('${s._id}')">
      <div style="width:30px;height:30px;background:#f1f5f9;border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:13px;flex-shrink:0">📄</div>
      <div style="flex:1;min-width:0">
        <div style="font-size:12.5px;font-weight:500;color:#0f172a;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${s.filename || 'unknown'}</div>
        <div style="font-size:11px;color:#94a3b8">${formatDate(s.created_at)}</div>
      </div>
      <span class="risk-badge ${s.risk_level}">${s.total_found || 0} ${s.risk_level === 'SAFE' ? 'Issues' : s.risk_level}</span>
    </div>
  `).join('');
}

let donutInstance = null;
let trendInstance = null;

function renderDonutChart(breakdown) {
  const ctx = document.getElementById('donutChart').getContext('2d');
  if (donutInstance) donutInstance.destroy();

  const labels = ['Critical', 'High', 'Medium', 'Low'];
  const values = [breakdown.CRITICAL||0, breakdown.HIGH||0, breakdown.MEDIUM||0, breakdown.LOW||0];
  const colors = ['#ef4444','#f97316','#f59e0b','#10b981'];

  if (values.every(v => v === 0)) {
    document.getElementById('donutLegend').innerHTML = '<div class="empty-state"><div class="empty-sub">No vulnerabilities yet</div></div>';
    return;
  }

  donutInstance = new Chart(ctx, {
    type: 'doughnut',
    data: { labels, datasets: [{ data: values, backgroundColor: colors, borderWidth: 0, hoverOffset: 4 }] },
    options: { cutout: '65%', plugins: { legend: { display: false } }, responsive: false }
  });

  const total = values.reduce((a,b) => a+b, 0);
  document.getElementById('donutLegend').innerHTML = labels.map((l, i) => `
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
      <div style="width:10px;height:10px;border-radius:50%;background:${colors[i]};flex-shrink:0"></div>
      <span style="font-size:12px;color:#374151;flex:1">${l}</span>
      <span style="font-size:12px;font-weight:600;color:#0f172a">${values[i]}</span>
      <span style="font-size:11px;color:#94a3b8">${total > 0 ? Math.round(values[i]/total*100) : 0}%</span>
    </div>
  `).join('');
}

function renderTrendChart() {
  const ctx = document.getElementById('trendChart').getContext('2d');
  if (trendInstance) trendInstance.destroy();
  const labels = Array.from({length: 10}, (_, i) => {
    const d = new Date(); d.setDate(d.getDate() - (9-i));
    return d.toLocaleDateString('en', {month:'short', day:'numeric'});
  });
  const data = Array.from({length: 10}, () => Math.floor(Math.random() * 20 + 5));

  trendInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{ label: 'Vulnerabilities', data, borderColor: '#06b6d4', backgroundColor: 'rgba(6,182,212,0.08)', tension: 0.4, fill: true, pointRadius: 3, pointBackgroundColor: '#06b6d4', borderWidth: 2 }]
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 10 }, color: '#94a3b8' } },
        y: { grid: { color: '#f1f5f9' }, ticks: { font: { size: 10 }, color: '#94a3b8' } }
      },
      responsive: true,
      maintainAspectRatio: true
    }
  });
}

let analyticsDonut = null, analyticsBar = null;

function renderAnalyticsCharts(data) {
  const bd = data.vulnerability_breakdown || {};
  const ctx1 = document.getElementById('analyticsDonut').getContext('2d');
  if (analyticsDonut) analyticsDonut.destroy();
  analyticsDonut = new Chart(ctx1, {
    type: 'doughnut',
    data: {
      labels: ['Critical', 'High', 'Medium', 'Low'],
      datasets: [{ data: [bd.CRITICAL||0, bd.HIGH||0, bd.MEDIUM||0, bd.LOW||0], backgroundColor: ['#ef4444','#f97316','#f59e0b','#10b981'], borderWidth: 0 }]
    },
    options: { plugins: { legend: { position: 'bottom', labels: { font: { size: 11 }, padding: 12 } } }, responsive: true, maintainAspectRatio: true }
  });

  const ctx2 = document.getElementById('analyticsBar').getContext('2d');
  if (analyticsBar) analyticsBar.destroy();
  const topTypes = data.top_vulnerability_types || [];
  analyticsBar = new Chart(ctx2, {
    type: 'bar',
    data: {
      labels: topTypes.map(t => t.type.split(' ').slice(0,2).join(' ')),
      datasets: [{ label: 'Count', data: topTypes.map(t => t.count), backgroundColor: 'rgba(6,182,212,0.7)', borderRadius: 6 }]
    },
    options: {
      indexAxis: 'y',
      plugins: { legend: { display: false } },
      scales: { x: { grid: { color: '#f1f5f9' }, ticks: { font: { size: 10 } } }, y: { grid: { display: false }, ticks: { font: { size: 10 } } } },
      responsive: true, maintainAspectRatio: true
    }
  });
}

async function loadAnalytics() {
  const res = await apiFetch('/api/dashboard');
  if (res && res.ok) { const data = await res.json(); renderAnalyticsCharts(data); }
}

// ─── SCAN ──────────────────────────────────────────────────────────

window.appFiles = [];
window.activeFileIndex = -1;

function handleFileUpload(files, type) {
  if (!files || !files.length) return;
  const fileArr = Array.from(files).filter(f =>
    f.name.match(/\.(py|js|ts|jsx|tsx|java|go|rb|php|c|cpp|h|hpp|swift|txt|md)$/)
  );

  // Strict check
  if (type === 'file') {
    if (Array.from(files).some(f => f.webkitRelativePath && f.webkitRelativePath.includes('/'))) {
      showToast('Folders not allowed here. Click Folder button.', 'error');
      return;
    }
  } else if (type === 'folder') {
    if (Array.from(files).every(f => !f.webkitRelativePath || !f.webkitRelativePath.includes('/'))) {
      showToast('Files not allowed here. Click Files button.', 'error');
      return;
    }
  }

  if (!fileArr.length) { showToast('No supported files found', 'error'); return; }

  window.appFiles = fileArr;
  window.activeFileIndex = 0;
  
  document.getElementById('uploadedFiles').style.display = 'block';
  renderFileList();
  switchActiveFile(0);

  showToast(`✓ Loaded ${fileArr.length} file(s)`, 'success');
}

function renderFileList() {
  document.getElementById('fileList').innerHTML = window.appFiles.map((f, i) =>
    `<span onclick="switchActiveFile(${i})" id="file-pill-${i}" style="background:${i === window.activeFileIndex ? '#06b6d4' : '#f1f5f9'};color:${i === window.activeFileIndex ? 'white' : '#374151'};border-radius:6px;padding:4px 10px;font-size:11px;cursor:pointer;transition:0.2s;display:inline-block">📄 ${f.name}</span>`
  ).join('');
}

async function switchActiveFile(index) {
  if (index < 0 || index >= window.appFiles.length) return;
  window.activeFileIndex = index;
  renderFileList();
  
  const file = window.appFiles[index];
  const ext = file.name.split('.').pop().toLowerCase();
  const langMap = { py:'python', js:'javascript', ts:'typescript', java:'java', go:'go', rb:'ruby', php:'php', c:'c', cpp:'cpp', swift:'swift', jsx:'javascript', tsx:'typescript', h:'c', hpp:'cpp', txt:'text', md:'markdown' };
  const detectedLang = langMap[ext] || 'python';
  
  document.getElementById('langSelect').value = detectedLang;
  document.getElementById('editorFilename').textContent = file.name;
  document.getElementById('detectedLang').textContent = detectedLang.toUpperCase();
  document.getElementById('detectedLang').style.display = 'inline-block';
  
  try {
    const text = await file.text();
    document.getElementById('codeInput').value = text;
    
    // Clear scan results for new file
    document.getElementById('vulnList').innerHTML = '<div class="empty-state"><div class="empty-icon">🛡️</div><div class="empty-title">Ready to scan</div><div class="empty-sub">Click Analyze to scan this file</div></div>';
    document.getElementById('vulnSubtitle').textContent = 'Run a scan to see results';
    document.getElementById('vulnCount').style.display = 'none';
    document.getElementById('diffCard').style.display = 'none';
    document.getElementById('geminiCard').style.display = 'none';
    document.getElementById('fixBtn').disabled = true;
    currentScanId = null;
  } catch(e) {
    showToast('Failed to read file', 'error');
  }
}

function clearEditor() {
  document.getElementById('codeInput').value = '';
  document.getElementById('vulnList').innerHTML = '<div class="empty-state"><div class="empty-icon">🛡️</div><div class="empty-title">Ready to scan</div><div class="empty-sub">Paste code or upload files, then click Analyze</div></div>';
  document.getElementById('vulnSubtitle').textContent = 'Run a scan to see results';
  document.getElementById('vulnCount').style.display = 'none';
  document.getElementById('diffCard').style.display = 'none';
  document.getElementById('geminiCard').style.display = 'none';
  document.getElementById('fixBtn').disabled = true;
  document.getElementById('detectedLang').style.display = 'none';
  document.getElementById('uploadedFiles').style.display = 'none';
  document.getElementById('editorFilename').textContent = 'untitled';
  currentScanId = null;
  window.appFiles = [];
  window.activeFileIndex = -1;
}\n\nasync function analyzeCode() {
  const code = document.getElementById('codeInput').value.trim();
  if (!code) { showToast('Please paste code or upload a file first', 'error'); return; }

  const btn = document.getElementById('analyzeBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>Analyzing...';

  try {
    const res = await apiFetch('/api/analyze', {
      method: 'POST',
      body: JSON.stringify({
        code,
        language: document.getElementById('langSelect').value,
        filename: document.getElementById('editorFilename').textContent || 'code',
        use_gemini: true
      })
    });

    if (!res || !res.ok) {
      const err = res ? await res.json() : {};
      showToast('Analysis failed: ' + (err.detail || 'Unknown error'), 'error');
      return;
    }

    const data = await res.json();
    currentScanId = data.scan_id;

    // Show Gemini analysis
    if (data.gemini_analysis) {
      document.getElementById('geminiCard').style.display = 'block';
      document.getElementById('geminiText').textContent = data.gemini_analysis;
    }

    // Show vulnerabilities
    renderVulnerabilities(data.vulnerabilities, data.total_found, data.risk_level);

    document.getElementById('fixBtn').disabled = false;
    showToast(`Found ${data.total_found} vulnerabilities [${data.risk_level}]`, data.total_found > 0 ? 'error' : 'success');

  } finally {
    btn.disabled = false;
    btn.innerHTML = '🔍 Analyze Code';
  }
}

function renderVulnerabilities(vulns, total, riskLevel) {
  const el = document.getElementById('vulnList');
  const cnt = document.getElementById('vulnCount');
  const sub = document.getElementById('vulnSubtitle');

  if (!vulns || vulns.length === 0) {
    el.innerHTML = '<div class="empty-state"><div class="empty-icon">✅</div><div class="empty-title">No vulnerabilities found!</div><div class="empty-sub">Your code looks secure</div></div>';
    sub.textContent = 'No issues detected';
    cnt.style.display = 'none';
    return;
  }

  cnt.textContent = `${total} found`;
  cnt.style.display = 'inline-block';
  sub.textContent = `Risk Level: ${riskLevel}`;

  el.innerHTML = vulns.map(v => `
    <div class="vuln-card ${v.severity}">
      <div class="vuln-head">
        <span class="vuln-title">${v.type}</span>
        <span class="severity-badge ${v.severity}">${v.severity}</span>
      </div>
      <div class="vuln-desc">${v.description}</div>
      <div class="vuln-meta">
        <span>📍 Line ${v.line || 'N/A'}</span>
        <span>${v.cwe_id || ''}</span>
        <span>${v.owasp_id || ''}</span>
        <span>Confidence: ${Math.round((v.confidence || 0) * 100)}%</span>
      </div>
      ${v.code_snippet ? `<div style="background:rgba(0,0,0,0.05);border-radius:4px;padding:5px 8px;margin-top:6px;font-family:monospace;font-size:10px;color:#374151">${v.code_snippet}</div>` : ''}
      <div class="conf-bar"><div class="conf-fill" style="width:${Math.round((v.confidence||0)*100)}%"></div></div>
    </div>
  `).join('');
}

async function generateFix() {
  if (!currentScanId) { showToast('Run a scan first', 'error'); return; }
  const code = document.getElementById('codeInput').value;
  if (!code) return;

  const btn = document.getElementById('fixBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>Generating...';

  try {
    // Get vulnerabilities from current scan
    const scanRes = await apiFetch(`/api/scans/${currentScanId}`);
    const scan = scanRes && scanRes.ok ? await scanRes.json() : { vulnerabilities: [] };

    const res = await apiFetch('/api/fix', {
      method: 'POST',
      body: JSON.stringify({
        scan_id: currentScanId,
        code,
        language: document.getElementById('langSelect').value,
        vulnerabilities: scan.vulnerabilities || []
      })
    });

    if (!res || !res.ok) { showToast('Fix generation failed', 'error'); return; }
    const data = await res.json();

    // Show diff viewer
    renderDiffViewer(code, data.fixed_code);
    document.getElementById('diffCard').style.display = 'block';
    showToast(`Fix generated! Confidence: ${Math.round(data.confidence * 100)}%`, 'success');

    // Scroll to diff
    document.getElementById('diffCard').scrollIntoView({ behavior: 'smooth' });

  } finally {
    btn.disabled = false;
    btn.innerHTML = '✨ Generate Fix';
  }
}

function renderDiffViewer(original, fixed) {
  const origLines = original.split('\n');
  const fixedLines = fixed.split('\n');

  document.getElementById('originalPane').innerHTML = origLines.map((line, i) => {
    const cls = fixedLines[i] !== line ? 'removed' : 'neutral';
    return `<div class="diff-line ${cls}"><span style="color:#475569;min-width:24px;text-align:right;margin-right:8px;user-select:none">${i+1}</span>${escHtml(line)}</div>`;
  }).join('');

  document.getElementById('fixedPane').innerHTML = fixedLines.map((line, i) => {
    const cls = origLines[i] !== line ? 'added' : 'neutral';
    return `<div class="diff-line ${cls}"><span style="color:#475569;min-width:24px;text-align:right;margin-right:8px;user-select:none">${i+1}</span>${escHtml(line)}</div>`;
  }).join('');
}

function escHtml(str) {
  return (str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function copyFixed() {
  const lines = document.getElementById('fixedPane').querySelectorAll('.diff-line');
  const text = Array.from(lines).map(l => l.textContent.replace(/^\d+/, '').trim()).join('\n');
  navigator.clipboard.writeText(text).then(() => showToast('Copied to clipboard!', 'success'));
}

// ─── DOWNLOADS ─────────────────────────────────────────────────────

async function downloadReport(type) {
  if (!currentScanId) { showToast('No scan selected', 'error'); return; }
  showToast(`Preparing ${type.toUpperCase()} download...`, 'info');
  const endpoint = `/api/download/${currentScanId}/${type}`;
  const res = await apiFetch(endpoint);
  if (!res || !res.ok) { showToast('Download failed', 'error'); return; }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = `aegisflow_report_${currentScanId.slice(-6)}.${type === 'markdown' ? 'md' : type === 'code' ? 'py' : type}`;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showToast('Download started!', 'success');
}

// ─── HISTORY ───────────────────────────────────────────────────────

async function loadHistory() {
  const search = document.getElementById('historySearch').value;
  const status = document.getElementById('historyFilter').value;
  const tbody = document.getElementById('historyTableBody');
  tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:30px;color:#94a3b8">Loading...</td></tr>';

  const res = await apiFetch(`/api/scans?page=${currentPage}&limit=10&search=${search}&status=${status}`);
  if (!res || !res.ok) return;
  const data = await res.json();
  historyTotalPages = data.pages || 1;

  document.getElementById('historyPageInfo').textContent = `${data.total} total scans`;
  document.getElementById('pageNum').textContent = currentPage;
  document.getElementById('prevBtn').disabled = currentPage <= 1;
  document.getElementById('nextBtn').disabled = currentPage >= historyTotalPages;

  if (!data.scans.length) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:40px;color:#94a3b8">No scans found. Run your first scan!</td></tr>';
    return;
  }

  tbody.innerHTML = data.scans.map(s => `
    <tr>
      <td><div style="font-weight:500">${s.filename || 'unknown'}</div></td>
      <td><span style="background:#f1f5f9;border-radius:6px;padding:2px 8px;font-size:11px">${(s.language || '').toUpperCase()}</span></td>
      <td style="color:#64748b">${formatDate(s.created_at)}</td>
      <td style="font-weight:600">${s.total_found || 0}</td>
      <td><span class="risk-badge ${s.risk_level}">${s.risk_level || 'SAFE'}</span></td>
      <td>${s.fix_applied ? '<span style="color:#10b981;font-size:12px">✓ Resolved</span>' : '<span style="color:#f59e0b;font-size:12px">⏳ Pending</span>'}</td>
      <td>
        <div class="action-btns">
          <button class="icon-btn" onclick="viewScan('${s._id}')" title="View">👁</button>
          <button class="icon-btn" onclick="downloadHistoryScan('${s._id}')" title="Download">⬇</button>
          <button class="icon-btn" onclick="deleteScan('${s._id}')" title="Delete" style="color:#ef4444;border-color:#ef4444">🗑</button>
        </div>
      </td>
    </tr>
  `).join('');
}

function changePage(dir) {
  currentPage = Math.max(1, Math.min(historyTotalPages, currentPage + dir));
  loadHistory();
}

async function viewScan(id) {
  showPage('scan', document.querySelector('.nav-item:nth-child(2)'));
  const res = await apiFetch(`/api/scans/${id}`);
  if (!res || !res.ok) return;
  const scan = await res.json();
  currentScanId = id;
  document.getElementById('codeInput').value = scan.original_code || '';
  document.getElementById('langSelect').value = scan.language || 'python';
  document.getElementById('editorFilename').textContent = scan.filename || 'unknown';
  renderVulnerabilities(scan.vulnerabilities || [], scan.total_found || 0, scan.risk_level || 'SAFE');
  if (scan.fixed_code) {
    renderDiffViewer(scan.original_code || '', scan.fixed_code);
    document.getElementById('diffCard').style.display = 'block';
  }
  if (scan.gemini_analysis) {
    document.getElementById('geminiCard').style.display = 'block';
    document.getElementById('geminiText').textContent = scan.gemini_analysis;
  }
  document.getElementById('fixBtn').disabled = false;
}

async function downloadHistoryScan(id) {
  currentScanId = id;
  await downloadReport('zip');
}

async function deleteScan(id) {
  if (!confirm('Delete this scan?')) return;
  const res = await apiFetch(`/api/scans/${id}`, { method: 'DELETE' });
  if (res && res.ok) { showToast('Scan deleted', 'success'); loadHistory(); }
  else showToast('Delete failed', 'error');
}

// ─── PROFILE ───────────────────────────────────────────────────────

async function loadProfileActivity() {
  const res = await apiFetch('/api/scans?page=1&limit=5');
  if (!res || !res.ok) return;
  const data = await res.json();
  const el = document.getElementById('profileActivity');
  if (!data.scans.length) {
    el.innerHTML = '<div class="empty-state"><div class="empty-sub">No recent activity</div></div>';
    return;
  }
  el.innerHTML = data.scans.map(s => `
    <div class="activity-item">
      <div class="activity-dot" style="background:${s.risk_level === 'CRITICAL' ? '#ef4444' : s.risk_level === 'HIGH' ? '#f97316' : s.risk_level === 'SAFE' ? '#10b981' : '#f59e0b'}"></div>
      <div style="flex:1">
        <div style="font-size:12.5px;font-weight:500;color:#0f172a">Scan: ${s.filename || 'unknown'}</div>
        <div style="font-size:11px;color:#94a3b8">${formatDate(s.created_at)}</div>
      </div>
      <span class="risk-badge ${s.risk_level}" style="font-size:10px">${s.total_found} issues</span>
    </div>
  `).join('');
}

function toggleEditMode() {
  const info = document.getElementById('profileInfoSection');
  const edit = document.getElementById('profileEditSection');
  if (edit.style.display === 'none') {
    edit.style.display = 'block';
    info.style.display = 'none';
    document.getElementById('edit-name').value = currentUser?.full_name || '';
    document.getElementById('edit-occupation').value = currentUser?.occupation || '';
    document.getElementById('edit-email').value = currentUser?.email || '';
    document.getElementById('edit-org').value = currentUser?.organization || '';

    document.getElementById('edit-location').value = currentUser?.location || '';
  } else {
    edit.style.display = 'none';
    info.style.display = 'block';
  }
}

async function saveProfile() {
  const res = await apiFetch('/api/auth/profile', {
    method: 'PUT',
    body: JSON.stringify({
      full_name: document.getElementById('edit-name').value,
      occupation: document.getElementById('edit-occupation').value,
      email: document.getElementById('edit-email').value,
      organization: document.getElementById('edit-org').value,

      location: document.getElementById('edit-location').value,
    })
  });
  if (res && res.ok) {
    const data = await res.json();
    currentUser = { ...currentUser, ...data.user };
    renderUserInfo();
    toggleEditMode();
    showToast('Profile updated!', 'success');
  } else {
    showToast('Update failed', 'error');
  }
}

// ─── TOAST & NOTIFS ────────────────────────────────────────────────

let notifCount = 0;

function clearNotifs() {
  notifCount = 0;
  document.getElementById('notifDot').style.display = 'none';
  document.getElementById('notifList').innerHTML = '<div class="empty-state" style="padding:15px"><div class="empty-sub">No recent notifications</div></div>';
}

function showToast(msg, type = 'info') {
  const container = document.getElementById('toastContainer');
  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  const icon = icons[type] || 'ℹ️';

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icon}</span><span>${msg}</span>`;
  container.appendChild(toast);
  setTimeout(() => { toast.style.opacity = '0'; toast.style.transition = 'opacity .3s'; setTimeout(() => toast.remove(), 300); }, 3500);

  // Add to Notification Dropdown
  const list = document.getElementById('notifList');
  if (list.querySelector('.empty-state')) list.innerHTML = '';
  const item = document.createElement('div');
  item.className = 'notif-item';
  item.innerHTML = `<div class="notif-icon">${icon}</div><div style="flex:1"><div style="color:var(--text-main);margin-bottom:2px">${msg}</div><div style="color:#94a3b8;font-size:10px">${formatDate(new Date().toISOString())}</div></div>`;
  list.insertBefore(item, list.firstChild);

  notifCount++;
  document.getElementById('notifDot').style.display = 'block';
}

// ─── THEME ─────────────────────────────────────────────────────────

function toggleDarkMode() {
  document.body.classList.toggle('dark-mode');
  const isDark = document.body.classList.contains('dark-mode');
  localStorage.setItem('theme', isDark ? 'dark' : 'light');
  document.getElementById('themeBtn').textContent = isDark ? 'Light Mode' : 'Dark Mode';
}

if (localStorage.getItem('theme') === 'dark') {
  toggleDarkMode();
}

// ─── UTILS ─────────────────────────────────────────────────────────

function formatDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  const now = new Date();
  const diff = now - d;
  if (diff < 60000) return 'Just now';
  if (diff < 3600000) return `${Math.floor(diff/60000)}m ago`;
  if (diff < 86400000) return `Today, ${d.toLocaleTimeString('en', {hour:'2-digit', minute:'2-digit'})}`;
  if (diff < 172800000) return `Yesterday, ${d.toLocaleTimeString('en', {hour:'2-digit', minute:'2-digit'})}`;
  return d.toLocaleDateString('en', {month:'short', day:'numeric', year:'numeric'});
}

// ─── START ─────────────────────────────────────────────────────────
init();
