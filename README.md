# WiFi Auto Login untuk Hotspot

Script untuk mengotomatisasi login ke WiFi hotspot yang memerlukan login page, seperti `http://hotspot.padang.go.id`.

## Fitur

- ✅ Auto login ke hotspot dengan login page
- ✅ Deteksi otomatis form login
- ✅ Mode daemon untuk monitoring terus menerus
- ✅ **Auto reconnect setiap 24 jam untuk menghindari expire login**
- ✅ Service systemd untuk auto-start saat boot
- ✅ Logging lengkap
- ✅ Konfigurasi mudah
- ✅ Status monitoring dan force reconnect manual

## Persyaratan

- Ubuntu/Debian Linux
- Python 3.6+
- Koneksi WiFi ke hotspot

## Instalasi

### 1. Clone atau Download Script

```bash
# Jika menggunakan git
git clone <repository-url>
cd wifi-auto-login

# Atau download manual dan extract
```

### 2. Berikan Permission Execute

```bash
chmod +x wifi_auto_login.sh
chmod +x wifi_auto_login.py
```

### 3. Install Dependencies dan Setup Service

```bash
sudo ./wifi_auto_login.sh install
```

### 4. Setup Konfigurasi

```bash
./wifi_auto_login.sh setup
```

Masukkan username dan password hotspot Anda ketika diminta.

## Penggunaan

### Setup Awal

```bash
# Setup username dan password
./wifi_auto_login.sh setup
```

### Login Sekali

```bash
# Login sekali ke hotspot
./wifi_auto_login.sh login
```

### Jalankan sebagai Daemon

```bash
# Jalankan daemon (monitoring terus menerus dengan auto reconnect 24 jam)
./wifi_auto_login.sh daemon
```

### Cek Status

```bash
# Tampilkan status koneksi dan reconnect
./wifi_auto_login.sh status
```

### Force Reconnect

```bash
# Paksa reconnect sekarang (tanpa menunggu 24 jam)
./wifi_auto_login.sh force-reconnect
```

### Install Service (Auto-start saat boot)

```bash
# Install service systemd
sudo ./wifi_auto_login.sh install

# Start service
sudo systemctl start wifi-auto-login

# Enable auto-start saat boot
sudo systemctl enable wifi-auto-login

# Cek status
sudo systemctl status wifi-auto-login
```

### Cek Log

```bash
# Tampilkan log real-time
./wifi_auto_login.sh logs

# Atau cek log systemd
sudo journalctl -u wifi-auto-login -f
```

### Uninstall

```bash
# Hapus service
sudo ./wifi_auto_login.sh uninstall
```

## Konfigurasi

File konfigurasi disimpan di `/etc/wifi_auto_login/config.json`:

```json
{
  "hotspot_url": "http://hotspot.padang.go.id",
  "username": "your_username",
  "password": "your_password",
  "check_interval": 30,
  "max_retries": 3,
  "timeout": 10,
  "auto_reconnect_interval": 86400,
  "force_reconnect": true
}
```

### Parameter Konfigurasi

- `hotspot_url`: URL login page hotspot
- `username`: Username untuk login
- `password`: Password untuk login
- `check_interval`: Interval pengecekan koneksi (detik)
- `max_retries`: Jumlah maksimal percobaan login
- `timeout`: Timeout untuk request HTTP (detik)
- `auto_reconnect_interval`: Interval auto reconnect dalam detik (default: 86400 = 24 jam)
- `force_reconnect`: Aktifkan/nonaktifkan fitur auto reconnect (default: true)

## Troubleshooting

### 1. Error "BeautifulSoup not installed"

```bash
pip3 install beautifulsoup4
```

### 2. Error Permission Denied

```bash
# Pastikan script memiliki permission execute
chmod +x wifi_auto_login.sh
chmod +x wifi_auto_login.py

# Pastikan user memiliki akses ke direktori konfigurasi
sudo chown $USER:$USER /etc/wifi_auto_login
```

### 3. Service tidak start

```bash
# Cek log service
sudo journalctl -u wifi-auto-login -n 50

# Restart service
sudo systemctl restart wifi-auto-login
```

### 4. Login gagal

1. Pastikan username dan password benar
2. Cek apakah URL hotspot benar
3. Pastikan terhubung ke WiFi hotspot
4. Cek log untuk detail error

### 5. Internet tidak terdeteksi

Script menggunakan beberapa metode untuk mendeteksi koneksi internet:
- Google DNS (8.8.8.8)
- Cloudflare DNS (1.1.1.1)

Jika masih ada masalah, edit script untuk menambahkan DNS server lain.

## Struktur File

```
wifi-auto-login/
├── wifi_auto_login.py      # Script Python utama
├── wifi_auto_login.sh      # Script bash wrapper
├── README.md              # Dokumentasi ini
└── requirements.txt       # Dependencies Python
```

## Log

- File log: `/var/log/wifi_auto_login.log`
- Systemd log: `sudo journalctl -u wifi-auto-login`

## Keamanan

⚠️ **Peringatan Keamanan:**

1. Password disimpan dalam file JSON tanpa enkripsi
2. File konfigurasi hanya dapat diakses oleh user yang menjalankan script
3. Gunakan dengan bijak dan jangan bagikan kredensial

## Kontribusi

Jika menemukan bug atau ingin menambahkan fitur, silakan buat issue atau pull request.

## Lisensi

Script ini dibuat untuk keperluan pribadi dan edukasi. Gunakan dengan tanggung jawab. 

##@abonkfarouk##