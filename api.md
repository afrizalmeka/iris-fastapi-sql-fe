# API Guide

Dokumen ini menjelaskan arah (flow) dan detail setiap API/route yang tersedia.

## Ringkasan Route
UI:
- `GET /` -> redirect ke `/prediksi` jika sudah login, kalau belum ke `/login`.
- `GET /login` -> halaman login.
- `POST /login` -> proses login.
- `GET /register` -> halaman registrasi user.
- `POST /register` -> proses registrasi user.
- `GET /logout` -> logout (hapus session).
- `GET /prediksi` -> halaman input prediksi + riwayat user.
- `POST /prediksi` -> proses prediksi + simpan riwayat.
- `GET /users` -> halaman manajemen akun (untuk user login).
- `POST /users/update-username` -> ubah username user login.
- `POST /users/update-password` -> ubah password user login.

API JSON:
- `POST /predict` -> API prediksi berbasis JSON (untuk integrasi eksternal).

## Detail Route UI

### 1) `GET /`
Arah:
- Jika session login ada, redirect ke `/prediksi`.
- Jika belum login, redirect ke `/login`.

### 2) `GET /login`
- Menampilkan form login.
- Jika sudah login, redirect ke `/prediksi`.

### 3) `POST /login`
Tujuan: autentikasi user.

Form Data:
- `username`
- `password`

Flow:
- Cek user berdasarkan username.
- Verifikasi password (hash).
- Jika valid -> simpan `user_id` dan `username` ke session, redirect ke `/prediksi`.
- Jika gagal -> flash error, kembali ke `/login`.

### 4) `GET /register`
- Menampilkan form registrasi akun user.
- Jika sudah login, redirect ke `/prediksi`.

### 5) `POST /register`
Tujuan: membuat akun user baru (role = user).

Form Data:
- `username`
- `password`
- `password_confirm`

Flow:
- Validasi input wajib.
- Pastikan password = password_confirm.
- Larang username `admin` untuk user biasa.
- Jika username belum dipakai -> simpan user, login otomatis, redirect ke `/prediksi`.
- Jika gagal -> flash error, kembali ke `/register`.

### 6) `GET /logout`
- Menghapus session.
- Redirect ke `/login`.

### 7) `GET /prediksi`
- Menampilkan form prediksi + riwayat prediksi user login.
- Jika belum login -> redirect ke `/login`.

### 8) `POST /prediksi`
Tujuan: menjalankan prediksi model dan simpan riwayat.

Form Data:
- `sepal_length`
- `sepal_width`
- `petal_length`
- `petal_width`

Flow:
- Validasi input harus angka.
- Jalankan model prediksi.
- Simpan hasil ke SQLite.
- Tampilkan hasil + riwayat.

### 9) `GET /users`
Tujuan: manajemen akun pribadi.

Flow:
- Hanya user login.
- Tampilkan data akun (username/role/timestamp) dan riwayat prediksi milik user tersebut.

### 10) `POST /users/update-username`
Tujuan: ganti username user login.

Form Data:
- `username`

Flow:
- Validasi input tidak kosong.
- Admin tidak boleh ganti username.
- Cek username baru belum dipakai.
- Update username + timestamp.

### 11) `POST /users/update-password`
Tujuan: ganti password user login.

Form Data:
- `password`

Flow:
- Validasi input tidak kosong.
- Update password hash + timestamp.

## Detail Route API JSON

### `POST /predict`
Tujuan: endpoint prediksi JSON (bisa dipakai integrasi di luar UI).

Request JSON:
```json
{
  "sepal_length": 5.1,
  "sepal_width": 3.5,
  "petal_length": 1.4,
  "petal_width": 0.2
}
```

Response JSON:
```json
{
  "status": "success",
  "prediction": 0,
  "label": "Iris-setosa"
}
```

Catatan:
- Endpoint ini tidak menyimpan riwayat ke SQLite (hanya untuk UI form `/prediksi`).
- Jika ingin simpan riwayat via API JSON, perlu endpoint baru.

## Session & Arah Akses
- Session disimpan via `SessionMiddleware`.
- Semua halaman selain `/login` dan `/register` membutuhkan session login.
- Admin default otomatis dibuat saat startup: `admin / admin`.
