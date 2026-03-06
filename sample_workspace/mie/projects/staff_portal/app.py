#!/usr/bin/env python3
"""
Staff Portal Rin — bon-soleil internal tools gateway
SQLite auth (no PostgreSQL dependency)
"""
import os
import sys
import subprocess
import signal
import json
import glob
import re
import shlex
import sqlite3
import bcrypt
from functools import wraps
from datetime import datetime, timezone

from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask, redirect, url_for, send_from_directory, request, Response, jsonify, session
from flask_session import Session
from flask_wtf.csrf import CSRFProtect, generate_csrf
from markupsafe import escape

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# --- Config ---
DB_PATH = os.path.expanduser('~/workspace/projects/rag/users.db')
SECRET_KEY_FILE = os.path.expanduser('~/.config/staff-auth/secret_key')
try:
    app.secret_key = open(SECRET_KEY_FILE).read().strip()
except Exception as e:
    import logging
    logging.critical(f"Secret key file not found: {e}. Using ephemeral key — sessions will not persist across restarts!")
    app.secret_key = os.urandom(32)

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sessions')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600
app.config['SESSION_COOKIE_NAME'] = 'staff_rin_session'
app.config['WTF_CSRF_TIME_LIMIT'] = 3600
app.config['WTF_CSRF_SECRET_KEY'] = app.secret_key
app.config["WTF_CSRF_SSL_STRICT"] = False
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20MB

csrf = CSRFProtect(app)
Session(app)

@app.after_request
def set_csrf_cookie(response):
    response.set_cookie('csrf_token', generate_csrf())
    return response

# --- Paths ---
PRESETS_DIR = os.path.expanduser('~/workspace/skills/nanobanana/presets')
CHARSHEETS_DIR = os.path.expanduser('~/workspace/assets/charsheets')
CRON_JOBS_FILE = os.path.expanduser('~/.openclaw/cron/jobs.json')
DISCUSSIONS_DIR = os.path.expanduser('~/workspace/documents')
EXCLUDED_CHARS = {'dao_de_jing', 'lotus_sutra', 'pali_canon'}
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
VIEWER_MAP = {
    '.md': ('md', 'fa-brands fa-markdown', '#8be9fd'),
    '.glb': ('3d', 'fa-solid fa-cube', '#50fa7b'),
    '.gltf': ('3d', 'fa-solid fa-cube', '#50fa7b'),
}

# --- Auth helpers ---
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def verify_password(username, password):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT password_hash, role FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        if not row:
            return None
        password_hash, role = row['password_hash'], row['role']
        if bcrypt.checkpw(password.encode(), password_hash.encode()):
            return {'username': username, 'role': role}
        return None
    finally:
        conn.close()

def require_auth(f):  # auth disabled
    return f  # noqa
    # original below
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated

def get_current_user():
    return {'username': session.get('username', ''), 'role': session.get('role', 'viewer')}

# --- CSS & shared styles ---
BASE_CSS = """
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #1a1a2e; color: #e0e0e0; min-height: 100vh; }
  .header { background: #16213e; border-bottom: 1px solid #0f3460; padding: 16px 24px;
             display: flex; justify-content: space-between; align-items: center; }
  .header h1 { color: #e94560; font-size: 1.3em; }
  .header .user { color: #888; font-size: 0.9em; }
  .header a { color: #e94560; text-decoration: none; margin-left: 16px; }
  .header a:hover { text-decoration: underline; }
  a { color: #e94560; text-decoration: none; }
  a:hover { text-decoration: underline; }
"""

FA_CDN = '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">'

def header_html(title, back_url=None, back_label=None):
    user = get_current_user()
    back = f'<a href="{back_url}"><i class="fa-solid fa-arrow-left"></i> {back_label}</a>' if back_url else ''
    return f"""<div class="header">
  <h1><i class="fa-solid fa-shield-halved"></i> {title}</h1>
  <div>
    {back}
    <span class="user">{user['username']} ({user['role']})</span>
    <a href="/staff/logout"><i class="fa-solid fa-right-from-bracket"></i> Logout</a>
  </div>
</div>"""

# --- Login / Logout ---
@app.route('/staff/login', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = verify_password(username, password)
        if user:
            session.clear()
            session.permanent = True
            session['username'] = user['username']
            session['role'] = user['role']
            next_url = request.args.get('next') or '/staff/'
            if next_url.startswith('http') or '//' in next_url:
                next_url = '/staff/'
            return redirect(next_url)
        error = 'Invalid username or password'

    return f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Staff Login</title>
{FA_CDN}
<style>
  {BASE_CSS}
  body {{ display: flex; align-items: center; justify-content: center; }}
  .login-box {{ background: #16213e; border: 1px solid #0f3460; border-radius: 12px; padding: 40px; width: 360px; }}
  .login-box h1 {{ color: #e94560; text-align: center; margin-bottom: 8px; font-size: 1.3em; }}
  .login-box p {{ color: #888; text-align: center; margin-bottom: 24px; font-size: 0.9em; }}
  .field {{ margin-bottom: 16px; }}
  .field label {{ display: block; color: #aaa; font-size: 0.85em; margin-bottom: 6px; }}
  .field input {{ width: 100%; padding: 10px 14px; background: #0f3460; border: 1px solid {'#e94560' if error else '#1a4a8a'};
                  border-radius: 6px; color: #e0e0e0; font-size: 1em; outline: none; }}
  .field input:focus {{ border-color: #e94560; }}
  .btn {{ width: 100%; padding: 12px; background: #e94560; color: white; border: none; border-radius: 6px;
          font-size: 1em; font-weight: 600; cursor: pointer; margin-top: 8px; }}
  .btn:hover {{ background: #c73652; }}
  .error {{ color: #e94560; font-size: 0.85em; text-align: center; margin-top: 12px; }}
</style>
</head><body>
<div class="login-box">
  <h1>🐱 Staff Portal</h1>
  <p>bon-soleil Rin internal</p>
  <form method="post">
    <input type="hidden" name="csrf_token" value="{generate_csrf()}">
    <div class="field">
      <label>Username</label>
      <input type="text" name="username" autofocus autocomplete="username">
    </div>
    <div class="field">
      <label>Password</label>
      <input type="password" name="password" autocomplete="current-password">
    </div>
    <button type="submit" class="btn">Login</button>
    {'<div class="error">' + error + '</div>' if error else ''}
  </form>
</div>
</body></html>"""

@app.route('/staff/logout')
def logout():
    session.clear()
    return redirect('/staff/login')

# --- Dashboard ---
@app.route('/staff/')
@require_auth
def index():
    user = get_current_user()
    return f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Staff Portal — bon-soleil Rin</title>
{FA_CDN}
<style>
  {BASE_CSS}
  .tools {{ max-width: 800px; margin: 40px auto; padding: 0 24px; }}
  .tools h2 {{ color: #aaa; font-size: 1em; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 2px; }}
  .tool-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }}
  .tool {{ background: #16213e; border: 1px solid #0f3460; border-radius: 8px; padding: 20px;
           text-decoration: none; color: #e0e0e0; transition: border-color 0.2s; display: block; }}
  .tool:hover {{ border-color: #e94560; }}
  .tool i {{ font-size: 1.5em; color: #e94560; margin-bottom: 8px; display: block; }}
  .tool .name {{ font-weight: 600; margin-bottom: 4px; }}
  .tool .desc {{ color: #888; font-size: 0.85em; }}
</style>
</head><body>
{header_html('Staff Portal')}
<div class="tools">
  <h2>Internal Tools</h2>
  <div class="tool-grid">
    <a href="/ragmyadmin/" class="tool">
      <i class="fa-solid fa-database"></i>
      <div class="name">ragMyAdmin</div>
      <div class="desc">ChromaDB RAG management</div>
    </a>
    <a href="/staff/documents/" class="tool">
      <i class="fa-solid fa-comments"></i>
      <div class="name">Documents</div>
      <div class="desc">Meeting notes, reviews & docs</div>
    </a>
    <a href="/staff/services/" class="tool">
      <i class="fa-solid fa-server"></i>
      <div class="name">Services</div>
      <div class="desc">Server process management</div>
    </a>
    <a href="/staff/crons/" class="tool">
      <i class="fa-solid fa-clock"></i>
      <div class="name">Cron Jobs</div>
      <div class="desc">Scheduled task management</div>
    </a>
    <a href="/staff/characters/" class="tool">
      <i class="fa-solid fa-users"></i>
      <div class="name">Characters</div>
      <div class="desc">Character sheets & generation presets</div>
    </a>
    <a href="http://127.0.0.1:18789/" target="_blank" class="tool">
      <i class="fa-solid fa-network-wired"></i>
      <div class="name">OpenClaw Gateway</div>
      <div class="desc">Gateway dashboard (local only)</div>
    </a>
  </div>
</div>
</body></html>"""

# --- Directory listing helper ---
def _dir_listing(base, subpath, prefix):
    from flask_wtf.csrf import generate_csrf
    csrf = generate_csrf()
    full = os.path.join(base, subpath)
    if not os.path.isdir(full):
        return "Not found", 404
    entries = sorted(os.listdir(full))

    folders, images, files = [], [], []
    for e in entries:
        if e.startswith('.') or e.endswith('.bak'):
            continue
        fp = os.path.join(full, e)
        href = f'/staff/{prefix}/{subpath}{e}'
        ext = os.path.splitext(e)[1].lower()
        if os.path.isdir(fp):
            folders.append(f'<a href="{href}/" class="folder"><i class="fa-solid fa-folder"></i> {e}/</a>')
        elif ext in IMAGE_EXTS:
            images.append(f'''<a href="{href}" class="thumb" target="_blank">
              <img src="{href}" loading="lazy" alt="{e}">
              <span>{e}</span></a>''')
        elif ext in VIEWER_MAP:
            viewer, icon, color = VIEWER_MAP[ext]
            viewer_href = f'/staff/viewer/{viewer}?file={href}'
            files.append(f'<a href="{viewer_href}" class="file" style="color:{color}"><i class="{icon}"></i> {e}</a>')
        else:
            files.append(f'<a href="{href}" class="file"><i class="fa-solid fa-file"></i> {e}</a>')

    parent = f'/staff/{prefix}/{subpath}../' if subpath else f'/staff/{prefix}/'
    up_link = f'<a href="{parent}" style="color:#8be9fd;text-decoration:none"><i class="fa-solid fa-level-up-alt"></i> Up</a>' if subpath else ''

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{prefix}/{subpath}</title>
{FA_CDN}
<style>
  {BASE_CSS}
  .container {{ padding: 24px; }}
  .subnav {{ display: flex; gap: 16px; margin-bottom: 20px; align-items: center; }}
  h1 {{ color: #e94560; font-size: 1.2em; margin-bottom: 20px; }}
  .folders {{ margin-bottom: 20px; }}
  .folder {{ color: #8be9fd; text-decoration: none; display: inline-block; padding: 6px 16px 6px 0; }}
  .folder:hover {{ text-decoration: underline; }}
  .folder i {{ margin-right: 6px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; margin-bottom: 20px; }}
  .thumb {{ display: block; background: #16213e; border: 1px solid #0f3460; border-radius: 8px;
            overflow: hidden; text-decoration: none; transition: border-color 0.2s; }}
  .thumb:hover {{ border-color: #e94560; }}
  .thumb img {{ width: 100%; height: 200px; object-fit: cover; display: block; }}
  .thumb span {{ display: block; padding: 8px; color: #aaa; font-size: 0.8em; white-space: nowrap;
                 overflow: hidden; text-overflow: ellipsis; }}
  .file {{ color: #e94560; text-decoration: none; display: block; padding: 4px 0; }}
  .file:hover {{ text-decoration: underline; }}
  .file i {{ margin-right: 6px; }}
</style></head><body>
{header_html(prefix, '/staff/', 'Dashboard')}
<div class="container">
  <div class="subnav">{up_link}<label id="upload-btn" style="margin-left:auto;background:#50fa7b;color:#1a1a2e;padding:4px 14px;border-radius:6px;cursor:pointer;font-size:0.85em;font-weight:600;display:none">
    <i class="fa-solid fa-upload"></i> アップロード
    <input type="file" id="upload-input" accept=".txt,.md,.pdf" style="display:none" onchange="uploadDoc(this)">
  </label></div>
  <div id="upload-msg" style="margin-bottom:12px;font-size:0.9em"></div>
  <h1><i class="fa-solid fa-folder-open"></i> {prefix}/{subpath}</h1>
  <div class="folders">{''.join(folders)}</div>
  <div class="grid">{''.join(images)}</div>
  {''.join(files)}
</div>
<script>
const SUBPATH = "{subpath}";
const CSRF_TOKEN = "{csrf}";
if (window.location.pathname.startsWith('/staff/documents')) {{
  document.getElementById('upload-btn').style.display = 'inline-flex';
}}
function uploadDoc(input) {{
  const file = input.files[0];
  if (!file) return;
  const msg = document.getElementById('upload-msg');
  msg.innerHTML = '<span style="color:#8be9fd">アップロード中...</span>';
  const fd = new FormData();
  fd.append('file', file);
  fd.append('subpath', SUBPATH);
  fd.append('csrf_token', CSRF_TOKEN);
  fetch('/staff/api/documents/upload', {{
    method: 'POST',
    body: fd
  }})
    .then(r => r.json())
    .then(d => {{
      if (d.ok) {{
        msg.innerHTML = '<span style="color:#50fa7b">✅ ' + d.filename + ' をアップロードしました</span>';
        setTimeout(() => location.reload(), 1000);
      }} else {{
        msg.innerHTML = '<span style="color:#e94560">❌ ' + d.error + '</span>';
      }}
    }})
    .catch(e => {{ msg.innerHTML = '<span style="color:#e94560">❌ ' + String(e) + '</span>'; }});
}}
</script>
</div>
</body></html>"""

# --- Discussions ---
@app.route('/staff/documents/')
@app.route('/staff/documents/<path:filepath>')
@require_auth
def serve_discussions(filepath=''):
    base = DISCUSSIONS_DIR
    if not filepath or filepath.endswith('/'):
        full = os.path.join(base, filepath or '')
        idx = os.path.join(full, 'index.html')
        if os.path.isfile(idx):
            return send_from_directory(full, 'index.html')
        return _dir_listing(base, filepath, 'documents')
    return send_from_directory(base, filepath)


@app.route('/staff/api/documents/upload', methods=['POST'])
@require_auth
def api_upload_document():
    import mimetypes
    ALLOWED_EXTS = {'.txt', '.md', '.pdf'}
    MAX_SIZE = 20 * 1024 * 1024  # 20MB

    try:
        if 'file' not in request.files:
            return jsonify({'ok': False, 'error': 'No file'}), 400
        f = request.files['file']
        if not f.filename:
            return jsonify({'ok': False, 'error': 'No filename'}), 400

        # ファイル名サニタイズ
        import unicodedata
        filename = f.filename.replace('/', '_').replace('\\', '_').replace('..', '_')
        filename = ''.join(c for c in filename if c.isprintable() and c not in '<>:"|?*')
        filename = filename.strip('. ')
        if not filename:
            return jsonify({'ok': False, 'error': 'Invalid filename'}), 400

        # 拡張子チェック
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTS:
            return jsonify({'ok': False, 'error': f'拡張子 {ext} は許可されていません（.txt .md .pdf のみ）'}), 400

        # サブパス取得（フォルダ内アップロード対応）
        subpath = request.form.get('subpath', '').strip('/')
        if subpath:
            # パストラバーサル対策
            dest_dir = os.path.realpath(os.path.join(DISCUSSIONS_DIR, subpath))
            if not dest_dir.startswith(os.path.realpath(DISCUSSIONS_DIR) + os.sep):
                return jsonify({'ok': False, 'error': 'Access denied'}), 403
        else:
            dest_dir = os.path.realpath(DISCUSSIONS_DIR)

        if not os.path.isdir(dest_dir):
            return jsonify({'ok': False, 'error': 'Destination directory not found'}), 400

        dest_path = os.path.realpath(os.path.join(dest_dir, filename))
        if not dest_path.startswith(dest_dir + os.sep):
            return jsonify({'ok': False, 'error': 'Access denied'}), 403

        # サイズチェック（read前にseekでチェック）
        f.seek(0, 2)
        size = f.tell()
        f.seek(0)
        if size > MAX_SIZE:
            return jsonify({'ok': False, 'error': f'ファイルサイズが大きすぎます（最大10MB）'}), 400

        # 内容読み込み
        data = f.read()

        # マジックバイトで実際の中身を検査
        PDF_MAGIC = b'%PDF'
        if ext == '.pdf':
            if not data.startswith(PDF_MAGIC):
                return jsonify({'ok': False, 'error': 'PDFファイルの形式が正しくありません'}), 400
        else:
            # テキストファイル: バイナリでないか確認
            try:
                data.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    data.decode('shift-jis')
                except UnicodeDecodeError:
                    return jsonify({'ok': False, 'error': 'テキストファイルの文字コードを認識できません'}), 400

        # 保存
        with open(dest_path, 'wb') as out:
            out.write(data)

        return jsonify({'ok': True, 'filename': filename})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

# --- Charsheets ---

# --- HR Charsheets ---
    return send_from_directory(base, filepath)

# --- Characters ---
def _load_all_presets():
    presets = {}
    if not os.path.isdir(PRESETS_DIR):
        return presets
    for fp in sorted(glob.glob(os.path.join(PRESETS_DIR, '*.json'))):
        name = os.path.splitext(os.path.basename(fp))[0]
        try:
            with open(fp) as f:
                presets[name] = json.load(f)
        except Exception:
            pass
    return presets

def _get_charsheet_images(name):
    candidates = [name, name.lower()]
    preset_path = os.path.join(PRESETS_DIR, f'{name}.json')
    if os.path.isfile(preset_path):
        try:
            with open(preset_path) as f:
                p = json.load(f)
            cs = p.get('charsheet', '')
            if cs:
                cs_full = os.path.expanduser(cs)
                cs_dir = os.path.dirname(cs_full)
                if os.path.isdir(cs_dir):
                    dirname = os.path.basename(cs_dir)
                    prefix = 'charsheets'
                    return [f'/staff/{prefix}/{dirname}/{f}' for f in sorted(os.listdir(cs_dir))
                            if os.path.splitext(f)[1].lower() in IMAGE_EXTS]
        except Exception:
            pass
    for dirname in candidates:
        d = os.path.join(CHARSHEETS_DIR, dirname)
        if os.path.isdir(d):
            return [f'/staff/charsheets/{dirname}/{f}' for f in sorted(os.listdir(d))
                    if os.path.splitext(f)[1].lower() in IMAGE_EXTS]
    return []

@app.route('/staff/charsheets/<path:filepath>')
def serve_charsheets_file(filepath=''):
    return send_from_directory(CHARSHEETS_DIR, filepath)


@app.route('/staff/characters/')
@require_auth
def characters_list():
    presets = _load_all_presets()
    charsheet_dirs = set()
    if os.path.isdir(CHARSHEETS_DIR):
        charsheet_dirs = {d for d in os.listdir(CHARSHEETS_DIR)
                          if os.path.isdir(os.path.join(CHARSHEETS_DIR, d))
                          and d not in EXCLUDED_CHARS and not d.startswith('.')}

    cards = []
    for name, data in presets.items():
        images = _get_charsheet_images(name)
        thumb = images[0] if images else ''
        styles = ', '.join(data.get('styles', {}).keys())
        cards.append(f'''<a href="/staff/characters/{name}" class="char-card">
          <div class="char-thumb">{'<img src="' + thumb + '">' if thumb else '<i class="fa-solid fa-user"></i>'}</div>
          <div class="char-info">
            <div class="char-name">{escape(name)}</div>
            <div class="char-styles">{escape(styles) or 'no styles'}</div>
          </div></a>''')

    for d in sorted(charsheet_dirs - set(presets.keys())):
        images = _get_charsheet_images(d)
        thumb = images[0] if images else ''
        cards.append(f'''<a href="/staff/characters/{d}" class="char-card no-preset">
          <div class="char-thumb">{'<img src="' + thumb + '">' if thumb else '<i class="fa-solid fa-user"></i>'}</div>
          <div class="char-info">
            <div class="char-name">{escape(d)}</div>
            <div class="char-styles" style="color:#e94560">no preset</div>
          </div></a>''')

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Characters — Staff Portal</title>
{FA_CDN}
<style>
  {BASE_CSS}
  body {{ padding: 24px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }}
  .char-card {{ display: flex; gap: 12px; background: #16213e; border: 1px solid #0f3460; border-radius: 8px;
                padding: 12px; text-decoration: none; color: #e0e0e0; transition: border-color 0.2s; align-items: center; }}
  .char-card:hover {{ border-color: #e94560; }}
  .char-card.no-preset {{ opacity: 0.6; }}
  .char-thumb {{ width: 64px; height: 64px; border-radius: 8px; overflow: hidden; flex-shrink: 0;
                 background: #0f3460; display: flex; align-items: center; justify-content: center; }}
  .char-thumb img {{ width: 100%; height: 100%; object-fit: cover; }}
  .char-thumb i {{ font-size: 1.5em; color: #555; }}
  .char-name {{ font-weight: 600; font-size: 1.1em; }}
  .char-styles {{ color: #8be9fd; font-size: 0.85em; margin-top: 4px; }}
</style></head><body>
{header_html('Characters', '/staff/', 'Dashboard')}
<div style="padding:24px">
<h1 style="color:#e94560;font-size:1.3em;margin-bottom:24px"><i class="fa-solid fa-users"></i> Characters</h1>
<div class="grid">{''.join(cards)}</div>
</div>
</body></html>"""

@app.route('/staff/characters/<name>')
@require_auth
def character_detail(name):
    preset_path = os.path.join(PRESETS_DIR, f'{name}.json')
    preset = {}
    if os.path.isfile(preset_path):
        with open(preset_path) as f:
            preset = json.load(f)

    images = _get_charsheet_images(name)
    styles = preset.get('styles', {})

    style_cards = []
    for sname, sdata in styles.items():
        model = sdata.get('model', 'default')
        desc = sdata.get('description', '')
        prefix = sdata.get('prompt_prefix', '')
        shortcut = f'python3 ~/workspace/skills/nanobanana/generate.py --preset {name} --style {sname} "YOUR PROMPT" -o ~/workspace/assets/tmp/output.jpg'
        style_cards.append(f'''<div class="style-card">
          <div class="style-header">
            <span class="style-name">{escape(sname)}</span>
            <span class="style-model">{escape(model)}</span>
          </div>
          <div class="style-desc">{escape(desc)}</div>
          <div class="style-prefix">{escape(prefix[:200])}</div>
          <div class="shortcut">
            <code>{escape(shortcut)}</code>
            <button onclick="navigator.clipboard.writeText(this.previousElementSibling.textContent)" title="Copy">
              <i class="fa-solid fa-copy"></i>
            </button>
          </div>
        </div>''')

    def img_filename(img):
        return img.split('/')[-1]
    img_html = ''.join(f'''<div class="img-card" id="img-{img_filename(img)}">
      <a href="{img}" target="_blank"><img src="{img}" loading="lazy"></a>
      <button class="del-btn" onclick="deleteImage('{img_filename(img)}')" title="削除"><i class="fa-solid fa-trash"></i></button>
    </div>''' for img in images)

    csrf_token = generate_csrf()
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(name)} — Characters</title>
{FA_CDN}
<style>
  {BASE_CSS}
  body {{ padding: 24px; }}
  h1 {{ color: #e94560; font-size: 1.3em; margin-bottom: 8px; }}
  .char-desc {{ color: #aaa; margin-bottom: 24px; line-height: 1.6; }}
  h2 {{ color: #8be9fd; font-size: 1em; margin: 24px 0 12px; text-transform: uppercase; letter-spacing: 1px; }}
  .gallery {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; margin-bottom: 24px; }}
  .img-card {{ position: relative; }}
  .img-card img {{ width: 100%; height: 180px; object-fit: cover; border-radius: 8px; border: 1px solid #0f3460; }}
  .img-card a:hover img {{ border-color: #e94560; }}
  .img-card {{ position: relative; }}
  .del-btn {{ display: none; position: absolute; top: 6px; right: 6px; background: rgba(233,69,96,0.9);
              color: white; border: none; border-radius: 6px; padding: 4px 8px; cursor: pointer; font-size: 0.85em; }}
  .img-card:hover .del-btn {{ display: block; }}
  .style-card {{ background: #16213e; border: 1px solid #0f3460; border-radius: 8px; padding: 16px; margin-bottom: 12px; }}
  .style-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
  .style-name {{ font-weight: 700; color: #50fa7b; font-size: 1.1em; }}
  .style-model {{ color: #bd93f9; font-size: 0.85em; background: #0f3460; padding: 2px 8px; border-radius: 4px; }}
  .style-desc {{ color: #ccc; margin-bottom: 6px; }}
  .style-prefix {{ color: #888; font-size: 0.85em; font-style: italic; margin-bottom: 10px; }}
  .shortcut {{ display: flex; align-items: center; gap: 8px; background: #0d1117; padding: 8px 12px; border-radius: 6px; overflow-x: auto; }}
  .shortcut code {{ color: #8be9fd; font-size: 0.8em; white-space: nowrap; }}
  .shortcut button {{ background: none; border: none; color: #888; cursor: pointer; padding: 4px; }}
  .shortcut button:hover {{ color: #e94560; }}
  .json-section {{ margin-top: 24px; }}
  .json-toggle {{ color: #e94560; cursor: pointer; font-size: 0.9em; }}
  .json-editor {{ display: none; margin-top: 8px; }}
  .json-editor textarea {{ width: 100%; min-height: 300px; background: #0d1117; color: #e0e0e0; border: 1px solid #0f3460;
                           border-radius: 6px; padding: 12px; font-family: monospace; font-size: 0.85em; resize: vertical; }}
  .save-btn {{ margin-top: 8px; padding: 8px 16px; background: #50fa7b; color: #1a1a2e; border: none; border-radius: 6px;
               font-weight: 600; cursor: pointer; }}
  .save-btn:hover {{ background: #3dd66b; }}
  .msg {{ margin-top: 8px; font-size: 0.9em; }}
</style></head><body>
{header_html(escape(name), '/staff/characters/', 'Characters')}
<div style="padding:24px">
<h1><i class="fa-solid fa-user"></i> {escape(name)}</h1>
<div class="char-desc">{escape(preset.get('character', 'No preset defined'))}</div>

<h2><i class="fa-solid fa-images"></i> Reference Images
  <label style="margin-left:12px;background:#e94560;color:#fff;padding:4px 12px;border-radius:6px;cursor:pointer;font-size:0.8em;font-weight:600;">
    <i class="fa-solid fa-upload"></i> Upload
    <input type="file" accept="image/*" style="display:none" onchange="uploadImage(this)">
  </label>
</h2>
<div class="gallery" id="gallery">{img_html if img_html else '<em style="color:#888">No images found</em>'}</div>

<h2><i class="fa-solid fa-wand-magic-sparkles"></i> Styles & Shortcuts</h2>
{''.join(style_cards) if style_cards else '<em style="color:#888">No styles defined</em>'}

<div class="json-section">
  <span class="json-toggle" onclick="let e=document.getElementById('json-ed');e.style.display=e.style.display==='none'?'block':'none'">
    <i class="fa-solid fa-code"></i> Edit JSON
  </span>
  <div class="json-editor" id="json-ed">
    <textarea id="json-raw">{escape(json.dumps(preset, ensure_ascii=False, indent=2))}</textarea>
    <button class="save-btn" onclick="savePreset()"><i class="fa-solid fa-floppy-disk"></i> Save</button>
    <div class="msg" id="save-msg"></div>
  </div>
</div>

<script>
const CSRF_TOKEN = '{csrf_token}';
function deleteImage(filename) {{
  if (!confirm('「' + filename + '」を削除しますか？')) return;
  fetch('/staff/api/characters/{escape(name)}/image/' + filename, {{
    method: 'DELETE',
    headers: {{'X-CSRFToken': CSRF_TOKEN}}
  }})
    .then(r => r.json())
    .then(d => {{
      if (d.ok) {{
        const el = document.getElementById('img-' + filename);
        if (el) el.remove();
      }} else {{
        alert('削除失敗: ' + d.error);
      }}
    }})
    .catch(e => alert('Error: ' + e));
}}
function uploadImage(input) {{
  const file = input.files[0];
  if (!file) return;
  const fd = new FormData();
  fd.append('file', file);
  fd.append('csrf_token', CSRF_TOKEN);
  fetch('/staff/api/characters/{escape(name)}/upload', {{
    method: 'POST',
    headers: {{'X-CSRFToken': CSRF_TOKEN}},
    body: fd
  }})
    .then(r => r.json())
    .then(d => {{
      if (d.ok) {{
        const img = document.createElement('div');
        img.className = 'img-card';
        img.innerHTML = '<a href="/staff/charsheets/{escape(name)}/'+d.filename+'" target="_blank"><img src="/staff/charsheets/{escape(name)}/'+d.filename+'" loading="lazy"></a>';
        document.getElementById('gallery').appendChild(img);
      }} else {{
        alert('Upload failed: ' + d.error);
      }}
    }})
    .catch(e => alert('Error: ' + e));
}}
function savePreset() {{
  const raw = document.getElementById('json-raw').value;
  try {{ JSON.parse(raw); }} catch(e) {{
    document.getElementById('save-msg').innerHTML = '<span style="color:#e94560">Invalid JSON: '+e+'</span>';
    return;
  }}
  fetch('/staff/api/characters/{escape(name)}', {{
    method: 'PUT',
    headers: {{'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN}},
    body: raw
  }})
    .then(r => r.json())
    .then(d => {{ document.getElementById('save-msg').innerHTML = d.ok ? '<span style="color:#50fa7b">Saved!</span>' : '<span style="color:#e94560">'+d.error+'</span>'; }})
    .catch(e => {{ document.getElementById('save-msg').innerHTML = '<span style="color:#e94560">'+e+'</span>'; }});
}}
</script>
</div>
</body></html>"""

@app.route('/staff/api/characters/<name>', methods=['PUT'])
@require_auth
def api_save_preset(name):
    try:
        if not re.match(r'^[a-zA-Z0-9_\-]+$', name):
            return jsonify({'ok': False, 'error': 'Invalid name'}), 400
        preset_path = os.path.realpath(os.path.join(PRESETS_DIR, f'{name}.json'))
        if not preset_path.startswith(os.path.realpath(PRESETS_DIR) + os.sep):
            return jsonify({'ok': False, 'error': 'Access denied'}), 403
        data = request.get_json()
        if not data or 'character' not in data:
            return jsonify({'ok': False, 'error': 'Invalid data'}), 400
        with open(preset_path, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/staff/api/characters/<name>/image/<filename>', methods=['DELETE'])
@require_auth
def api_delete_charsheet(name, filename):
    try:
        if not re.match(r'^[a-zA-Z0-9_\-]+$', name):
            return jsonify({'ok': False, 'error': 'Invalid name'}), 400
        dest_dir = os.path.realpath(os.path.join(CHARSHEETS_DIR, name))
        file_path = os.path.realpath(os.path.join(dest_dir, filename))
        if not file_path.startswith(dest_dir + os.sep):
            return jsonify({'ok': False, 'error': 'Access denied'}), 403
        if not os.path.isfile(file_path):
            return jsonify({'ok': False, 'error': 'File not found'}), 404
        os.remove(file_path)
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/staff/api/characters/<name>/upload', methods=['POST'])
@require_auth
def api_upload_charsheet(name):
    try:
        if not re.match(r'^[a-zA-Z0-9_\-]+$', name):
            return jsonify({'ok': False, 'error': 'Invalid name'}), 400
        if 'file' not in request.files:
            return jsonify({'ok': False, 'error': 'No file'}), 400
        f = request.files['file']
        if not f.filename:
            return jsonify({'ok': False, 'error': 'No filename'}), 400
        ext = os.path.splitext(f.filename)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            return jsonify({'ok': False, 'error': 'Invalid file type'}), 400
        dest_dir = os.path.join(CHARSHEETS_DIR, name)
        os.makedirs(dest_dir, exist_ok=True)
        filename = f.filename.replace('/', '_')
        dest_path = os.path.realpath(os.path.join(dest_dir, filename))
        if not dest_path.startswith(os.path.realpath(dest_dir)):
            return jsonify({'ok': False, 'error': 'Access denied'}), 403
        f.save(dest_path)
        return jsonify({'ok': True, 'filename': filename})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


# --- Viewers ---
@app.route('/staff/viewer/md')
@require_auth
def viewer_md():
    file_path = request.args.get('file', '')
    if not file_path:
        return "No file specified", 400
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(file_path.split('/')[-1])}</title>
{FA_CDN}
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.5.0/github-markdown-dark.min.css">
<style>
  body {{ background: #1a1a2e; color: #e0e0e0; padding: 24px; font-family: -apple-system, sans-serif; }}
  .nav {{ margin-bottom: 20px; }}
  .nav a {{ color: #e94560; text-decoration: none; margin-right: 16px; }}
  .markdown-body {{ max-width: 900px; margin: 0 auto; padding: 24px; background: #16213e; border-radius: 8px; }}
</style>
</head><body>
<div class="nav">
  <a href="javascript:history.back()"><i class="fa-solid fa-arrow-left"></i> Back</a>
  <a href="{escape(file_path)}" download><i class="fa-solid fa-download"></i> Raw</a>
</div>
<div class="markdown-body"><div style="color:#888;text-align:center;padding:40px">Loading...</div></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/11.1.1/marked.min.js"></script>
<script>
fetch("{escape(file_path)}")
  .then(r => r.text())
  .then(md => {{ document.querySelector('.markdown-body').innerHTML = marked.parse(md); }})
  .catch(e => {{ document.querySelector('.markdown-body').innerHTML = '<p style="color:#e94560">Failed: ' + e + '</p>'; }});
</script>
</body></html>"""

@app.route('/staff/viewer/3d')
@require_auth
def viewer_3d():
    file_path = request.args.get('file', '')
    if not file_path:
        return "No file specified", 400
    fname = escape(file_path.split('/')[-1])
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{fname}</title>
<script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.5.0/model-viewer.min.js"></script>
{FA_CDN}
<style>
  body {{ background: #1a1a2e; color: #e0e0e0; padding: 24px; margin: 0; }}
  .nav {{ margin-bottom: 20px; padding: 0 24px; }}
  .nav a {{ color: #e94560; text-decoration: none; margin-right: 16px; }}
  h1 {{ color: #e94560; font-size: 1.2em; margin: 0 24px 16px; }}
  model-viewer {{ width: 100%; height: calc(100vh - 120px); background: #0d1117; border-radius: 8px; }}
</style>
</head><body>
<div class="nav">
  <a href="javascript:history.back()"><i class="fa-solid fa-arrow-left"></i> Back</a>
  <a href="{escape(file_path)}" download><i class="fa-solid fa-download"></i> Download</a>
</div>
<h1><i class="fa-solid fa-cube"></i> {fname}</h1>
<model-viewer src="{escape(file_path)}" auto-rotate camera-controls shadow-intensity="1"
  environment-image="neutral" exposure="1"></model-viewer>
</body></html>"""

# --- Services (macOS launchd) ---
SERVICES = [
    {"name": "openclaw-gateway", "type": "launchd", "label": "ai.openclaw.gateway", "port": None, "desc": "OpenClaw Gateway"},
    {"name": "staff-portal", "type": "launchd", "label": "com.bonsoleil.staff-portal", "port": 8795, "desc": "Staff Portal (this app)"},
    {"name": "ragmyadmin", "type": "launchd", "label": "com.bonsoleil.ragmyadmin", "port": 8792, "desc": "ragMyAdmin (ChromaDB)"},
    {"name": "ragapi", "type": "launchd", "label": "com.bonsoleil.ragapi", "port": 8500, "desc": "RAG API"},
]

def _get_service_status(svc):
    info = {"name": svc["name"], "desc": svc["desc"], "type": svc["type"], "port": svc.get("port")}
    if svc["type"] == "launchd":
        try:
            r = subprocess.run(["launchctl", "list", svc["label"]], capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                info["status"] = "active"
                for line in r.stdout.split("\n"):
                    if '"PID"' in line or line.strip().startswith('"PID"'):
                        try:
                            pid = int(line.split("=")[1].strip().rstrip(";"))
                            if pid > 0:
                                info["pid"] = pid
                                info["memory_mb"] = _get_pid_memory_mac(pid)
                        except Exception:
                            pass
            else:
                info["status"] = "inactive"
        except Exception:
            info["status"] = "unknown"
    else:
        pid = _find_pid_by_port_mac(svc["port"])
        if pid:
            info["status"] = "active"
            info["pid"] = pid
            info["memory_mb"] = _get_pid_memory_mac(pid)
        else:
            info["status"] = "inactive"
    return info

def _find_pid_by_port_mac(port):
    try:
        r = subprocess.run(["lsof", "-i", f":{port}", "-t", "-sTCP:LISTEN"], capture_output=True, text=True, timeout=5)
        pids = r.stdout.strip().split("\n")
        if pids and pids[0]:
            return int(pids[0])
    except Exception:
        pass
    return None

def _get_pid_memory_mac(pid):
    try:
        r = subprocess.run(["ps", "-o", "rss=", "-p", str(pid)], capture_output=True, text=True, timeout=5)
        rss_kb = int(r.stdout.strip())
        return rss_kb // 1024
    except Exception:
        return None

def _service_action_mac(svc, action):
    if action not in ("start", "stop", "restart"):
        return False, "Invalid action"
    if svc["type"] == "launchd":
        plist = os.path.expanduser(f'~/Library/LaunchAgents/{svc["label"]}.plist')
        if not os.path.isfile(plist):
            return False, f"plist not found: {plist}"
        try:
            if action == "stop":
                r = subprocess.run(["launchctl", "unload", plist], capture_output=True, text=True, timeout=15)
            elif action == "start":
                r = subprocess.run(["launchctl", "load", plist], capture_output=True, text=True, timeout=15)
            elif action == "restart":
                subprocess.run(["launchctl", "unload", plist], capture_output=True, text=True, timeout=10)
                import time; time.sleep(2)
                r = subprocess.run(["launchctl", "load", plist], capture_output=True, text=True, timeout=15)
            if r.returncode == 0:
                return True, f"{action} OK"
            return False, r.stderr.strip() or f"{action} failed"
        except Exception as e:
            return False, str(e)
    else:
        pid = _find_pid_by_port_mac(svc["port"])
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
                return True, f"Sent SIGTERM to {pid}"
            except Exception as e:
                return False, str(e)
        return False, "Not running"

def _get_system_stats_mac():
    mem_total = mem_used = mem_avail = 0
    try:
        r = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=5)
        mem_total_bytes = int(r.stdout.strip())
        mem_total = mem_total_bytes // (1024 * 1024)
        r2 = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=5)
        page_size = 4096
        stats = {}
        for line in r2.stdout.split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                try:
                    stats[k.strip()] = int(v.strip().rstrip("."))
                except Exception:
                    pass
        free_pages = stats.get("Pages free", 0) + stats.get("Pages speculative", 0)
        mem_avail = (free_pages * page_size) // (1024 * 1024)
        mem_used = mem_total - mem_avail
    except Exception:
        pass
    disk_total = disk_used = disk_avail = 0
    try:
        r = subprocess.run(["df", "-m", "/"], capture_output=True, text=True, timeout=5)
        parts = r.stdout.strip().split("\n")[1].split()
        disk_total = int(parts[1])
        disk_used = int(parts[2])
        disk_avail = int(parts[3])
    except Exception:
        pass
    return mem_total, mem_used, mem_avail, disk_total, disk_used, disk_avail

@app.route('/staff/services/')
@require_auth
def services_page():
    user = get_current_user()
    is_admin = user.get('role') == 'admin'
    services = [_get_service_status(s) for s in SERVICES]
    mem_total, mem_used, mem_avail, disk_total, disk_used, disk_avail = _get_system_stats_mac()
    mem_pct = round(mem_used / mem_total * 100) if mem_total else 0
    disk_pct = round(disk_used / disk_total * 100) if disk_total else 0
    disk_total_gb = round(disk_total / 1024, 1)
    disk_used_gb = round(disk_used / 1024, 1)
    disk_avail_gb = round(disk_avail / 1024, 1)

    rows = ""
    for s in services:
        status_icon = "🟢" if s["status"] == "active" else "🔴"
        mem_str = f'{s["memory_mb"]} MB' if s.get("memory_mb") else "—"
        port_str = str(s["port"]) if s.get("port") else "—"
        pid_str = str(s.get("pid", "—"))
        buttons = ""
        if is_admin:
            if s["status"] == "active":
                buttons = f'''<button class="btn btn-stop" onclick="svcAction('{s["name"]}','stop')"><i class="fa-solid fa-stop"></i></button>
                             <button class="btn btn-restart" onclick="svcAction('{s["name"]}','restart')"><i class="fa-solid fa-rotate-right"></i></button>'''
            else:
                buttons = f'''<button class="btn btn-start" onclick="svcAction('{s["name"]}','start')"><i class="fa-solid fa-play"></i></button>'''
        action_col = f'<td>{buttons}</td>' if is_admin else ''
        rows += f'''<tr class="{'active' if s['status'] == 'active' else 'inactive'}">
            <td>{status_icon} {s["name"]}</td><td>{s["desc"]}</td><td>{port_str}</td>
            <td>{pid_str}</td><td>{mem_str}</td><td>{s["type"]}</td>{action_col}</tr>'''

    csrf_token = generate_csrf()
    mem_color = "#e94560" if mem_pct > 80 else "#4ecca3"
    disk_color = "#e94560" if disk_pct > 80 else "#4ecca3"

    return f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Services — Staff Portal</title>
{FA_CDN}
<style>
  {BASE_CSS}
  .container {{ max-width: 1000px; margin: 24px auto; padding: 0 24px; }}
  .bar-wrap {{ background: #0f3460; border-radius: 8px; height: 24px; margin: 12px 0; position: relative; overflow: hidden; }}
  .bar-fill {{ height: 100%; border-radius: 8px; transition: width 0.3s; }}
  .bar-label {{ position: absolute; top: 3px; left: 12px; font-size: 0.8em; font-weight: 600; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
  th {{ background: #16213e; color: #aaa; padding: 10px 8px; text-align: left; font-size: 0.85em;
       text-transform: uppercase; letter-spacing: 1px; border-bottom: 1px solid #0f3460; }}
  td {{ padding: 10px 8px; border-bottom: 1px solid #0f3460; font-size: 0.9em; }}
  tr.active td:first-child {{ color: #4ecca3; }}
  tr.inactive td:first-child {{ color: #e94560; }}
  .btn {{ border: none; border-radius: 4px; padding: 6px 10px; cursor: pointer; color: #fff; font-size: 0.8em; margin: 0 2px; }}
  .btn-stop {{ background: #e94560; }}
  .btn-start {{ background: #4ecca3; }}
  .btn-restart {{ background: #e9a045; }}
  #toast {{ display: none; position: fixed; bottom: 24px; right: 24px; background: #16213e;
           border: 1px solid #0f3460; border-radius: 8px; padding: 12px 20px; font-size: 0.9em; z-index: 999; }}
</style>
</head><body>
{header_html('Services', '/staff/', 'Dashboard')}
<div class="container">
  <div class="bar-wrap">
    <div class="bar-fill" style="width:{mem_pct}%;background:{mem_color}"></div>
    <div class="bar-label"><i class="fa-solid fa-memory"></i> Memory: {mem_used} / {mem_total} MB ({mem_pct}%) — Available: {mem_avail} MB</div>
  </div>
  <div class="bar-wrap">
    <div class="bar-fill" style="width:{disk_pct}%;background:{disk_color}"></div>
    <div class="bar-label"><i class="fa-solid fa-hard-drive"></i> Disk: {disk_used_gb} / {disk_total_gb} GB ({disk_pct}%) — Available: {disk_avail_gb} GB</div>
  </div>
  <table>
    <tr><th>Service</th><th>Description</th><th>Port</th><th>PID</th><th>Memory</th><th>Type</th>{"<th>Actions</th>" if is_admin else ""}</tr>
    {rows}
  </table>
</div>
<div id="toast"></div>
<script>
async function svcAction(name, action) {{
  const toast = document.getElementById('toast');
  toast.style.display = 'block';
  toast.textContent = action + 'ing ' + name + '...';
  try {{
    const r = await fetch('/staff/api/services/' + name + '/' + action, {{
      method: 'POST', headers: {{'X-CSRFToken': '{csrf_token}'}}
    }});
    const d = await r.json();
    toast.textContent = d.ok ? '✅ ' + name + ': ' + d.message : '❌ ' + d.message;
    setTimeout(() => location.reload(), 1500);
  }} catch(e) {{
    toast.textContent = '❌ Error: ' + e.message;
  }}
  setTimeout(() => {{ toast.style.display = 'none'; }}, 3000);
}}
</script>
</body></html>"""

@app.route('/staff/api/services/<name>/<action>', methods=['POST'])
@require_auth
def api_service_action(name, action):
    user = get_current_user()
    if user.get('role') != 'admin':
        return jsonify({"ok": False, "message": "Admin only"}), 403
    svc = next((s for s in SERVICES if s["name"] == name), None)
    if not svc:
        return jsonify({"ok": False, "message": "Service not found"}), 404
    if action not in {"start", "stop", "restart"}:
        return jsonify({"ok": False, "message": "Invalid action"}), 400
    if name == "staff-portal" and action == "stop":
        return jsonify({"ok": False, "message": "Cannot stop self"}), 400
    ok, msg = _service_action_mac(svc, action)
    return jsonify({"ok": ok, "message": msg})

# --- Cron Jobs ---
def _load_cron_jobs():
    try:
        with open(CRON_JOBS_FILE) as f:
            data = json.load(f)
        return data.get('jobs', [])
    except Exception:
        return []

@app.route('/staff/crons/')
@require_auth
def crons_page():
    user = get_current_user()
    is_admin = user.get('role') == 'admin'
    jobs = _load_cron_jobs()

    rows = ""
    for j in sorted(jobs, key=lambda x: x.get('name', '')):
        enabled = j.get('enabled', False)
        status_icon = "🟢" if enabled else "🔴"
        name = j.get('name', j.get('id', '?'))
        schedule = j.get('schedule', {})
        sched_kind = schedule.get('kind', '?')
        if sched_kind == 'cron':
            sched_str = f"<code>{schedule.get('expr', '?')}</code>"
            tz = schedule.get('tz', 'UTC')
            if tz != 'UTC':
                sched_str += f" <small>({tz})</small>"
        elif sched_kind == 'at':
            sched_str = f"at {schedule.get('at', '?')[:16]}"
        elif sched_kind == 'every':
            ms = schedule.get('everyMs', 0)
            sched_str = f"every {ms // 60000}m"
        else:
            sched_str = sched_kind

        state = j.get('state', {})
        next_run = state.get('nextRunAtMs')
        last_run = state.get('lastRunAtMs')
        last_status = state.get('lastStatus', '—')
        last_dur = state.get('lastDurationMs')

        next_str = datetime.fromtimestamp(next_run / 1000, tz=timezone.utc).strftime('%m/%d %H:%M UTC') if next_run else '—'
        last_str = datetime.fromtimestamp(last_run / 1000, tz=timezone.utc).strftime('%m/%d %H:%M UTC') if last_run else '—'
        dur_str = f"{last_dur // 1000}s" if last_dur else '—'
        status_cls = 'ok' if last_status == 'ok' else 'err' if last_status not in ('ok', '—') else ''
        target = j.get('sessionTarget', '?')
        delete_after = '🗑️' if j.get('deleteAfterRun') else ''
        job_id = j.get('id', '')
        toggle_label = 'Disable' if enabled else 'Enable'
        toggle_icon = 'fa-pause' if enabled else 'fa-play'
        toggle_cls = 'btn-stop' if enabled else 'btn-start'
        enabled_js = 'false' if enabled else 'true'
        action_td = f'<td><button class="btn {toggle_cls}" onclick="cronToggle(\'{job_id}\',{enabled_js})" title="{toggle_label}"><i class="fa-solid {toggle_icon}"></i></button></td>' if is_admin else ''
        rows += f"""<tr class="{'enabled' if enabled else 'disabled'}">
            <td>{status_icon} {name} {delete_after}</td>
            <td>{sched_str}</td><td>{next_str}</td><td>{last_str}</td>
            <td class="{status_cls}">{last_status}</td><td>{dur_str}</td><td>{target}</td>{action_td}</tr>"""

    enabled_count = sum(1 for j in jobs if j.get('enabled'))
    disabled_count = len(jobs) - enabled_count
    csrf_token = generate_csrf()

    return f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cron Jobs — Staff Portal</title>
{FA_CDN}
<style>
  {BASE_CSS}
  .container {{ max-width: 1100px; margin: 24px auto; padding: 0 24px; }}
  .summary {{ display: flex; gap: 16px; margin-bottom: 20px; }}
  .stat {{ background: #16213e; border: 1px solid #0f3460; border-radius: 8px; padding: 16px 20px; flex: 1; text-align: center; }}
  .stat .num {{ font-size: 2em; font-weight: 700; }}
  .stat .label {{ color: #888; font-size: 0.85em; margin-top: 4px; }}
  .stat.active .num {{ color: #4ecca3; }}
  .stat.inactive .num {{ color: #e94560; }}
  .stat.total .num {{ color: #e9a045; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ background: #16213e; color: #aaa; padding: 10px 8px; text-align: left; font-size: 0.8em;
       text-transform: uppercase; letter-spacing: 1px; border-bottom: 1px solid #0f3460; }}
  td {{ padding: 10px 8px; border-bottom: 1px solid #0f3460; font-size: 0.85em; }}
  tr.disabled {{ opacity: 0.5; }}
  td.ok {{ color: #4ecca3; }}
  td.err {{ color: #e94560; }}
  code {{ background: #0f3460; padding: 2px 6px; border-radius: 4px; font-size: 0.85em; }}
  small {{ color: #666; }}
  .btn {{ border: none; border-radius: 4px; padding: 6px 10px; cursor: pointer; color: #fff; font-size: 0.8em; }}
  .btn-stop {{ background: #e94560; }}
  .btn-start {{ background: #4ecca3; }}
</style>
</head><body>
{header_html('Cron Jobs', '/staff/', 'Dashboard')}
<div class="container">
  <div class="summary">
    <div class="stat total"><div class="num">{len(jobs)}</div><div class="label">Total Jobs</div></div>
    <div class="stat active"><div class="num">{enabled_count}</div><div class="label">Enabled</div></div>
    <div class="stat inactive"><div class="num">{disabled_count}</div><div class="label">Disabled</div></div>
  </div>
  <table>
    <tr><th>Job</th><th>Schedule</th><th>Next Run</th><th>Last Run</th><th>Status</th><th>Duration</th><th>Target</th>{"<th>Actions</th>" if is_admin else ""}</tr>
    {rows}
  </table>
</div>
<div id="toast" style="display:none;position:fixed;bottom:24px;right:24px;background:#16213e;border:1px solid #0f3460;border-radius:8px;padding:12px 20px;font-size:0.9em;z-index:999"></div>
<script>
async function cronToggle(jobId, enable) {{
  const toast = document.getElementById('toast');
  toast.style.display = 'block';
  toast.textContent = (enable ? 'Enabling' : 'Disabling') + '...';
  try {{
    const r = await fetch('/staff/api/crons/' + jobId + '/toggle', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json', 'X-CSRFToken': '{csrf_token}'}},
      body: JSON.stringify({{enabled: enable}})
    }});
    const d = await r.json();
    toast.textContent = d.ok ? '✅ ' + d.message : '❌ ' + d.message;
    setTimeout(() => location.reload(), 1000);
  }} catch(e) {{
    toast.textContent = '❌ ' + e.message;
  }}
  setTimeout(() => {{ toast.style.display = 'none'; }}, 3000);
}}
</script>
</body></html>"""

@app.route('/staff/api/crons/<job_id>/toggle', methods=['POST'])
@require_auth
def api_cron_toggle(job_id):
    user = get_current_user()
    if user.get('role') != 'admin':
        return jsonify({"ok": False, "message": "Admin only"}), 403
    try:
        data = request.get_json()
        enabled = data.get('enabled', True)
        with open(CRON_JOBS_FILE) as f:
            cron_data = json.load(f)
        jobs = cron_data.get('jobs', [])
        found = next((j for j in jobs if j.get('id') == job_id), None)
        if not found:
            return jsonify({"ok": False, "message": "Job not found"}), 404
        found['enabled'] = enabled
        with open(CRON_JOBS_FILE, 'w') as f:
            json.dump(cron_data, f, indent=2, ensure_ascii=False)
        return jsonify({"ok": True, "message": f"{'Enabled' if enabled else 'Disabled'}: {found.get('name', job_id)}"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8795, debug=False)
