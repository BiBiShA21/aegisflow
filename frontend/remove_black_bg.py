import re

def remove_black_bg(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace('; background-color: #000000;', '')
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

remove_black_bg(r'c:\aegisflow\frontend\login.html')
remove_black_bg(r'c:\aegisflow\frontend\register.html')

print('Black backgrounds removed!')
