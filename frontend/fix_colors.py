import re

def update_colors(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Feature text color (light gray to text-main)
    content = content.replace('color:#cbd5e1', 'color:var(--text-main)')
    
    # 2. Subtitle text color (dark gray to text-muted)
    content = content.replace('color:#94a3b8', 'color:var(--text-muted)')
    
    # 3. Trust badge text color (darker gray to text-muted)
    content = content.replace('color:#64748b', 'color:var(--text-muted)')
    
    # 4. Any leftover cyan colors in CSS
    content = content.replace('color:#06b6d4', 'color:#ec4899')
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

update_colors(r'c:\aegisflow\frontend\login.html')
update_colors(r'c:\aegisflow\frontend\register.html')

print('Colors updated to CSS variables!')
