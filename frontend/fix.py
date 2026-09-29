import re

with open(r'c:\aegisflow\frontend\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add toggle switch CSS
css_to_add = '''
.toggle-switch { position: relative; display: inline-block; width: 36px; height: 20px; flex-shrink: 0; }
.toggle-switch input { opacity: 0; width: 0; height: 0; }
.toggle-slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: var(--surface-border); transition: .3s; border-radius: 34px; border: 1px solid var(--text-muted); }
.toggle-slider:before { position: absolute; content: ''; height: 14px; width: 14px; left: 2px; bottom: 2px; background-color: var(--text-muted); transition: .3s; border-radius: 50%; }
.toggle-switch input:checked + .toggle-slider { background: linear-gradient(135deg, #ec4899, #8b5cf6); border-color: transparent; }
.toggle-switch input:checked + .toggle-slider:before { transform: translateX(16px); background-color: white; }
'''
if '.toggle-switch {' not in html:
    html = html.replace('</style>', css_to_add + '</style>')

# 2. Update page-settings
settings_new = '''      <div class="page" id="page-settings">
        <div class="card" style="max-width:600px">
          <div class="card-head"><div class="card-title" style="display:flex;align-items:center;gap:8px"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg> Settings</div></div>
          <div class="card-body">
            <div class="settings-item"><div class="settings-item-left"><div class="settings-item-icon" style="background:#ede9fe;color:#8b5cf6"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"></path><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"></path></svg></div>Notifications</div>
              <label class="toggle-switch">
                <input type="checkbox" checked>
                <span class="toggle-slider"></span>
              </label>
            </div>
            <div class="settings-item"><div class="settings-item-left"><div class="settings-item-icon" style="background:#fef9c3;color:#eab308"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="13.5" cy="6.5" r=".5" fill="currentColor"></circle><circle cx="17.5" cy="10.5" r=".5" fill="currentColor"></circle><circle cx="8.5" cy="7.5" r=".5" fill="currentColor"></circle><circle cx="6.5" cy="12.5" r=".5" fill="currentColor"></circle><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"></path></svg></div>Theme</div><button class="btn btn-outline" style="font-size:11px;padding:5px 10px;display:flex;align-items:center;gap:6px" onclick="toggleDarkMode()" id="themeBtn"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"></path></svg> Dark Mode</button></div>
            <hr style="border:none;border-top:1px solid var(--surface-border);margin:8px 0">
            <div class="settings-item" onclick="logout()"><div class="settings-item-left" style="color:#ef4444"><div class="settings-item-icon" style="background:#fee2e2;color:#ef4444"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" x2="9" y1="12" y2="12"></line></svg></div>Sign Out</div></div>
          </div>
        </div>
      </div>'''
html = re.sub(r'<div class="page" id="page-settings">.*?</div>\s*</div><!-- /content -->', settings_new + '\n\n    </div><!-- /content -->', html, flags=re.DOTALL)

# 3. Update topbar buttons
sun_svg = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"></circle><path d="M12 2v2"></path><path d="M12 20v2"></path><path d="m4.93 4.93 1.41 1.41"></path><path d="m17.66 17.66 1.41 1.41"></path><path d="M2 12h2"></path><path d="M20 12h2"></path><path d="m6.34 17.66-1.41 1.41"></path><path d="m19.07 4.93-1.41 1.41"></path></svg>'
moon_svg = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"></path></svg>'
bell_svg = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"></path><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"></path></svg>'

# Find the theme toggle button - it has the moon/sun emoji in the html body
html = re.sub(r'<button class="icon-btn" id="themeToggle".*?</button>', f'<button class="icon-btn" id="themeToggle" onclick="toggleTheme()" style="border:none;background:var(--surface);backdrop-filter:blur(10px);width:auto;padding:0 12px;display:flex;align-items:center;gap:6px;font-size:12px;border-radius:9999px;color:var(--text-main)">\n        {sun_svg} Light Mode\n      </button>', html, flags=re.DOTALL)

# Find the notif button, replace the emoji with bell_svg
html = re.sub(r'<div class="notif-btn"(.*?)>\s*.*?\s*<div class="notif-dot"', f'<div class="notif-btn"\\1>\n        {bell_svg}\n        <div class="notif-dot"', html, flags=re.DOTALL)

# 4. Update toggleTheme JS
html = re.sub(r"btn\.innerHTML = '[^']+ Light Mode';", f"btn.innerHTML = '{sun_svg} Light Mode';", html)
html = re.sub(r"btn\.innerHTML = '[^']+ Dark Mode';", f"btn.innerHTML = '{moon_svg} Dark Mode';", html)
html = re.sub(r"btn\.innerHTML = savedTheme === 'light' \? '[^']+' : '[^']+';", f"btn.innerHTML = savedTheme === 'light' ? '{moon_svg} Dark Mode' : '{sun_svg} Light Mode';", html)
html = re.sub(r"document\.getElementById\('themeBtn'\)\.textContent = isDark \? 'Light Mode' : 'Dark Mode';", f"document.getElementById('themeBtn').innerHTML = isDark ? '{sun_svg} Light Mode' : '{moon_svg} Dark Mode';", html)


with open(r'c:\aegisflow\frontend\index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Done')
