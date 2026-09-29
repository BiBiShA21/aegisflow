import os
import re

css_overrides = """
/* ==============================================================
   PREMIUM GLASSMORPHIC THEME OVERRIDES
   ============================================================== */
:root {
  --bg: #09090b;
  --surface: rgba(24, 24, 27, 0.4);
  --surface-border: rgba(255, 255, 255, 0.08);
  --surface-hover: rgba(255, 255, 255, 0.05);
  --text-main: #ffffff;
  --text-muted: #a1a1aa;
  --text-secondary: #e4e4e7;
  --accent-primary: #8b5cf6;
  --accent-secondary: #ec4899;
  --accent-tertiary: #3b82f6;
  --glow-op: 0.15;
}

[data-theme="light"] {
  --bg: #f8fafc;
  --surface: rgba(255, 255, 255, 0.8);
  --surface-border: rgba(0, 0, 0, 0.05);
  --surface-hover: rgba(0, 0, 0, 0.02);
  --text-main: #0f172a;
  --text-muted: #64748b;
  --text-secondary: #334155;
  --glow-op: 0.1;
}

body {
  font-family: 'Inter', sans-serif !important;
  background-color: var(--bg) !important;
  color: var(--text-main) !important;
  transition: background-color 0.4s ease, color 0.4s ease;
}

/* Ambient Glows */
.ambient-glow {
  position: fixed; border-radius: 50%; filter: blur(120px); z-index: -1;
  opacity: var(--glow-op); transition: opacity 0.4s ease; pointer-events: none;
}
.glow-1 { top: -10%; left: -10%; width: 50vw; height: 50vw; background: var(--accent-tertiary); }
.glow-2 { bottom: -20%; right: -10%; width: 60vw; height: 60vw; background: var(--accent-primary); }
.glow-3 { top: 30%; left: 40%; width: 40vw; height: 40vw; background: var(--accent-secondary); }

/* Overrides for index.html elements */
.sidebar, .topbar, .card, .stat-card, .toast, .notif-dropdown, .auth-card, .table-container, .code-editor-head {
  background: var(--surface) !important;
  backdrop-filter: blur(20px) !important;
  -webkit-backdrop-filter: blur(20px) !important;
  border-color: var(--surface-border) !important;
  color: var(--text-main) !important;
}

.card-head, .topbar, .sidebar-brand, .sidebar-user, .auth-card { border-color: var(--surface-border) !important; }
.topbar-left h1, .brand-name, .card-title, .user-name, .stat-value, .upload-title, .vuln-title, .info-value, .notif-head, .hero-title, .auth-card h1 { color: var(--text-main) !important; }
.topbar-left p, .nav-item, .card-sub, .upload-sub, .vuln-desc, .text-muted, .empty-title, .empty-sub, .stat-label, .profile-role, .profile-stat-label, .hero-desc, .auth-card p { color: var(--text-muted) !important; }

.nav-item:hover, .user-card:hover, .settings-item:hover, .history-table tr:hover td { background: var(--surface-hover) !important; }

/* Remove old dark mode classes to avoid conflicts */
body.dark-mode { background-color: var(--bg) !important; color: var(--text-main) !important; }

/* Buttons */
.btn-primary, .btn-teal, .btn-coral, .btn-green {
  border-radius: 9999px !important;
  border: none !important;
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)) !important;
  color: white !important;
}
.btn-primary:hover, .btn-teal:hover, .btn-coral:hover, .btn-green:hover {
  background: linear-gradient(135deg, #7c3aed, #db2777) !important;
  box-shadow: 0 4px 15px rgba(236, 72, 153, 0.4) !important;
}

/* Text Inputs */
.search-box, .edit-input, select, .form-input {
  background: rgba(255, 255, 255, 0.03) !important;
  border-color: var(--surface-border) !important;
  color: var(--text-main) !important;
  backdrop-filter: blur(10px);
}
.search-box input, .form-input { color: var(--text-main) !important; }

/* History Table overrides */
.history-table th { background: rgba(0,0,0,0.05) !important; border-color: var(--surface-border) !important; color: var(--text-muted) !important; }
.history-table td { border-color: var(--surface-border) !important; color: var(--text-secondary) !important; }

/* Left Auth Section */
.left { background: transparent !important; }
.left::before, .left::after { display: none !important; }

"""

font_link = '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Outfit:wght@500;600;700&display=swap" rel="stylesheet">'
ambient_glow_html = """
  <!-- Ambient Background -->
  <div class="ambient-glow glow-1"></div>
  <div class="ambient-glow glow-2"></div>
  <div class="ambient-glow glow-3"></div>
"""

theme_toggle_html = """
      <button class="icon-btn" id="themeToggle" onclick="toggleTheme()" style="border:none;background:var(--surface);backdrop-filter:blur(10px);width:auto;padding:0 12px;font-size:12px;border-radius:9999px;color:var(--text-main)">
        🌞 Light Mode
      </button>
"""

js_override = """
    // Theme Toggling Logic
    function toggleTheme() {
      const html = document.documentElement;
      const btn = document.getElementById('themeToggle');
      if (html.getAttribute('data-theme') === 'dark') {
        html.setAttribute('data-theme', 'light');
        if(btn) btn.innerHTML = '🌙 Dark Mode';
        localStorage.setItem('aegisflow-theme', 'light');
      } else {
        html.setAttribute('data-theme', 'dark');
        if(btn) btn.innerHTML = '🌞 Light Mode';
        localStorage.setItem('aegisflow-theme', 'dark');
      }
    }

    const savedTheme = localStorage.getItem('aegisflow-theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    window.addEventListener('DOMContentLoaded', () => {
        const btn = document.getElementById('themeToggle');
        if(btn) {
           btn.innerHTML = savedTheme === 'light' ? '🌙 Dark Mode' : '🌞 Light Mode';
        }
    });
"""


for filename in ["index.html", "login.html", "register.html"]:
    path = os.path.join("c:\\aegisflow\\frontend", filename)
    if not os.path.exists(path): continue
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # 1. Update <head> font and Add data-theme to <html>
    if "data-theme" not in content:
        content = content.replace('<html lang="en">', '<html lang="en" data-theme="dark">')
    if "fonts.googleapis.com" not in content:
        content = content.replace("<title>", font_link + "\n<title>")
        
    # 2. Add CSS Overrides to end of <style>
    if "PREMIUM GLASSMORPHIC THEME OVERRIDES" not in content:
        content = content.replace("</style>", css_overrides + "\n</style>")
        
    # 3. Insert Ambient Glows right after <body>
    if "ambient-glow" not in content:
        content = content.replace("<body>", "<body>\n" + ambient_glow_html)
        
    # 4. Insert Theme Toggle button in Topbar (index.html only)
    if filename == "index.html" and "id=\"themeToggle\"" not in content:
        # insert before <div class="notif-btn"...>
        content = content.replace('<div class="notif-btn"', theme_toggle_html + '\n      <div class="notif-btn"')
        
    # 5. Insert JS logic right before </body>
    if "toggleTheme()" not in content or "function toggleTheme()" not in content:
        content = content.replace("</body>", "<script>\n" + js_override + "\n</script>\n</body>")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Updated {filename}")
