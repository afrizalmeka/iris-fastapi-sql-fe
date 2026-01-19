from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
import pickle
import secrets
import sqlite3

from fastapi import Body, FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")
SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-secret-change-me")
WIB = timezone(timedelta(hours=7))
TIME_FORMAT = "%d-%m-%Y %H:%M:%S"
LEGACY_FORMATS = ("%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S")
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET, same_site="lax")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

model = pickle.load(open(os.path.join(BASE_DIR, "model.pkl"), "rb"))


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Aktifkan foreign key agar relasi antar tabel tetap konsisten.
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    with get_db() as conn:
        # Buat tabel users untuk menyimpan kredensial, role, dan timestamp audit.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        # Buat tabel predictions untuk menyimpan riwayat prediksi per user.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                sepal_length REAL NOT NULL,
                sepal_width REAL NOT NULL,
                petal_length REAL NOT NULL,
                petal_width REAL NOT NULL,
                prediction_id INTEGER NOT NULL,
                label TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        # Cek kolom tabel users untuk migrasi ringan.
        columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()
        }
        if "updated_at" not in columns:
            # Tambah kolom updated_at untuk data audit.
            conn.execute("ALTER TABLE users ADD COLUMN updated_at TEXT")
            # Isi updated_at dari created_at untuk data lama.
            conn.execute(
                "UPDATE users SET updated_at = created_at WHERE updated_at IS NULL"
            )
        if "role" not in columns:
            # Tambah kolom role agar bisa membedakan admin vs user.
            conn.execute(
                "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'"
            )
        # Normalisasi role yang kosong/null pada data lama.
        conn.execute("UPDATE users SET role = 'user' WHERE role IS NULL OR role = ''")
        conn.commit()


def now_wib():
    return datetime.now(WIB).strftime(f"{TIME_FORMAT} WIB")


def format_wib(value):
    if not value:
        return ""
    value = value.strip()
    if value.endswith("WIB"):
        return value
    raw = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        parsed = None
        for fmt in LEGACY_FORMATS:
            try:
                parsed = datetime.strptime(value, fmt)
                break
            except ValueError:
                continue
        if parsed is None:
            return value
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(WIB).strftime(f"{TIME_FORMAT} WIB")


def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    ).hex()
    return f"{salt}${digest}"


def verify_password(password, stored):
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    check = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    ).hex()
    return hmac.compare_digest(check, digest)


def create_user(username, password, role="user"):
    timestamp = now_wib()
    with get_db() as conn:
        # Simpan user baru dengan password hash dan timestamp.
        conn.execute(
            """
            INSERT INTO users (username, password_hash, role, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (username, hash_password(password), role, timestamp, timestamp),
        )
        conn.commit()


def get_user_by_username(username):
    with get_db() as conn:
        # Ambil user berdasarkan username untuk login/validasi.
        return conn.execute(
            """
            SELECT id, username, password_hash, role, created_at, updated_at
            FROM users
            WHERE username = ?
            """,
            (username,),
        ).fetchone()


def get_user_by_id(user_id):
    with get_db() as conn:
        # Ambil user login berdasarkan id untuk kebutuhan session.
        return conn.execute(
            """
            SELECT id, username, role, created_at, updated_at
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()


def ensure_admin_user():
    admin = get_user_by_username(ADMIN_USERNAME)
    if admin is None:
        create_user(ADMIN_USERNAME, ADMIN_PASSWORD, role="admin")
        return
    if admin["role"] != "admin":
        with get_db() as conn:
            # Naikkan role jadi admin bila perlu.
            conn.execute(
                "UPDATE users SET role = ?, updated_at = ? WHERE id = ?",
                ("admin", now_wib(), admin["id"]),
            )
            conn.commit()


def set_flash(request, message, category="info"):
    request.session["flash"] = {"message": message, "category": category}


def pop_flash(request):
    return request.session.pop("flash", None)


def get_current_user(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return get_user_by_id(user_id)


def redirect_to(path):
    return RedirectResponse(url=path, status_code=status.HTTP_303_SEE_OTHER)


def run_prediction(sepal_length, sepal_width, petal_length, petal_width):
    features = [sepal_length, sepal_width, petal_length, petal_width]
    prediction = model.predict([features])
    pred_id = int(prediction[0])
    label_map = {
        0: "Iris-setosa",
        1: "Iris-versicolor",
        2: "Iris-virginica",
    }
    return pred_id, label_map.get(pred_id, "unknown")


def load_history(user_id, limit=10):
    with get_db() as conn:
        # Ambil riwayat prediksi terbaru untuk user saat ini.
        rows = conn.execute(
            """
            SELECT sepal_length, sepal_width, petal_length, petal_width,
                   prediction_id, label, created_at
            FROM predictions
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    history = []
    for row in rows:
        data = dict(row)
        data["created_at"] = format_wib(data.get("created_at"))
        history.append(data)
    return history


def save_prediction(user_id, sepal_length, sepal_width, petal_length, petal_width, pred_id, label):
    with get_db() as conn:
        # Simpan catatan prediksi untuk user saat ini.
        conn.execute(
            """
            INSERT INTO predictions (
                user_id, sepal_length, sepal_width, petal_length, petal_width,
                prediction_id, label, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                sepal_length,
                sepal_width,
                petal_length,
                petal_width,
                pred_id,
                label,
                now_wib(),
            ),
        )
        conn.commit()


@app.on_event("startup")
def on_startup():
    init_db()
    ensure_admin_user()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    if get_current_user(request):
        return redirect_to("/prediksi")
    return redirect_to("/login")


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if get_current_user(request):
        return redirect_to("/prediksi")
    flash = pop_flash(request)
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "title": "Login",
            "user": None,
            "flash": flash,
        },
    )


@app.post("/login")
def login_action(request: Request, username: str = Form(...), password: str = Form(...)):
    user = get_user_by_username(username.strip())
    if not user or not verify_password(password, user["password_hash"]):
        set_flash(request, "Username atau password salah.", "error")
        return redirect_to("/login")
    request.session["user_id"] = user["id"]
    request.session["username"] = user["username"]
    return redirect_to("/prediksi")


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    if get_current_user(request):
        return redirect_to("/prediksi")
    flash = pop_flash(request)
    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "title": "Buat Akun",
            "user": None,
            "flash": flash,
        },
    )


@app.post("/register")
def register_action(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
):
    if get_current_user(request):
        return redirect_to("/prediksi")
    username = username.strip()
    if not username or not password.strip() or not password_confirm.strip():
        set_flash(request, "Username dan password wajib diisi.", "error")
        return redirect_to("/register")
    if password != password_confirm:
        set_flash(request, "Password tidak cocok. Silakan ulangi.", "error")
        return redirect_to("/register")
    if username.lower() == ADMIN_USERNAME:
        set_flash(request, "Username tersebut tidak bisa digunakan.", "error")
        return redirect_to("/register")
    if get_user_by_username(username):
        set_flash(request, "Username sudah dipakai.", "error")
        return redirect_to("/register")
    create_user(username, password, role="user")
    user = get_user_by_username(username)
    request.session["user_id"] = user["id"]
    request.session["username"] = user["username"]
    return redirect_to("/prediksi")


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return redirect_to("/login")


@app.get("/prediksi", response_class=HTMLResponse)
def predict_page(request: Request):
    user = get_current_user(request)
    if not user:
        return redirect_to("/login")
    flash = pop_flash(request)
    history = load_history(user["id"])
    return templates.TemplateResponse(
        "predict.html",
        {
            "request": request,
            "title": "Prediksi",
            "user": user,
            "flash": flash,
            "history": history,
            "result": None,
            "values": {},
        },
    )


@app.post("/prediksi", response_class=HTMLResponse)
def predict_action(
    request: Request,
    sepal_length: str = Form(...),
    sepal_width: str = Form(...),
    petal_length: str = Form(...),
    petal_width: str = Form(...),
):
    user = get_current_user(request)
    if not user:
        return redirect_to("/login")
    error = None
    values = {
        "sepal_length": sepal_length,
        "sepal_width": sepal_width,
        "petal_length": petal_length,
        "petal_width": petal_width,
    }
    try:
        features = [float(sepal_length), float(sepal_width), float(petal_length), float(petal_width)]
    except ValueError:
        error = "Semua input harus berupa angka."
        result = None
    else:
        pred_id, label = run_prediction(*features)
        save_prediction(user["id"], features[0], features[1], features[2], features[3], pred_id, label)
        result = {"prediction_id": pred_id, "label": label}
    history = load_history(user["id"])
    return templates.TemplateResponse(
        "predict.html",
        {
            "request": request,
            "title": "Prediksi",
            "user": user,
            "flash": {"message": error, "category": "error"} if error else None,
            "history": history,
            "result": result,
            "values": values,
        },
    )


@app.get("/users", response_class=HTMLResponse)
def users_page(request: Request):
    user = get_current_user(request)
    if not user:
        return redirect_to("/login")
    flash = pop_flash(request)
    user_view = dict(user)
    user_view["created_at"] = format_wib(user_view.get("created_at"))
    user_view["updated_at"] = format_wib(user_view.get("updated_at"))
    history = load_history(user["id"])
    return templates.TemplateResponse(
        "users.html",
        {
            "request": request,
            "title": "Manajemen User",
            "user": user_view,
            "flash": flash,
            "history": history,
        },
    )


@app.post("/users/update-password")
def users_update_password(request: Request, password: str = Form(...)):
    current = get_current_user(request)
    if not current:
        return redirect_to("/login")
    if not password.strip():
        set_flash(request, "Password baru wajib diisi.", "error")
        return redirect_to("/users")
    with get_db() as conn:
        # Update password user saat ini dan timestamp perubahan.
        conn.execute(
            "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
            (hash_password(password), now_wib(), current["id"]),
        )
        conn.commit()
    set_flash(request, "Password berhasil diubah.", "success")
    return redirect_to("/users")


@app.post("/users/update-username")
def users_update_username(request: Request, username: str = Form(...)):
    current = get_current_user(request)
    if not current:
        return redirect_to("/login")
    username = username.strip()
    if not username:
        set_flash(request, "Username baru wajib diisi.", "error")
        return redirect_to("/users")
    if current["role"] == "admin" and username != current["username"]:
        set_flash(request, "Username admin tidak bisa diubah.", "error")
        return redirect_to("/users")
    if username.lower() == ADMIN_USERNAME and current["role"] != "admin":
        set_flash(request, "Username tersebut tidak bisa digunakan.", "error")
        return redirect_to("/users")
    existing = get_user_by_username(username)
    if existing and existing["id"] != current["id"]:
        set_flash(request, "Username sudah dipakai.", "error")
        return redirect_to("/users")
    with get_db() as conn:
        # Update username user saat ini dan timestamp perubahan.
        conn.execute(
            "UPDATE users SET username = ?, updated_at = ? WHERE id = ?",
            (username, now_wib(), current["id"]),
        )
        conn.commit()
    request.session["username"] = username
    set_flash(request, "Username berhasil diubah.", "success")
    return redirect_to("/users")


@app.post("/predict")
def predict_data(
    sepal_length: float = Body(..., description="Sepal length (cm)", example=5.1),
    sepal_width: float = Body(..., description="Sepal width (cm)", example=3.5),
    petal_length: float = Body(..., description="Petal length (cm)", example=1.4),
    petal_width: float = Body(..., description="Petal width (cm)", example=0.2),
):
    pred_id, label = run_prediction(sepal_length, sepal_width, petal_length, petal_width)
    return {
        "status": "success",
        "prediction": pred_id,
        "label": label,
    }
