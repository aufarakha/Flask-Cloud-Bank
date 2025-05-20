# Flask Cloud Bank

Aplikasi perbankan web modern yang dibangun dengan Flask, dilengkapi dengan otentikasi pengguna, transfer uang, riwayat transaksi, dan panel admin.

[Read in English](README.md)

## Fitur

- Otentikasi dan registrasi pengguna
- Transfer uang antar rekening
- Pelacakan riwayat transaksi
- Kurs mata uang real-time
- Panel admin untuk manajemen pengguna
- Dukungan multi-bahasa (Inggris/Indonesia)
- Toggle mode Gelap/Terang
- Manajemen foto profil

## Instalasi

1. Clone repository:

```bash
git clone https://github.com/yourusername/Flask-Cloud-Bank.git
cd Flask-Cloud-Bank
```

2. Buat dan aktifkan virtual environment:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

3. Install paket yang diperlukan:

```bash
pip install -r requirements.txt
```

4. Buat file `.env` di direktori utama dan tambahkan API key untuk Exchange Rate:

```
EXCHANGE_API_KEY=your_api_key_here
```

5. Inisialisasi database:

```bash
python db_setup.py
```

6. Jalankan aplikasi:

```bash
python app.py
```

7. Akses aplikasi di `http://localhost:5000`

Akun owner default:

- Email: owner@cloudbank.com
- Password: ownerpass

## Struktur Proyek

```
Flask-Cloud-Bank/
├── app.py              # File aplikasi utama
├── models.py           # Model database
├── db_setup.py         # Inisialisasi database
├── requirements.txt    # Dependensi proyek
├── static/            # File statis (CSS, JS, gambar)
├── templates/         # Template HTML
└── instance/         # Database SQLite
```

## Tech Stack

- Flask - Web framework
- SQLAlchemy - Database ORM
- Flask-Login - Otentikasi pengguna
- SQLite - Database
- Exchange Rate API - Konversi mata uang

## Lisensi

Proyek ini dilisensikan di bawah Apache License 2.0 - lihat file [LICENSE](LICENSE) untuk detailnya.
