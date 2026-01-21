# Iris FastAPI + SQLite

Aplikasi FastAPI untuk prediksi Iris dengan UI sederhana dan penyimpanan data di SQLite.

## Sumber dan dokumentasi tambahan
- SQL (DDL/DML): [sql-integration.md](sql-integration.md)
- Panduan Makefile untuk pemula: [readme_makefile.md](readme_makefile.md)
- Rangkuman API dan contoh: [api.md](api.md)

## Fitur
- Login, registrasi user, dan manajemen akun (username/password).
- Prediksi Iris + riwayat prediksi per user.
- Admin otomatis dibuat saat startup.
- API JSON tetap tersedia di `/predict`.

## Requirements
- Python 3.10+
- `make` (opsional, hanya untuk perintah Makefile; lihat bagian Install make di bawah).

## Install make (Windows/macOS/Linux)
Jika perintah `make` belum ada, instal sesuai OS. Setelah install, cek: `make --version`.

macOS:
```bash
xcode-select --install
```
Atau (Homebrew):
```bash
brew install make
```

Linux:
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install -y make
```
Alternatif:
```bash
# Fedora
sudo dnf install -y make
# Arch
sudo pacman -S make
```

Windows:
- Disarankan (WSL): jalankan `wsl --install -d Ubuntu`, lalu di WSL: `sudo apt update && sudo apt install -y make`.
- Native (tanpa WSL): install lewat `winget install GnuWin32.Make` atau `choco install make`, lalu buka terminal baru.

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

Mapping nilai `prediction`:
- `0` = Iris-setosa
- `1` = Iris-versicolor
- `2` = Iris-virginica

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
