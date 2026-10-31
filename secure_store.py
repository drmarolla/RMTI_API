"""Per-practitioner encrypted workspace (SQLite + Fernet envelope encryption).

Design
- Passwords: scrypt (salted) -> verifier. Never stored in clear.
- Data: each user has a random data key (DEK). The DEK is stored wrapped by a key derived from the user's password
  (a separate scrypt salt). Records are encrypted with the DEK, label and payload together, so the database holds only
  ciphertext. Neither a stolen database file nor the server operator can read cases without the user's password.
  Consequence: a forgotten password means the data cannot be recovered. That is deliberate.
- Lockout after repeated failures; generic login errors; idle timeout is enforced by the UI layer.
- Audit log stores action names and timestamps only, never content.
- Data minimisation: labels and payloads are scanned for direct identifiers and refused.
This protects data in the application and at rest. It does NOT by itself make a deployment HIPAA/GDPR compliant:
that also needs compliant hosting, TLS, backups, access policies and institutional approval (see README).
"""
import base64, hashlib, hmac, json, os, re, secrets, sqlite3, time
from cryptography.fernet import Fernet, InvalidToken
from service import _ID_VALUES, _ID_COLS

DB_PATH = os.environ.get("RMTI_DB", os.path.join(os.path.dirname(__file__), "data", "rmti_secure.db"))
SCRYPT = dict(n=2 ** 15, r=8, p=1, maxmem=2 ** 26, dklen=32)
MAX_FAILS, LOCK_SECONDS, MIN_PW = 5, 15 * 60, 12
_USER = re.compile(r"^[a-z0-9._-]{3,40}$")


class AuthError(Exception): ...
class StoreError(Exception): ...


def _db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE, pw_salt BLOB, pw_hash BLOB,
        kek_salt BLOB, wrapped_dek BLOB, created REAL, failed INTEGER DEFAULT 0, locked_until REAL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS records(id INTEGER PRIMARY KEY, user_id INTEGER, kind TEXT, token BLOB, created REAL);
    CREATE TABLE IF NOT EXISTS audit(ts REAL, user_id INTEGER, action TEXT);""")
    try:
        os.chmod(DB_PATH, 0o600)
    except OSError:
        pass
    return c


def _kdf(password, salt):
    return hashlib.scrypt(password.encode(), salt=salt, **SCRYPT)


def _kek(password, salt):
    return base64.urlsafe_b64encode(_kdf(password, salt))


def _audit(c, uid, action):
    c.execute("INSERT INTO audit VALUES(?,?,?)", (time.time(), uid, action))


def vault_enabled():
    return os.environ.get("RMTI_ENABLE_VAULT") == "1"


def register(username, password, invite):
    required = os.environ.get("RMTI_INVITE_CODE", "")
    if not required:
        raise AuthError("Registration is closed: no invite code is configured on this server.")
    if not hmac.compare_digest(invite or "", required):
        raise AuthError("Invalid invite code.")
    username = (username or "").strip().lower()
    if not _USER.match(username):
        raise AuthError("Username: 3-40 characters from a-z, 0-9, dot, underscore, hyphen. Do not use a real name.")
    if len(password) < MIN_PW:
        raise AuthError(f"Password must be at least {MIN_PW} characters.")
    pw_salt, kek_salt = secrets.token_bytes(16), secrets.token_bytes(16)
    dek = Fernet.generate_key()
    wrapped = Fernet(_kek(password, kek_salt)).encrypt(dek)
    with _db() as c:
        try:
            cur = c.execute("INSERT INTO users(username,pw_salt,pw_hash,kek_salt,wrapped_dek,created) VALUES(?,?,?,?,?,?)",
                            (username, pw_salt, _kdf(password, pw_salt), kek_salt, wrapped, time.time()))
        except sqlite3.IntegrityError:
            raise AuthError("That username is taken.")
        _audit(c, cur.lastrowid, "register")


def login(username, password):
    username = (username or "").strip().lower()
    with _db() as c:
        u = c.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if u is None:
            _kdf(password or "x", b"0" * 16)                         # equalise timing, avoid user enumeration
            raise AuthError("Invalid username or password.")
        if u["locked_until"] > time.time():
            raise AuthError("Too many failed attempts. Try again later.")
        if not hmac.compare_digest(_kdf(password, u["pw_salt"]), u["pw_hash"]):
            fails = u["failed"] + 1
            c.execute("UPDATE users SET failed=?, locked_until=? WHERE id=?",
                      (0 if fails >= MAX_FAILS else fails, time.time() + LOCK_SECONDS if fails >= MAX_FAILS else 0, u["id"]))
            _audit(c, u["id"], "login_failed")
            c.commit()
            raise AuthError("Invalid username or password.")
        c.execute("UPDATE users SET failed=0, locked_until=0 WHERE id=?", (u["id"],))
        _audit(c, u["id"], "login")
        dek = Fernet(_kek(password, u["kek_salt"])).decrypt(u["wrapped_dek"])
    return {"user_id": u["id"], "username": username, "dek": dek}


def change_password(sess, old, new):
    if len(new) < MIN_PW:
        raise AuthError(f"Password must be at least {MIN_PW} characters.")
    with _db() as c:
        u = c.execute("SELECT * FROM users WHERE id=?", (sess["user_id"],)).fetchone()
        if not hmac.compare_digest(_kdf(old, u["pw_salt"]), u["pw_hash"]):
            raise AuthError("Current password is incorrect.")
        ps, ks = secrets.token_bytes(16), secrets.token_bytes(16)
        c.execute("UPDATE users SET pw_salt=?, pw_hash=?, kek_salt=?, wrapped_dek=? WHERE id=?",
                  (ps, _kdf(new, ps), ks, Fernet(_kek(new, ks)).encrypt(sess["dek"]), u["id"]))
        _audit(c, u["id"], "password_changed")


def _scan(obj, path="payload"):
    """Refuse anything that looks like a direct identifier (keys or string values)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if _ID_COLS.search(str(k)):
                raise StoreError(f"Refused: field '{k}' looks like a direct identifier.")
            _scan(v, f"{path}.{k}")
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _scan(v, path)
    elif isinstance(obj, str):
        if any(p.search(obj) for p in _ID_VALUES):
            raise StoreError("Refused: text looks like an email, phone or ID number.")


def save_record(sess, kind, label, payload):
    label = (label or "").strip()
    if not label:
        raise StoreError("Give the case a pseudonymous label (e.g. a study code), not a name.")
    _scan({"label": label}); _scan(payload)
    blob = Fernet(sess["dek"]).encrypt(json.dumps({"label": label, "payload": payload}, default=str).encode())
    with _db() as c:
        cur = c.execute("INSERT INTO records(user_id,kind,token,created) VALUES(?,?,?,?)",
                        (sess["user_id"], kind, blob, time.time()))
        _audit(c, sess["user_id"], f"save_{kind}")
    return cur.lastrowid


def list_records(sess):
    out = []
    with _db() as c:
        for r in c.execute("SELECT * FROM records WHERE user_id=? ORDER BY created DESC", (sess["user_id"],)):
            try:
                d = json.loads(Fernet(sess["dek"]).decrypt(r["token"]))
            except InvalidToken:
                continue
            out.append({"id": r["id"], "kind": r["kind"], "created": r["created"], **d})
    return out


def delete_record(sess, rid):
    with _db() as c:
        c.execute("DELETE FROM records WHERE id=? AND user_id=?", (rid, sess["user_id"]))
        _audit(c, sess["user_id"], "delete_record")


def export_all(sess):
    with _db() as c:
        _audit(c, sess["user_id"], "export")
    return json.dumps(list_records(sess), indent=2, default=str)


def audit_log(sess, limit=50):
    with _db() as c:
        return [dict(r) for r in c.execute("SELECT ts, action FROM audit WHERE user_id=? ORDER BY ts DESC LIMIT ?",
                                           (sess["user_id"], limit))]


def delete_account(sess, password):
    with _db() as c:
        u = c.execute("SELECT * FROM users WHERE id=?", (sess["user_id"],)).fetchone()
        if not hmac.compare_digest(_kdf(password, u["pw_salt"]), u["pw_hash"]):
            raise AuthError("Password is incorrect.")
        c.execute("DELETE FROM records WHERE user_id=?", (u["id"],))
        c.execute("DELETE FROM users WHERE id=?", (u["id"],))
        c.execute("DELETE FROM audit WHERE user_id=?", (u["id"],))
