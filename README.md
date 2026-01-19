# Iris FastAPI + SQLite

Aplikasi FastAPI untuk prediksi Iris dengan UI sederhana dan penyimpanan data di SQLite.

## Fitur
- Login, registrasi user, dan manajemen akun (username/password).
- Prediksi Iris + riwayat prediksi per user.
- Admin otomatis dibuat saat startup.
- API JSON tetap tersedia di `/predict`.

## Requirements
- Python 3.10+

## Menjalankan (Makefile)
Build venv dan install dependency:

```bash
make build
```

Jalankan server:

```bash
make up
```

Agar menghentikan server, tekan `CTRL+C` di terminal yang menjalankan `make up`/`make run`.

Akses:
- UI: `http://127.0.0.1:8000/login`
- Swagger: `http://127.0.0.1:8000/docs`

## Akun Default
Admin otomatis dibuat saat startup:
- username: `admin`
- password: `admin`

User baru bisa dibuat dari tombol "Buat akun" di halaman login.

## Endpoint API
`POST /predict` (JSON):

```json
{
  "sepal_length": 5.1,
  "sepal_width": 3.5,
  "petal_length": 1.4,
  "petal_width": 0.2
}
```

Respons contoh:
```json
{"status":"success","prediction":0,"label":"Iris-setosa"}
```

## Database
- File SQLite otomatis dibuat di `app.db` (root project).
- Timestamp disimpan dalam WIB dengan format `DD-MM-YYYY HH:MM:SS WIB`.
- Hapus `app.db` jika ingin reset data.

## Konfigurasi
Set secret untuk session (disarankan):

```bash
SESSION_SECRET=your-secret-here make up
```

## Cara Kerja (ringkas)
1) Saat server start, tabel `users` dan `predictions` dibuat jika belum ada.
2) Admin default (`admin`/`admin`) disiapkan otomatis.
3) User login atau registrasi, lalu masuk ke halaman prediksi.
4) Prediksi disimpan ke SQLite dan muncul di riwayat user.
5) Halaman manajemen akun hanya untuk user yang sedang login.

Detail SQL (DDL/DML): lihat `sql-integration.md`.

## Model
Model ada di `model.pkl` (root). Untuk training ulang:

```bash
.venv/bin/python train_model.py
```

Data training: `source_code/Iris-Classification-WebApp/Iris.csv`.
