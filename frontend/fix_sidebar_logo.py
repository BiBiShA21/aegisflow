import re

with open(r'c:\aegisflow\frontend\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('style="height: 60px;', 'style="height: 120px;')

with open(r'c:\aegisflow\frontend\index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Sidebar logo size updated!')
