import os
import re

def test_no_mojibake_in_source_code():
    mojibake_patterns = [
        '\u00C3[^O\n\r]',
        '\u00C2',
        '\u00E2\u20AC',
        '\uFFFD'
    ]

    failures = []
    ignored_exts = ('.exe', '.dll', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.pyc', '.pyd', '.zip', '.db', '.pdf', '.ttf', '.woff', '.woff2', '.bin', '.dat', '.mp3', '.mp4', '.sqlite', '.log', '.pkg')
    ignored_dirs = ['.git', '__pycache__', 'node_modules', '.venv', '.pytest_cache', 'build', 'dist', 'dados']

    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        for file in files:
            if file.endswith(ignored_exts):
                continue

            filepath = os.path.join(root, file)
            if 'test_no_mojibake.py' in filepath or 'fix_mojibake.py' in filepath:
                continue

            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                for p in mojibake_patterns:
                    if re.search(p, content):
                        failures.append(f'{filepath} contains mojibake matching: {p}')

    assert not failures, "Mojibake found:\\n" + "\\n".join(failures)
