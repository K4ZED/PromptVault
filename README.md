# PromptVault

PromptVault adalah web app Flask untuk AI Marketing Specialist yang perlu menyimpan prompt, membuat prompt lokal dari template, memberi rating hasil, dan melacak produksi konten marketing/affiliate.

## Fitur MVP

- Auth register, login, logout dengan Flask-Login.
- Password hashing dengan Werkzeug.
- Dashboard ringkasan prompt dan content task.
- CRUD Prompt Library dengan search, filter, rating, catatan, dan tombol copy.
- Prompt Generator berbasis template lokal tanpa API AI eksternal.
- CRUD Content Tasks harian dengan status produksi, relasi opsional ke prompt, dan reset otomatis setiap hari.
- PostgreSQL via Neon menggunakan SQLAlchemy.
- Siap deploy ke Vercel.

## Tech Stack

- Python Flask
- PostgreSQL Neon
- SQLAlchemy
- Flask-Login
- Werkzeug
- Jinja2
- HTML, CSS custom, JavaScript vanilla

## Setup Lokal

1. Buat virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependency.

```bash
pip install -r requirements.txt
```

3. Buat file `.env` dari contoh.

```bash
cp .env.example .env
```

4. Isi `DATABASE_URL` dan `SECRET_KEY` di `.env`.
   Gunakan `AUTO_CREATE_TABLES=true` untuk setup awal. Setelah tabel sudah ada di production, kamu bisa set `AUTO_CREATE_TABLES=false`.
   `RESET_CONTENT_TASKS_DAILY=true` membuat content task otomatis reset setiap hari berdasarkan `APP_TIMEZONE`.

## Setup Neon PostgreSQL

1. Buat project baru di Neon.
2. Salin connection string PostgreSQL.
3. Pastikan memakai parameter SSL seperti `?sslmode=require`.
4. Tempel connection string ke `DATABASE_URL`.

Jika connection string dari Neon diawali `postgres://`, aplikasi otomatis mengubahnya menjadi `postgresql://` agar kompatibel dengan SQLAlchemy.

## Menjalankan Project

```bash
flask --app app run --debug
```

Buka `http://127.0.0.1:5000`.

## Deploy ke Vercel

1. Push project ke Git repository.
2. Import repository di Vercel.
3. Tambahkan environment variables:
   - `DATABASE_URL`
   - `SECRET_KEY`
   - `AUTO_CREATE_TABLES`
   - `RESET_CONTENT_TASKS_DAILY`
   - `APP_TIMEZONE`
4. Deploy. Konfigurasi `vercel.json` sudah mengarahkan request ke `app.py`.

## Struktur Folder

```text
promptvault/
├── app.py
├── config.py
├── models.py
├── requirements.txt
├── vercel.json
├── .env.example
├── README.md
├── templates/
│   ├── base.html
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── dashboard.html
│   ├── prompts/
│   │   ├── index.html
│   │   ├── form.html
│   │   └── detail.html
│   ├── generator.html
│   └── tasks/
│       ├── index.html
│       └── form.html
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── app.js
```
