import re

with open(r'c:\aegisflow\frontend\login.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update text gradient
html = html.replace('linear-gradient(90deg,#06b6d4,#22d3ee)', 'linear-gradient(90deg,#ec4899,#8b5cf6)')

# 2. Update shield icon color
html = html.replace('stroke="#06b6d4"', 'stroke="#ec4899"')

# 3. Add toggle button to top right
sun_svg = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"></circle><path d="M12 2v2"></path><path d="M12 20v2"></path><path d="m4.93 4.93 1.41 1.41"></path><path d="m17.66 17.66 1.41 1.41"></path><path d="M2 12h2"></path><path d="M20 12h2"></path><path d="m6.34 17.66-1.41 1.41"></path><path d="m19.07 4.93-1.41 1.41"></path></svg>'
moon_svg = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"></path></svg>'

btn_html = f'''  <!-- Theme Toggle -->
  <button id="themeToggle" onclick="toggleTheme()" style="position: absolute; top: 20px; right: 20px; z-index: 100; border: 1px solid var(--surface-border); background: var(--surface); padding: 8px 12px; border-radius: 9999px; color: var(--text-main); cursor: pointer; display: flex; align-items: center; gap: 8px; font-size: 12px; font-weight: 500; backdrop-filter: blur(10px);">
    {sun_svg} Light Mode
  </button>'''

if 'id="themeToggle"' not in html:
    html = html.replace('<body>', '<body>\n' + btn_html)

# 4. Update JS logic
html = re.sub(r"btn\.innerHTML = '[^']+ Dark Mode';", f"btn.innerHTML = '{moon_svg} Dark Mode';", html)
html = re.sub(r"btn\.innerHTML = '[^']+ Light Mode';", f"btn.innerHTML = '{sun_svg} Light Mode';", html)
html = re.sub(r"btn\.innerHTML = savedTheme === 'light' \? '[^']+' : '[^']+';", f"btn.innerHTML = savedTheme === 'light' ? '{moon_svg} Dark Mode' : '{sun_svg} Light Mode';", html)


with open(r'c:\aegisflow\frontend\login.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Done')
