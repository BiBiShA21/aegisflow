import re

with open(r'c:\aegisflow\frontend\register.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update text gradient if it exists
html = html.replace('linear-gradient(90deg,#06b6d4,#22d3ee)', 'linear-gradient(90deg,#ec4899,#8b5cf6)')

# 2. Update feature-icon CSS
html = html.replace('background:rgba(6,182,212,0.15);border:1px solid rgba(6,182,212,0.3)', 'background:linear-gradient(135deg, #ec4899, #8b5cf6);border:none;color:white')

# 3. Add toggle button to top right
sun_svg = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"></circle><path d="M12 2v2"></path><path d="M12 20v2"></path><path d="m4.93 4.93 1.41 1.41"></path><path d="m17.66 17.66 1.41 1.41"></path><path d="M2 12h2"></path><path d="M20 12h2"></path><path d="m6.34 17.66-1.41 1.41"></path><path d="m19.07 4.93-1.41 1.41"></path></svg>'
moon_svg = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"></path></svg>'

btn_html = f'''  <!-- Theme Toggle -->
  <button id="themeToggle" onclick="toggleTheme()" style="position: absolute; top: 20px; right: 20px; z-index: 100; border: 1px solid var(--surface-border); background: var(--surface); padding: 8px 12px; border-radius: 9999px; color: var(--text-main); cursor: pointer; display: flex; align-items: center; gap: 8px; font-size: 12px; font-weight: 500; backdrop-filter: blur(10px);">
    {sun_svg} Light Mode
  </button>'''

if 'id="themeToggle"' not in html:
    html = html.replace('<body>', '<body>\n' + btn_html)

# Update the toggleTheme JS in register.html just like login.html
html = re.sub(r"btn\.innerHTML = '[^']+ Dark Mode';", f"btn.innerHTML = '{moon_svg} Dark Mode';", html)
html = re.sub(r"btn\.innerHTML = '[^']+ Light Mode';", f"btn.innerHTML = '{sun_svg} Light Mode';", html)
html = re.sub(r"btn\.innerHTML = savedTheme === 'light' \? '[^']+' : '[^']+';", f"btn.innerHTML = savedTheme === 'light' ? '{moon_svg} Dark Mode' : '{sun_svg} Light Mode';", html)


# 4. Replace emojis with clean SVGs
search_svg = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>'
robot_svg = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="10" rx="2"></rect><circle cx="12" cy="5" r="2"></circle><path d="M12 7v4"></path><line x1="8" y1="16" x2="8" y2="16"></line><line x1="16" y1="16" x2="16" y2="16"></line></svg>'
chart_svg = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>'
save_svg = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>'
pr_svg = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="18" r="3"></circle><circle cx="6" cy="6" r="3"></circle><path d="M13 6h3a2 2 0 0 1 2 2v7"></path><line x1="6" y1="9" x2="6" y2="21"></line></svg>'
lock_svg = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:#ec4899;margin-right:6px"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>'

# Find the feature list div and replace exactly inside it using regex
html = re.sub(r'<div class="feature-icon">[^<]+</div>15 vulnerability types detected', f'<div class="feature-icon">{search_svg}</div>15 vulnerability types detected', html)
html = re.sub(r'<div class="feature-icon">[^<]+</div>Gemini AI-powered fixes', f'<div class="feature-icon">{robot_svg}</div>Gemini AI-powered fixes', html)
html = re.sub(r'<div class="feature-icon">[^<]+</div>Real-time security analytics', f'<div class="feature-icon">{chart_svg}</div>Real-time security analytics', html)
html = re.sub(r'<div class="feature-icon">[^<]+</div>Persistent scan history', f'<div class="feature-icon">{save_svg}</div>Persistent scan history', html)
html = re.sub(r'<div class="feature-icon">[^<]+</div>1-click GitHub PR creation', f'<div class="feature-icon">{pr_svg}</div>1-click GitHub PR creation', html)

# Trust badge lock
html = re.sub(r'<div class="trust">[^<]+Secure', f'<div class="trust">{lock_svg}Secure', html)


with open(r'c:\aegisflow\frontend\register.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Done')
