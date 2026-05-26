import json
import py_compile
from pathlib import Path

required_files = [
    'main.py', 'menu.py', 'add_device.py', 'add_log.py',
    'equipment_profile.py', 'database.py', 'export_tools.py', 'buildozer.spec', 'icon.png'
]

missing = [name for name in required_files if not Path(name).exists()]
if missing:
    raise SystemExit('Missing required file(s): ' + ', '.join(missing))

for py_file in Path('.').glob('*.py'):
    if py_file.name == 'prebuild_check.py':
        continue
    py_compile.compile(str(py_file), doraise=True)

with open('survey_equipment_db.json', 'r', encoding='utf-8') as f:
    json.load(f)

spec = Path('buildozer.spec').read_text(encoding='utf-8')
for required_line in ['requirements = python3,kivy', 'android.minapi = 24', 'android.ndk_api = 24', 'android.release_artifact = apk']:
    if required_line not in spec:
        raise SystemExit(f'buildozer.spec missing: {required_line}')

print('Prebuild check passed: Python files compile, JSON is valid, required files exist, and Android API is set to 24.')
