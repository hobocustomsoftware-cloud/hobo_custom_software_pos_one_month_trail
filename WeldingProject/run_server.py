"""
HoBo POS - Windows .exe entry point.
Run this with PyInstaller; when double-clicked, starts Django + opens browser to /app/
EXE mode: DB is encrypted at rest (machine_id key) so copied files cannot be used on another PC.
"""
import os
import sys
import webbrowser
import threading
import time
import hashlib
import base64
import platform
import uuid
from pathlib import Path

def _is_frozen():
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def _machine_id_for_key(exe_dir):
    """EXE အတွက် machine ID (Django မလိုဘဲ) — license.utils နဲ့ ကိုက်ညီအောင်"""
    env_id = os.environ.get('MACHINE_ID', '').strip()
    if env_id:
        return hashlib.sha256(env_id.encode()).hexdigest()[:64]
    file_path = Path(exe_dir) / 'data' / 'machine_id'
    try:
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                stored = f.read().strip()
            if stored:
                return stored
        file_path.parent.mkdir(parents=True, exist_ok=True)
        raw = f"{platform.node()}-{os.environ.get('COMPUTERNAME', '')}" if platform.system() == 'Windows' else platform.node()
        raw += str(uuid.getnode())
        mid = hashlib.sha256(raw.encode()).hexdigest()[:64]
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(mid)
        return mid
    except Exception:
        raw = f"{platform.node()}-{uuid.getnode()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:64]


def _derive_db_key(machine_id):
    """Fernet key (32 bytes) from machine_id"""
    key = hashlib.pbkdf2_hmac('sha256', machine_id.encode(), b'hobopos_db_salt', 100_000)[:32]
    return base64.urlsafe_b64encode(key).decode()


def _decrypt_db(exe_dir):
    """db.sqlite3.enc ရှိရင် decrypt လုပ်ပြီး db.sqlite3 ဖန်တီးမယ်"""
    enc = Path(exe_dir) / 'db.sqlite3.enc'
    db = Path(exe_dir) / 'db.sqlite3'
    if not enc.exists():
        return
    try:
        from cryptography.fernet import Fernet
        key = _derive_db_key(_machine_id_for_key(exe_dir))
        f = Fernet(key.encode() if isinstance(key, str) else key)
        data = f.decrypt(enc.read_bytes())
        db.write_bytes(data)
    except Exception:
        pass


def _encrypt_db(exe_dir):
    """db.sqlite3 ကို encrypt လုပ်ပြီး db.sqlite3.enc သိမ်းမယ်"""
    db = Path(exe_dir) / 'db.sqlite3'
    enc = Path(exe_dir) / 'db.sqlite3.enc'
    if not db.exists():
        return
    try:
        from cryptography.fernet import Fernet
        key = _derive_db_key(_machine_id_for_key(exe_dir))
        f = Fernet(key.encode() if isinstance(key, str) else key)
        enc.write_bytes(f.encrypt(db.read_bytes()))
        db.unlink()
    except Exception:
        pass


def main():
    exe_dir = None
    if _is_frozen():
        exe_dir = Path(sys.executable).resolve().parent
        os.environ['HOBOPOS_DB_DIR'] = str(exe_dir)
        os.chdir(sys._MEIPASS)
        _decrypt_db(exe_dir)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WeldingProject.settings')

    import django
    django.setup()

    from django.core.management import call_command

    print('Running migrations...')
    call_command('migrate', '--run-syncdb')

    def open_browser():
        time.sleep(1.2)
        webbrowser.open('http://127.0.0.1:8000/app/')

    threading.Thread(target=open_browser, daemon=True).start()

    try:
        from waitress import serve
        from WeldingProject.wsgi import application
        # Low-spec (2GB RAM / Celeron): set HOBOPOS_LOW_RAM=1 to use 2 threads and reduce memory
        threads = 4
        if os.environ.get('HOBOPOS_LOW_RAM', '').strip().lower() in ('1', 'true', 'yes'):
            threads = 2
        print('HoBo POS starting at http://127.0.0.1:8000/app/')
        print('Browser will open automatically. Close this window to stop the server.')
        serve(application, host='127.0.0.1', port=8000, threads=threads)
    except ImportError:
        from django.core.management import call_command
        call_command('runserver', '127.0.0.1:8000', '--noreload')
    finally:
        if _is_frozen() and exe_dir is not None:
            _encrypt_db(exe_dir)

if __name__ == '__main__':
    main()
