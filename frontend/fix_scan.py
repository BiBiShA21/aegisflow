import re

with open(r'c:\aegisflow\frontend\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = re.sub(r'(<span class="icon">.*?</span>)\s*New Scan', r'\1 Scan', html)
html = re.sub(r'(<button class="quick-btn new-scan".*?>.*?</svg>)\s*New Scan(</button>)', r'\1 Scan\2', html)

with open(r'c:\aegisflow\frontend\index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Done')
