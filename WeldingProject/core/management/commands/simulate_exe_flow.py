"""
CLI simulation: EXE စီးဆင်းမှု စစ်ဆေးခြင်း (Customer PC မှာ EXE ပဲ ရှိသလို စစ်မယ်)
Run: python manage.py simulate_exe_flow [--base-url http://127.0.0.1:8000] [--start-server] [--start-exe]
- Server ပြေးနေရင် ထို server ကို HTTP နဲ့ စစ်မယ် (browser မလို)
- --start-server: runserver စပြီး စစ်မယ်
- --start-exe: HoBoPOS_Release\\HoBoPOS.exe စပြီး စစ်မယ် (Windows, EXE build ပြီးမှ)
Customer PC မှာ Python/repo မရှိ - EXE နဲ့ data folder ပဲ ရှိတာကို ထည့်စဉ်းစားပြီး ဒီ flow အတိုင်း အဆင်ပြေမပြေ စစ်ပါတယ်။
"""
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path as PathLib
from django.core.management.base import BaseCommand


def _safe_str(s):
    try:
        return str(s).encode('ascii', 'replace').decode('ascii')
    except Exception:
        return str(s)[:80]


def http_get(base_url, path, token=None, timeout=10):
    url = base_url.rstrip('/') + path
    req = urllib.request.Request(url, method='GET')
    if token:
        req.add_header('Authorization', 'Bearer %s' % token)
    req.add_header('Accept', 'application/json')
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.getcode(), r.read().decode('utf-8', errors='replace')


def http_post_json(base_url, path, data, timeout=10):
    url = base_url.rstrip('/') + path
    body = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=body, method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Accept', 'application/json')
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.getcode(), r.read().decode('utf-8', errors='replace')


def wait_for_port(host='127.0.0.1', port=8000, timeout=60, interval=0.5):
    import socket
    start = time.time()
    while time.time() - start < timeout:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((host, port))
            s.close()
            return True
        except (socket.error, OSError):
            time.sleep(interval)
    return False


class Command(BaseCommand):
    help = 'CLI simulation: EXE flow (health, register, login, API). No browser. Optional: --start-server or --start-exe.'

    def add_arguments(self, parser):
        parser.add_argument('--base-url', default='http://127.0.0.1:8000', help='Backend base URL')
        parser.add_argument('--start-server', action='store_true', help='Start runserver in subprocess, then run checks')
        parser.add_argument('--start-exe', action='store_true', help='Start HoBoPOS.exe (Windows), then run checks')
        parser.add_argument('--exe-path', default=None, help='Path to HoBoPOS.exe (default: repo HoBoPOS_Release)')
        parser.add_argument('--test-403', action='store_true', help='Test license blocked 403 (run simulate_errors then expect 403)')

    def log(self, msg, style='HTTP_INFO'):
        out = _safe_str(msg)
        self.stdout.write(getattr(self.style, style, self.style.HTTP_INFO)(out))

    def run_checks(self, base_url):
        err_count = 0
        token = None

        # 1) Health
        self.log('\n[1] GET /health/', 'WARNING')
        try:
            code, body = http_get(base_url, '/health/', timeout=8)
            if code != 200:
                self.log('  FAIL: status %s' % code, 'ERROR')
                err_count += 1
            else:
                self.log('  OK: %s' % code, 'SUCCESS')
        except urllib.error.URLError as e:
            self.log('  FAIL: %s' % _safe_str(e), 'ERROR')
            err_count += 1
            return err_count

        # 2) License status (no auth)
        self.log('\n[2] GET /api/license/status/', 'WARNING')
        try:
            code, body = http_get(base_url, '/api/license/status/', timeout=8)
            if code != 200:
                self.log('  FAIL: status %s' % code, 'ERROR')
                err_count += 1
            else:
                data = json.loads(body)
                self.log('  OK: can_use=%s status=%s' % (data.get('can_use'), data.get('status')), 'SUCCESS')
        except Exception as e:
            self.log('  FAIL: %s' % _safe_str(e), 'ERROR')
            err_count += 1

        # 3) Register (first user)
        self.log('\n[3] POST /api/core/register/', 'WARNING')
        payload = {
            'username': 'cli_sim_user',
            'email': 'cli_sim@test.local',
            'password': 'cli_sim_pass_123',
            'password_confirm': 'cli_sim_pass_123',
            'full_name': 'CLI Sim User',
        }
        try:
            code, body = http_post_json(base_url, '/api/core/register/', payload, timeout=8)
            if code in (200, 201):
                self.log('  OK: registered', 'SUCCESS')
            elif code == 400:
                j = json.loads(body)
                if 'username' in str(j).lower() and 'already' in str(j).lower():
                    self.log('  OK: user exists (will login)', 'SUCCESS')
                else:
                    self.log('  FAIL: %s %s' % (code, _safe_str(j)), 'ERROR')
                    err_count += 1
            else:
                self.log('  FAIL: %s %s' % (code, body[:200]), 'ERROR')
                err_count += 1
        except Exception as e:
            self.log('  FAIL: %s' % _safe_str(e), 'ERROR')
            err_count += 1
            return err_count

        # 4) Login
        self.log('\n[4] POST /api/token/', 'WARNING')
        try:
            code, body = http_post_json(base_url, '/api/token/', {
                'username': 'cli_sim_user',
                'password': 'cli_sim_pass_123',
            }, timeout=8)
            if code != 200:
                self.log('  FAIL: %s %s' % (code, body[:200]), 'ERROR')
                err_count += 1
                return err_count
            data = json.loads(body)
            token = data.get('access')
            if not token:
                self.log('  FAIL: no access token', 'ERROR')
                err_count += 1
                return err_count
            self.log('  OK: JWT obtained', 'SUCCESS')
        except Exception as e:
            self.log('  FAIL: %s' % _safe_str(e), 'ERROR')
            err_count += 1
            return err_count

        # 5) Shop settings (skip-license path)
        self.log('\n[5] GET /api/core/shop-settings/ (with token)', 'WARNING')
        try:
            code, body = http_get(base_url, '/api/core/shop-settings/', token=token, timeout=8)
            if code != 200:
                self.log('  FAIL: %s (shop-settings should work with token)' % code, 'ERROR')
                err_count += 1
            else:
                self.log('  OK: %s' % code, 'SUCCESS')
        except Exception as e:
            self.log('  FAIL: %s' % _safe_str(e), 'ERROR')
            err_count += 1

        # 6) API that requires license (staff/items)
        self.log('\n[6] GET /api/staff/items/ (with token, license required)', 'WARNING')
        try:
            code, body = http_get(base_url, '/api/staff/items/', token=token, timeout=8)
            if code == 200:
                self.log('  OK: 200 (license OK or trial)', 'SUCCESS')
            elif code == 403:
                try:
                    j = json.loads(body)
                    if j.get('error') == 'license_expired':
                        self.log('  OK: 403 license_expired (expected when license blocked)', 'SUCCESS')
                    else:
                        self.log('  FAIL: 403 %s' % _safe_str(j), 'ERROR')
                        err_count += 1
                except Exception:
                    self.log('  FAIL: 403 without license_expired body', 'ERROR')
                    err_count += 1
            else:
                self.log('  FAIL: %s %s' % (code, body[:200]), 'ERROR')
                err_count += 1
        except Exception as e:
            self.log('  FAIL: %s' % _safe_str(e), 'ERROR')
            err_count += 1

        return err_count

    def handle(self, *args, **options):
        base_url = options['base_url'].rstrip('/')
        start_server = options['start_server']
        start_exe = options['start_exe']
        exe_path = options['exe_path']
        test_403 = options['test_403']

        self.log('========================================', 'MIGRATE_HEADING')
        self.log('HoBo POS - EXE flow CLI simulation', 'MIGRATE_HEADING')
        self.log('(Customer PC = EXE + data only; this checks same flow via HTTP)', 'MIGRATE_HEADING')
        self.log('========================================', 'MIGRATE_HEADING')

        proc = None
        welding_root = PathLib(__file__).resolve().parent.parent.parent.parent
        try:
            if start_exe:
                # Repo root = one level above WeldingProject
                repo_root = welding_root.parent
                exe = exe_path or (repo_root / 'HoBoPOS_Release' / 'HoBoPOS.exe')
                if not PathLib(exe).exists():
                    self.log('EXE not found: %s' % exe, 'ERROR')
                    self.log('Build first: build_exe.bat', 'WARNING')
                    return 1
                self.log('\nStarting EXE: %s' % exe, 'WARNING')
                proc = subprocess.Popen([str(exe)], cwd=str(PathLib(exe).parent), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if not wait_for_port('127.0.0.1', 8000, timeout=45):
                    self.log('EXE did not open port 8000 in time.', 'ERROR')
                    if proc: proc.terminate()
                    return 1
                self.log('EXE listening on 8000.', 'SUCCESS')
            elif start_server:
                self.log('\nStarting runserver...', 'WARNING')
                proc = subprocess.Popen(
                    [sys.executable, 'manage.py', 'runserver', '8000', '--noreload'],
                    cwd=str(welding_root),
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                if not wait_for_port('127.0.0.1', 8000, timeout=30):
                    self.log('Server did not start in time.', 'ERROR')
                    if proc: proc.terminate()
                    return 1
                self.log('Server listening on 8000.', 'SUCCESS')

            if test_403:
                self.log('\n[0] Simulating license expired...', 'WARNING')
                subprocess.run([sys.executable, 'manage.py', 'simulate_errors', '--license-expired'], cwd=str(welding_root), capture_output=True, timeout=15)
                self.log('  Done. Next API call should get 403.', 'HTTP_INFO')

            err_count = self.run_checks(base_url)

            if test_403:
                self.log('\n[7] Reset license...', 'WARNING')
                subprocess.run([sys.executable, 'manage.py', 'simulate_errors', '--reset-license'], cwd=str(welding_root), capture_output=True, timeout=15)
                self.log('  Done.', 'SUCCESS')

            self.log('\n========================================', 'MIGRATE_HEADING')
            if err_count == 0:
                self.log('EXE flow simulation: ALL CHECKS PASSED.', 'SUCCESS')
            else:
                self.log('EXE flow simulation: %s error(s). Fix and re-run.' % err_count, 'ERROR')
            self.log('========================================', 'MIGRATE_HEADING')
            return 0 if err_count == 0 else 1
        finally:
            if proc:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()


