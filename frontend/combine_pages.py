import re

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove sidebar nav item for 'github'
nav_item_pattern = r'    <a class="nav-item" onclick="showPage\(\'github\',this\)">\s*<span class="icon">.*?</svg></span> Scan Repository\s*</a>\n'
content = re.sub(nav_item_pattern, '', content)

# 2. Extract GitHub Input Card
input_card_pattern = r'(          <div class="card">\s*<div class="card-head">\s*<div>\s*<div class="card-title">?? GitHub Repository Scan</div>.*?</button>\s*</div>\s*</div>)'
input_card_match = re.search(input_card_pattern, content, re.DOTALL)
if not input_card_match:
    print("Could not find GitHub Input Card")
input_card = input_card_match.group(1)

# Fix the button style to match the new brand
input_card = input_card.replace('btn-teal', 'btn-primary')
input_card = input_card.replace('?? GitHub Repository Scan', '?? Scan GitHub Repository')

# 3. Extract GitHub Results Card
res_card_pattern = r'(          <div class="card" id="ghSummaryCard" style="display:none">.*?</button>\s*</div>\s*</div>\s*</div>\s*</div>)'
res_card_match = re.search(res_card_pattern, content, re.DOTALL)
if not res_card_match:
    print("Could not find GitHub Results Card")
res_card = res_card_match.group(1)
res_card = res_card.replace('btn-green', 'btn-primary')

# 4. Remove entire page-github
page_github_pattern = r'    <!-- --------------- GITHUB SCAN PAGE --------------- -->\s*<div class="page" id="page-github">.*?</div>\s*</div>\s*</div>'
content = re.sub(page_github_pattern, '', content, flags=re.DOTALL)

# 5. Insert GitHub Input Card into page-scan left column
insert_left_target = r'(        <!-- Upload \+ Code Editor -->\s*<div style="display:flex;flex-direction:column;gap:16px">)'
content = re.sub(insert_left_target, r'\1\n' + input_card + '\n', content)

# 6. Insert GitHub Results Card into page-scan right column
insert_right_target = r'(        <!-- Results Panel -->\s*<div style="display:flex;flex-direction:column;gap:16px;height:100%">)'
content = re.sub(insert_right_target, r'\1\n' + res_card + '\n', content)

# 7. Update page titles logic
titles_pattern = r'const titles = \{ dashboard:\'Dashboard\', scan:\'New Scan\', github:\'Scan Repository\','
content = content.replace(titles_pattern, "const titles = { dashboard:'Dashboard', scan:'Scanner', github:'Scan Repository',")

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Success!")
