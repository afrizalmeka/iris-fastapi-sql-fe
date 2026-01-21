# Panduan Makefile untuk Proyek Ini (Pemula)

Dokumen ini menjelaskan cara menjalankan proyek dengan dan tanpa Makefile. Semua perintah diambil dari isi `Makefile` yang ada di root project ini.

## 0) Instalasi make (Windows/macOS/Linux)

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
- Native (tanpa WSL): install lewat `winget install GnuWin32.Make` atau `choco install make`/MSYS2, lalu buka terminal baru.

Kalau tidak ingin install `make`, ikuti langkah manual di bagian 2 (Tanpa Makefile).

## 1) Konsep singkat: apa itu Makefile dan manfaatnya

Makefile adalah file yang berisi kumpulan perintah terstruktur (disebut "target") agar langkah-langkah yang berulang bisa dijalankan dengan cepat dan konsisten.
Manfaatnya:
- Mengurangi salah ketik perintah.
- Menyatukan alur build dan run supaya mudah diikuti.
- Memastikan setiap orang memakai perintah yang sama.

## 2) Tanpa Makefile (manual)

Bagian ini meniru isi Makefile, tetapi dijalankan manual satu per satu.

### Langkah 1 - Buat virtual environment (venv)

Tujuan: menyiapkan lingkungan Python terpisah untuk dependency proyek.

Perintah macOS/Linux:
```bash
python3 -m venv --clear .venv
```

Perintah Windows (PowerShell):
```powershell
python -m venv --clear .venv
```

Catatan:
- `--clear` akan menghapus isi venv lama jika sudah ada.

### Langkah 2 - Aktivasi venv (opsional)

Tujuan: memudahkan pemanggilan `python` dan `pip` tanpa menulis path lengkap.

Catatan penting:
- Makefile tidak memakai aktivasi. Ia menjalankan perintah langsung dari path venv.
- Karena perintah aktivasi tidak ada di Makefile, bagian ini hanya sebagai konsep dan tidak mencantumkan perintah.

### Langkah 3 - Install dependency

Tujuan: memasang semua paket dari `requirements.txt`.

Perintah macOS/Linux:
```bash
.venv/bin/python -m pip install -r requirements.txt
```

Perintah Windows (PowerShell):
```powershell
.venv/Scripts/python -m pip install -r requirements.txt
```

### Langkah 4 - Jalankan server

Tujuan: menyalakan aplikasi FastAPI dengan auto-reload untuk pengembangan.

Perintah macOS/Linux:
```bash
.venv/bin/uvicorn main:app --reload
```

Perintah Windows (PowerShell):
```powershell
.venv/Scripts/uvicorn main:app --reload
```

Catatan:
- `--reload` membuat server restart otomatis saat ada perubahan file.

## 3) Dengan Makefile

### Prasyarat
- Python (lihat versi minimal di `README.md`).
- `make` sudah tersedia di terminal Anda.

### Isi Makefile (ringkas)

```makefile
VENV_DIR ?= .venv

ifeq ($(OS),Windows_NT)
PYTHON ?= python
VENV_BIN := $(VENV_DIR)/Scripts
else
PYTHON ?= python3
VENV_BIN := $(VENV_DIR)/bin
endif

VENV_PY := $(VENV_BIN)/python

.PHONY: build run up

build:
	$(PYTHON) -m venv --clear $(VENV_DIR)
	$(VENV_PY) -m pip install -r requirements.txt

run: up

up:
	$(VENV_BIN)/uvicorn main:app --reload
```

### Penjelasan bagian-bagian Makefile

- `OS`: variabel bawaan Make yang bernilai `Windows_NT` di Windows. Dipakai untuk memilih path yang sesuai.
- `VENV_DIR`: lokasi venv. Default-nya `.venv`.
- `ACTIVATE`: tidak ada di Makefile ini. Aktivasi venv tidak dipakai karena perintah langsung memanggil `$(VENV_BIN)` atau `$(VENV_PY)`.
- `.PHONY`: menandai `build`, `run`, dan `up` sebagai target "virtual" agar selalu dijalankan meski ada file bernama sama.

### Detail tiap target

#### `make build`

Perintah yang dijalankan:
- `python3 -m venv --clear .venv` (macOS/Linux) atau `python -m venv --clear .venv` (Windows)
- `.venv/bin/python -m pip install -r requirements.txt` atau `.venv/Scripts/python -m pip install -r requirements.txt`

Alasan/tujuan:
- Membuat venv baru (atau membersihkan venv lama).
- Memasang dependency yang dibutuhkan aplikasi.

Catatan penting:
- `--clear` akan menghapus isi venv lama, jadi paket akan diinstal ulang.

#### `make run`

Perintah yang dijalankan:
- Tidak ada perintah langsung. Target ini hanya memanggil `make up`.

Alasan/tujuan:
- Memberi alias yang mudah diingat untuk menjalankan server.

Catatan penting:
- Pastikan `make build` sudah dijalankan sebelumnya.

#### `make up`

Perintah yang dijalankan:
- `.venv/bin/uvicorn main:app --reload` atau `.venv/Scripts/uvicorn main:app --reload`

Alasan/tujuan:
- Menyalakan server FastAPI.

Catatan penting:
- `--reload` memudahkan pengembangan karena server akan restart saat file berubah.

## 4) Alur yang disarankan untuk pemula

Pakai Makefile:
1. `make build`
2. `make up`

Tanpa Makefile:
1. Buat venv.
2. Install dependency.
3. Jalankan server.

## 5) Cara menghentikan server

Tekan `CTRL+C` di terminal yang sedang menjalankan server.

## 6) (Opsional) Troubleshooting umum

- `python` atau `python3` tidak ditemukan: pastikan Python terpasang dan ada di PATH.
- `make` tidak dikenali: pastikan Anda menjalankan perintah di terminal yang memiliki `make`.
- `uvicorn` tidak ditemukan: pastikan langkah install dependency sudah sukses.
