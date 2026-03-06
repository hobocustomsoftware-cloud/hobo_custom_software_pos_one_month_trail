"""
License utilities: machine_id, license validation
- Server (Docker): MACHINE_ID env or persistent file (volume)
- Installation: platform-based (hostname, etc.)
"""
import hashlib
import platform
import uuid
import os
import json
from pathlib import Path

# Django settings - optional for standalone use
try:
    from django.conf import settings
    _BASE_DIR = Path(settings.BASE_DIR)
except Exception:
    _BASE_DIR = Path(__file__).resolve().parent.parent


def _get_machine_id_file_path():
    """machine_id သိမ်းမည့်ဖိုင် (EXE: HOBOPOS_DB_DIR, Docker: volume)"""
    data_dir = os.environ.get('HOBOPOS_DB_DIR')
    if data_dir:
        return Path(data_dir) / 'data' / 'machine_id'
    return _BASE_DIR / 'data' / 'machine_id'


def get_machine_id():
    """
    စက်ကို ခွဲခြားသတ်မှတ်ရန် unique ID
    Priority: 1) MACHINE_ID env  2) data/machine_id file  3) platform-based
    """
    # 1. Env (Docker: MACHINE_ID=xxx သတ်မှတ်ထားနိုင်သည်)
    env_id = os.environ.get('MACHINE_ID', '').strip()
    if env_id:
        return hashlib.sha256(env_id.encode()).hexdigest()[:64]

    # 2. Persistent file (Docker volume - container restart လုပ်ရင်လည်း မပြောင်း)
    file_path = _get_machine_id_file_path()
    try:
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                stored = f.read().strip()
            if stored:
                return stored
        # First run: generate and save
        file_path.parent.mkdir(parents=True, exist_ok=True)
        mid = _generate_platform_machine_id()
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(mid)
        return mid
    except Exception:
        pass

    # 3. Platform-based (Installation - no file/env)
    return _generate_platform_machine_id()


def _generate_platform_machine_id():
    """Platform မှ machine ID ထုတ်ခြင်း"""
    try:
        if platform.system() == 'Windows':
            raw = f"{platform.node()}-{os.environ.get('COMPUTERNAME', '')}"
        else:
            raw = platform.node()
        raw += str(uuid.getnode())
        return hashlib.sha256(raw.encode()).hexdigest()[:64]
    except Exception:
        return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:64]


def get_license_file_path():
    """license.lic ဖိုင်ကို ဘယ်မှာ သိမ်းမလဲ (EXE: HOBOPOS_DB_DIR)"""
    data_dir = os.environ.get('HOBOPOS_DB_DIR')
    if data_dir:
        return Path(data_dir) / 'license.lic'
    return _BASE_DIR / 'license.lic'


def load_license_from_file():
    """
    license.lic ဖိုင်မှ ဖတ်ခြင်း (On-Premise offline)
    """
    path = get_license_file_path()
    if not path.exists():
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception:
        return None


def save_license_to_file(license_key, machine_id, license_type, expires_at=None):
    """license.lic ဖိုင်သို့ သိမ်းခြင်း"""
    path = get_license_file_path()
    exp_str = None
    if expires_at:
        exp_str = expires_at.isoformat() if hasattr(expires_at, 'isoformat') else str(expires_at)
    data = {
        'license_key': license_key,
        'machine_id': machine_id,
        'license_type': license_type,
        'expires_at': exp_str,
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    return path
