import sys

with open('modules/core/cleanup_service.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
with open('modules/core/cleanup_service.py', 'w', encoding='utf-8') as f:
    for line in lines:
        f.write(line.rstrip() + '\n')
