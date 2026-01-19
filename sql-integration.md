# SQL Integration (SQLite)

Dokumen ini menjelaskan integrasi SQLite pada aplikasi Iris FastAPI secara lebih detail: koneksi, DDL, DML, dan alur data.

## Ringkas Konsep
- DDL (Data Definition Language): perintah SQL untuk membuat atau mengubah struktur tabel.
- DML (Data Manipulation Language): perintah SQL untuk mengisi, membaca, dan mengubah data di tabel.

## Koneksi dan Konfigurasi
- Database lokal disimpan sebagai file `app.db` (di root project).
- Koneksi dibuat di fungsi `get_db()`:
  - `sqlite3.connect(DB_PATH)` membuka koneksi ke file DB.
  - `row_factory = sqlite3.Row` agar hasil query bisa diakses seperti dict (contoh: `row["username"]`).
  - `PRAGMA foreign_keys = ON` mengaktifkan foreign key agar relasi antar tabel konsisten.

## DDL: Struktur Tabel dan Migrasi Ringan
Semua DDL dijalankan di `init_db()` saat server start.

### 1) CREATE TABLE users
Tujuan: menyimpan akun (admin/user), hash password, serta timestamp audit.

SQL:
```
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
```
Penjelasan:
- `id` auto-increment agar setiap user punya identitas unik.
- `username` dibuat `UNIQUE` untuk mencegah duplikasi.
- `password_hash` menyimpan hash, bukan password asli.
- `role` dipakai untuk membedakan admin vs user.
- `created_at` dan `updated_at` menyimpan waktu audit (WIB).

### 2) CREATE TABLE predictions
Tujuan: menyimpan riwayat prediksi milik setiap user.

SQL:
```
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
```
Penjelasan:
- `user_id` menghubungkan prediksi dengan tabel users.
- `FOREIGN KEY ... ON DELETE CASCADE` artinya jika user dihapus, riwayat prediksi ikut terhapus.
- Kolom `sepal_*` dan `petal_*` menyimpan input model.
- `prediction_id` dan `label` menyimpan hasil prediksi.
- `created_at` menyimpan waktu prediksi (WIB).

### 3) ALTER TABLE untuk migrasi ringan
Tujuan: menambah kolom baru untuk DB yang sudah ada, tanpa tools migrasi.

SQL:
```
ALTER TABLE users ADD COLUMN updated_at TEXT
ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'
```
Penjelasan:
- `updated_at` ditambahkan agar perubahan akun bisa dicatat.
- `role` ditambahkan dengan default `user` agar semua data lama tetap valid.

### 4) UPDATE normalisasi data lama
Tujuan: menyiapkan nilai default untuk data lama.

SQL:
```
UPDATE users SET updated_at = created_at WHERE updated_at IS NULL
UPDATE users SET role = 'user' WHERE role IS NULL OR role = ''
```
Penjelasan:
- Jika DB dibuat sebelum kolom ditambahkan, nilai bisa kosong. Query ini mengisi nilai yang belum ada.

## DML: Operasi Data (INSERT, SELECT, UPDATE)
DML tersebar di beberapa fungsi di `main.py`.

### A) INSERT (menambah data)
1) Insert user baru (register)
- Fungsi: `create_user()`
- SQL:
```
INSERT INTO users (username, password_hash, role, created_at, updated_at)
VALUES (?, ?, ?, ?, ?)
```
Penjelasan:
- Placeholder `?` mencegah SQL injection.
- `password_hash` disimpan, bukan password asli.
- `created_at` dan `updated_at` diisi dengan timestamp WIB.

2) Insert prediksi
- Fungsi: `save_prediction()`
- SQL:
```
INSERT INTO predictions (
    user_id, sepal_length, sepal_width, petal_length, petal_width,
    prediction_id, label, created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
```
Penjelasan:
- Data input + hasil prediksi disimpan untuk riwayat.

### B) SELECT (membaca data)
1) Ambil user berdasarkan username (login/validasi)
- Fungsi: `get_user_by_username()`
- SQL:
```
SELECT id, username, password_hash, role, created_at, updated_at
FROM users
WHERE username = ?
```
Penjelasan:
- Dipakai untuk login dan cek duplikasi saat registrasi.

2) Ambil user berdasarkan id (session)
- Fungsi: `get_user_by_id()`
- SQL:
```
SELECT id, username, role, created_at, updated_at
FROM users
WHERE id = ?
```
Penjelasan:
- Dipakai untuk mengambil data user yang sedang login.

3) Ambil riwayat prediksi user
- Fungsi: `load_history()`
- SQL:
```
SELECT sepal_length, sepal_width, petal_length, petal_width,
       prediction_id, label, created_at
FROM predictions
WHERE user_id = ?
ORDER BY id DESC
LIMIT ?
```
Penjelasan:
- `ORDER BY id DESC` menampilkan data terbaru dulu.
- `LIMIT` membatasi jumlah data untuk UI.

### C) UPDATE (mengubah data)
1) Pastikan admin punya role admin
- Fungsi: `ensure_admin_user()`
- SQL:
```
UPDATE users SET role = ?, updated_at = ? WHERE id = ?
```
Penjelasan:
- Jika user admin sudah ada tapi role belum admin, diperbaiki otomatis.

2) Update password user
- Fungsi: `users_update_password()`
- SQL:
```
UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?
```
Penjelasan:
- Password disimpan dalam bentuk hash baru.

3) Update username user
- Fungsi: `users_update_username()`
- SQL:
```
UPDATE users SET username = ?, updated_at = ? WHERE id = ?
```
Penjelasan:
- Digunakan saat user mengganti username sendiri.

## Alur Data (Step-by-step)
1) Startup aplikasi -> `init_db()` membuat tabel dan migrasi ringan (DDL).
2) `ensure_admin_user()` membuat admin default jika belum ada (DML INSERT/UPDATE).
3) User registrasi -> data masuk ke `users` (DML INSERT).
4) User login -> data user dibaca untuk validasi (DML SELECT).
5) User melakukan prediksi -> hasil disimpan ke `predictions` (DML INSERT).
6) Halaman riwayat/manajemen -> data hanya untuk user login (DML SELECT).
7) User update username/password -> tabel `users` diperbarui (DML UPDATE).

## Catatan Tambahan
- Semua query menggunakan parameter binding (`?`) untuk keamanan.
- Timestamp disimpan dalam WIB dengan format `DD-MM-YYYY HH:MM:SS WIB`.
- Karena menggunakan SQLite file lokal, deploy multi-user skala besar sebaiknya mempertimbangkan DB server terpisah.
