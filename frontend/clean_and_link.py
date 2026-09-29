import os
import re

for filename in ["index.html", "login.html", "register.html"]:
    path = os.path.join("c:\\aegisflow\\frontend", filename)
    if not os.path.exists(path): continue
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Add the stylesheet link if not present
    if "theme.css" not in content:
        content = content.replace("</head>", '  <link rel="stylesheet" href="theme.css">\n</head>')
        
    # Remove old inline body backgrounds
    content = re.sub(r'body\s*{[^}]*background:[^;]+;[^}]*}', 'body{font-family: \'Inter\', sans-serif;}', content)
    content = re.sub(r'body\s*{[^}]*background-color:[^;]+;[^}]*}', 'body{font-family: \'Inter\', sans-serif;}', content)
    
    # Remove the .left gradient entirely from login and register to be 100% sure
    content = re.sub(r'\.left\s*{[^}]*}', '.left { flex: 0 0 45%; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px; position: relative; z-index: 10; }', content)
    content = re.sub(r'\.left::before\s*{[^}]*}', '', content)
    content = re.sub(r'\.left::after\s*{[^}]*}', '', content)
    content = re.sub(r'\.right\s*{[^}]*}', '.right { flex: 1; display: flex; align-items: center; justify-content: center; padding: 60px 40px; z-index: 10; position: relative; }', content)

    # In case there are multiple ambient glows injected due to repeated script runs, fix it:
    # Remove all ambient-glow divs
    content = re.sub(r'<div class="ambient-glow[^>]+></div>', '', content)
    
    # Re-insert EXACTLY once
    glows = """
  <!-- Ambient Background -->
  <div class="ambient-glow glow-1"></div>
  <div class="ambient-glow glow-2"></div>
  <div class="ambient-glow glow-3"></div>
"""
    content = content.replace("<body>", "<body>\n" + glows)
    
    # Save back
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"Cleaned and linked theme.css in {filename}")
