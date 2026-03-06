#!/usr/bin/env python3
"""agent@example.com の新着メールをチェック
- 要対応メール（VIP送信者/オーナー）→ OpenClawセッションを起動してエージェントが自律処理
- その他 → Telegram通知のみ

セキュリティ対策:
- ロックファイルによる重複実行防止（冪等性）
- メール本文のサニタイズ（文字数制限）
- SPF/DKIM/DMARC検証（Authentication-Resultsヘッダ、信頼チェーン考慮）
- UIDVALIDITY変化の検知
- エラーハンドリング＋Telegram通知
- 添付ファイルサイズ・タイプ制限
- 構造化監査ログ（JSON Lines）
"""

import imaplib, email, json, os, sys, time, subprocess, re, fcntl
from email.header import decode_header
from pathlib import Path
from datetime import datetime, timezone, timedelta

MAIL_CONFIG = Path(os.path.expanduser("~/.config/mail/akiko.json"))
STATE_FILE = Path(os.path.expanduser("~/.config/mail/last_seen_uid.txt"))
UIDVALIDITY_FILE = Path(os.path.expanduser("~/.config/mail/uidvalidity.txt"))
LOCK_FILE = Path(os.path.expanduser("~/.config/mail/check_mail.lock"))
AUDIT_LOG = Path(os.path.expanduser("~/logs/mail_audit.jsonl"))
OPENCLAW_BIN = os.path.expanduser("~/.nvm/versions/node/v24.14.0/bin/openclaw")
OPENCLAW_CONFIG = Path(os.path.expanduser("~/.openclaw/openclaw.json"))
TMP_DIR = Path(os.path.expanduser("~/workspace/assets/tmp"))
TELEGRAM_CHAT_ID = ""

# この送信者からのメールはOpenClawセッションを起動してエージェントが自律処理
AUTO_PROCESS_SENDERS = [
    # "boss@example.com",
    # "client@example.com",
]

# メール本文の最大文字数（プロンプトインジェクション緩和）
MAX_BODY_CHARS = 3000

# system eventに渡すタスクの最大文字数
MAX_TASK_CHARS = 5000

# 添付ファイル制限
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_ATTACHMENT_TYPES = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp",  # 画像
    ".heic", ".heif",                                    # iPhone写真
}

# 受信サーバーのホスト名（Authentication-Results の信頼チェーン）
TRUSTED_AUTH_SERVER = ""  # 例: "mx.example.com"

JST = timezone(timedelta(hours=9))


# ─────────────────────────────────────────────
# 監査ログ（JSON Lines）
# ─────────────────────────────────────────────
def audit_log(event, **kwargs):
    """構造化監査ログを記録"""
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(JST).isoformat(),
        "event": event,
        **kwargs
    }
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ─────────────────────────────────────────────
# ロックファイル（冪等性: cron重複実行防止）
# ─────────────────────────────────────────────
class FileLock:
    """fcntl.flock ベースの排他ロック（ローカルFS専用）"""
    def __init__(self, path):
        self.path = path
        self.fd = None

    def acquire(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fd = open(self.path, "w")
        try:
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.fd.write(str(os.getpid()))
            self.fd.flush()
            return True
        except OSError:
            self.fd.close()
            self.fd = None
            return False

    def release(self):
        if self.fd:
            fcntl.flock(self.fd, fcntl.LOCK_UN)
            self.fd.close()
            self.fd = None
            try:
                self.path.unlink()
            except OSError:
                pass


# ─────────────────────────────────────────────
# 通知
# ─────────────────────────────────────────────
def telegram_notify(text):
    """Telegram にテキスト通知を送る"""
    try:
        config = json.load(open(OPENCLAW_CONFIG))
        bot_token = config["channels"]["telegram"]["botToken"]
    except Exception as e:
        print(f"Telegram token error: {e}")
        return
    import urllib.request, urllib.parse
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    clean_text = text.replace("&", "&amp;")
    params = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": clean_text,
        "parse_mode": "HTML"
    }).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(url, data=params), timeout=10)
    except Exception as e:
        print(f"Telegram notify failed: {e}")


def telegram_error(error_msg):
    """エラーをTelegramで通知"""
    telegram_notify(f"⚠️ <b>check_mail.py エラー</b>\n{error_msg}")


# ─────────────────────────────────────────────
# system event
# ─────────────────────────────────────────────
def wake_akiko(task_message):
    """システムイベントを注入してエージェントのメインセッションを即座に起こす"""
    if len(task_message) > MAX_TASK_CHARS:
        task_message = task_message[:MAX_TASK_CHARS] + "\n\n[...メール本文が長いため省略されました]"
    try:
        result = subprocess.run(
            [OPENCLAW_BIN, "system", "event",
             "--text", task_message,
             "--mode", "now"],
            capture_output=True, text=True, timeout=15
        )
        print(f"  → System event sent (exit={result.returncode})")
        if result.stdout.strip():
            print(f"    stdout: {result.stdout[:300]}")
        if result.stderr.strip():
            print(f"    stderr: {result.stderr[:300]}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("  → System event timed out")
        return False
    except Exception as e:
        print(f"  → System event failed: {e}")
        return False


# ─────────────────────────────────────────────
# メールパーサ
# ─────────────────────────────────────────────
def decode_header_value(value):
    if value is None:
        return ""
    parts = decode_header(value)
    return "".join([
        s.decode(e or "utf-8") if isinstance(s, bytes) else s
        for s, e in parts
    ])


def extract_sender_email(from_header):
    match = re.search(r'<([^>]+)>', from_header)
    if match:
        return match.group(1).lower()
    return from_header.strip().lower()


def sanitize_body(body):
    """メール本文をサニタイズ"""
    if len(body) > MAX_BODY_CHARS:
        body = body[:MAX_BODY_CHARS] + "\n\n[...本文が長いため省略]"
    return body.strip()


def extract_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode(
                    part.get_content_charset() or "utf-8", errors="replace")
                break
    else:
        body = msg.get_payload(decode=True).decode(
            msg.get_content_charset() or "utf-8", errors="replace")
    return sanitize_body(body)


def extract_attachments(msg):
    """メールから添付ファイルを抽出してtmpに保存（サイズ・タイプ制限付き）"""
    files = []
    skipped = []
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    for part in msg.walk():
        filename = part.get_filename()
        if filename:
            decoded_fn = decode_header_value(filename)
            safe_name = re.sub(r'[^\w\.\-]', '_', decoded_fn)
            safe_name = os.path.basename(safe_name)
            if not safe_name:
                safe_name = f"attachment_{int(time.time())}"

            # 拡張子チェック
            ext = os.path.splitext(safe_name)[1].lower()
            if ext not in ALLOWED_ATTACHMENT_TYPES:
                skipped.append(f"{decoded_fn} (type={ext}: blocked)")
                audit_log("attachment_blocked", filename=decoded_fn,
                          ext=ext, reason="disallowed_type")
                continue

            # サイズチェック
            payload = part.get_payload(decode=True)
            if payload and len(payload) > MAX_ATTACHMENT_SIZE:
                skipped.append(f"{decoded_fn} (size={len(payload)//1024//1024}MB: too large)")
                audit_log("attachment_blocked", filename=decoded_fn,
                          size=len(payload), reason="too_large")
                continue

            filepath = TMP_DIR / safe_name
            with open(filepath, "wb") as f:
                f.write(payload)
            files.append(str(filepath))

    if skipped:
        print(f"  ⚠️ Skipped attachments: {skipped}")

    return files


# ─────────────────────────────────────────────
# メール認証検証（SPF/DKIM/DMARC）
# ─────────────────────────────────────────────
def _find_trusted_auth_header(all_auth):
    """信頼サーバーが付与した Authentication-Results ヘッダを探す

    RFC 8601 Section 5: MTA は自身が付与した Authentication-Results を
    ヘッダブロックの最上部に挿入する。複数MTAを経由する場合、
    最上位ヘッダが最終受信MTAのもの。

    ただし中間MTAが書き換える場合もあるため、TRUSTED_AUTH_SERVER に
    一致するヘッダを上から順に探し、最初に見つかったものを採用する。
    """
    if not TRUSTED_AUTH_SERVER:
        # 信頼サーバー未設定 → 最上位ヘッダをそのまま使用（非推奨）
        return all_auth[0] if all_auth else None

    for header in all_auth:
        # Authentication-Results の最初のトークンが authserv-id（サーバー名）
        # 例: "mx.hetemail.jp; dkim=pass; spf=pass; dmarc=pass"
        if TRUSTED_AUTH_SERVER in header:
            return header

    return None  # 信頼サーバーのヘッダが見つからない


def verify_email_auth(msg, sender_email):
    """Authentication-Results ヘッダでSPF/DKIM/DMARCを検証

    RFC 8601 準拠の信頼チェーン:
    1. msg.get_all() で全ヘッダ取得
    2. TRUSTED_AUTH_SERVER に一致するヘッダを上から探索
    3. 信頼サーバーのヘッダのみ使用（外部注入ヘッダを排除）

    Returns:
        (bool, str): (検証合格, 詳細メッセージ)
    """
    all_auth = msg.get_all("Authentication-Results") or []

    if not all_auth:
        return False, "Authentication-Results ヘッダなし（認証不可: ブロック）"

    # 信頼サーバーが付与したヘッダを探す
    auth_results = _find_trusted_auth_header(all_auth)

    if auth_results is None:
        return False, (
            f"信頼サーバー({TRUSTED_AUTH_SERVER})のAuth-Resultsが見つからない "
            f"(全{len(all_auth)}件のヘッダを検査済み)"
        )

    auth_lower = auth_results.lower()

    # DMARC fail — policy=reject/quarantine なら拒否
    if "dmarc=fail" in auth_lower:
        if "policy=reject" in auth_lower or "policy=quarantine" in auth_lower:
            return False, f"DMARC検証失敗(policy=reject/quarantine): {auth_results[:200]}"
        return True, f"DMARC fail but policy=none（警告）: {auth_results[:200]}"

    # SPF fail + DKIM fail なら拒否
    spf_fail = "spf=fail" in auth_lower or "spf=softfail" in auth_lower
    dkim_fail = "dkim=fail" in auth_lower or "dkim=none" in auth_lower

    if spf_fail and dkim_fail:
        return False, f"SPF+DKIM両方失敗: {auth_results[:200]}"

    if spf_fail:
        return True, f"SPF失敗（DKIM通過で許容）: {auth_results[:200]}"

    return True, "認証OK"


# ─────────────────────────────────────────────
# UIDVALIDITY管理
# ─────────────────────────────────────────────
def get_saved_uidvalidity():
    if UIDVALIDITY_FILE.exists():
        return UIDVALIDITY_FILE.read_text().strip()
    return None


def save_uidvalidity(val):
    UIDVALIDITY_FILE.parent.mkdir(parents=True, exist_ok=True)
    UIDVALIDITY_FILE.write_text(str(val))


def get_last_seen_uid():
    if STATE_FILE.exists():
        return STATE_FILE.read_text().strip()
    return "0"


def save_last_seen_uid(uid):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(str(uid))


# ─────────────────────────────────────────────
# メイン処理
# ─────────────────────────────────────────────
def check_mail():
    creds = json.load(open(MAIL_CONFIG))

    # IMAP接続（リトライ付き）
    m = None
    for attempt in range(3):
        try:
            m = imaplib.IMAP4_SSL(creds["imap_server"])
            m.login(creds["email"], creds["password"])
            break
        except Exception as e:
            if attempt == 2:
                error_msg = f"IMAP接続失敗（3回リトライ後）: {e}"
                print(error_msg)
                audit_log("imap_error", error=str(e))
                telegram_error(error_msg)
                return
            time.sleep(5)

    try:
        status, select_data = m.select("INBOX")
        if status != "OK":
            error_msg = f"INBOX選択失敗: {status}"
            print(error_msg)
            audit_log("imap_error", error=error_msg)
            telegram_error(error_msg)
            m.logout()
            return

        # UIDVALIDITY チェック
        uidvalidity = None
        try:
            status, uv_data = m.status("INBOX", "(UIDVALIDITY)")
            if status == "OK" and uv_data[0]:
                match = re.search(r'UIDVALIDITY\s+(\d+)', uv_data[0].decode())
                if match:
                    uidvalidity = match.group(1)
        except Exception:
            pass

        if uidvalidity:
            saved_uv = get_saved_uidvalidity()
            if saved_uv and saved_uv != uidvalidity:
                print(f"  ⚠️ UIDVALIDITY changed: {saved_uv} → {uidvalidity} — resetting last_seen_uid")
                save_last_seen_uid("0")
                audit_log("uidvalidity_reset", old=saved_uv, new=uidvalidity)
                telegram_notify(
                    "⚠️ <b>IMAP UIDVALIDITY変更検知</b>\n"
                    "UIDがリセットされました。last_seen_uidを0にリセットしました。"
                )
            save_uidvalidity(uidvalidity)

        last_uid = get_last_seen_uid()

        status, data = m.uid("search", None, f"UID {int(last_uid)+1}:*")
        if status != "OK" or not data[0]:
            m.logout()
            return

        uids = data[0].split()
        uids = [u for u in uids if int(u) > int(last_uid)]

        if not uids:
            m.logout()
            return

        now_jst = datetime.now(JST)
        print(f"[{now_jst.strftime('%Y-%m-%d %H:%M JST')}] {len(uids)} new mail(s)")

        max_uid = 0
        for uid in uids:
            try:
                status, msg_data = m.uid("fetch", uid, "(RFC822)")
                if status != "OK":
                    continue
                msg = email.message_from_bytes(msg_data[0][1])

                frm = decode_header_value(msg["From"])
                subj = decode_header_value(msg["Subject"])
                sender_email = extract_sender_email(frm)
                body = extract_body(msg)
                attachments = extract_attachments(msg)

                print(f"  UID {uid.decode()}: From={sender_email} Subject={subj} Attachments={len(attachments)}")

                if sender_email in AUTO_PROCESS_SENDERS:
                    # ── メール認証検証 ──
                    auth_ok, auth_detail = verify_email_auth(msg, sender_email)

                    audit_log("mail_received",
                              uid=uid.decode(), sender=sender_email, subject=subj,
                              auto_process=True, auth_ok=auth_ok, auth_detail=auth_detail[:200],
                              attachments=len(attachments))

                    if not auth_ok:
                        print(f"  ⚠️ 認証失敗 — スキップ: {auth_detail}")
                        audit_log("mail_blocked", uid=uid.decode(),
                                  sender=sender_email, reason=auth_detail[:200])
                        telegram_notify(
                            f"🚨 <b>メール認証失敗 — 自動処理をブロック</b>\n"
                            f"From: {sender_email}\nSubject: {subj}\n"
                            f"理由: {auth_detail[:200]}\n\n"
                            f"From詐称の可能性があります。手動で確認してください。"
                        )
                        if int(uid) > max_uid:
                            max_uid = int(uid)
                        continue

                    if auth_detail != "認証OK":
                        print(f"  ℹ️ 認証警告: {auth_detail}")

                    # ── 自律処理 ──
                    sender_name = "VIP送信者" if "kawashima" in sender_email else "オーナー"

                    att_info = ""
                    if attachments:
                        att_list = "\n".join([f"  - {f}" for f in attachments])
                        att_info = f"\n\n添付ファイル（~/workspace/assets/tmp/ に保存済み）:\n{att_list}"

                    task = f"""📧 {sender_name}からメールが届きました。内容を読んで自律的に対応してください。

From: {frm}
Subject: {subj}
Date: {msg['Date']}

【メール本文】
{body}
{att_info}

【対応ルール】
- VIP送信者からの投稿依頼 → イラスト生成・キャプション作成・確認メール送信・OK後に投稿
- オーナーからの指示 → 内容に応じて判断・実行
- 対応完了後、Telegramでオーナーに完了報告すること
- メール処理後はIMAPで該当メールを削除（Expunge）すること
- 簡潔なメッセージは短く返答してOK"""

                    success = wake_akiko(task)
                    audit_log("mail_processed", uid=uid.decode(),
                              sender=sender_email, action="system_event",
                              success=success)
                    if not success:
                        telegram_notify(
                            f"📧 <b>⚡ {sender_name}からメール（自動処理失敗）</b>\n"
                            f"Subject: {subj}\n\n{body[:300]}\n\n"
                            f"⚠️ 手動で対応してください。"
                        )
                else:
                    # その他 → Telegram通知のみ
                    audit_log("mail_received",
                              uid=uid.decode(), sender=sender_email, subject=subj,
                              auto_process=False)
                    preview = body[:200]
                    telegram_notify(
                        f"📧 <b>新着メール</b>\n"
                        f"From: {frm}\nSubject: {subj}\n\n{preview}"
                    )

            except Exception as e:
                print(f"  ⚠️ UID {uid.decode()} 処理エラー: {e}")
                audit_log("mail_error", uid=uid.decode(), error=str(e))
                telegram_error(f"UID {uid.decode()} 処理エラー: {e}")

            if int(uid) > max_uid:
                max_uid = int(uid)

        if max_uid > 0:
            save_last_seen_uid(max_uid)

    except Exception as e:
        error_msg = f"メールチェック中にエラー: {e}"
        print(error_msg)
        audit_log("check_mail_error", error=str(e))
        telegram_error(error_msg)
    finally:
        try:
            m.logout()
        except Exception:
            pass


if __name__ == "__main__":
    lock = FileLock(LOCK_FILE)
    if not lock.acquire():
        print("Another instance is running — skipping")
        sys.exit(0)
    try:
        check_mail()
    finally:
        lock.release()
