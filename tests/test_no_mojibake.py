import os
import re
import pytest

def test_no_mojibake_in_source_code():
    mojibake_patterns = [
        r'Ã[^O\n\r]', # Ã not followed by O
        r'Â',
        r'â€',
        r'\uFFFD'
    ]
    failures = []
    for root, _, files in os.walk('.'):
        if any(ignored in root for ignored in ['.git', '__pycache__', 'node_modules', '.venv', '.pytest_cache']):
            continue
        for file in files:
            if file.endswith(('.py', '.js', '.md', '.html', '.json', '.txt')):
                filepath = os.path.join(root, file)
                if 'test_no_mojibake.py' in filepath or 'fix_mojibake.py' in filepath:
                    continue
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for p in mojibake_patterns:
                            if re.search(p, content):
                                failures.append(f'{filepath} contains mojibake matching: {p}')
                except Exception:
                    pass
    assert not failures, "Mojibake found:\\n" + "\\n".join(failures)
