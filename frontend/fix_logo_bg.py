import re

def update_logo(filename, old_str, new_str):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace(old_str, new_str)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

update_logo(r'c:\aegisflow\frontend\login.html', 'style="height: 280px;"', 'style="height: 280px; background-color: #000000;"')
update_logo(r'c:\aegisflow\frontend\register.html', 'style="height: 200px;"', 'style="height: 280px; background-color: #000000;"')

print('Logos updated with black background and matching size')
