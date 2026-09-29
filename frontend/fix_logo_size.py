import re

def update_logo_size(filename, old_str, new_str):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace(old_str, new_str)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

update_logo_size(r'c:\aegisflow\frontend\index.html', 'style="height: 40px;', 'style="height: 60px;')
update_logo_size(r'c:\aegisflow\frontend\login.html', 'style="height: 180px;', 'style="height: 280px;')
update_logo_size(r'c:\aegisflow\frontend\register.html', 'style="height: 120px;', 'style="height: 200px;')

print('Logo sizes updated!')
