#!/bin/bash

# WiFi Auto Login Script
# Untuk hotspot yang memerlukan login page seperti http://hotspot.padang.go.id

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/wifi_auto_login.py"
CONFIG_DIR="/etc/wifi_auto_login"
CONFIG_FILE="$CONFIG_DIR/config.json"
LOG_FILE="/var/log/wifi_auto_login.log"

# Fungsi untuk menampilkan bantuan
show_help() {
    echo "WiFi Auto Login Script"
    echo "====================="
    echo ""
    echo "Penggunaan: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  setup           - Setup konfigurasi awal (username dan password)"
    echo "  login           - Login sekali ke hotspot"
    echo "  daemon          - Jalankan sebagai daemon (terus memantau dengan auto reconnect 3 jam)"
    echo "  status          - Cek status koneksi dan reconnect"
    echo "  force-reconnect - Paksa reconnect sekarang"
    echo "  install         - Install dependencies dan setup service"
    echo "  uninstall       - Hapus service dan file konfigurasi"
    echo "  service-status  - Cek status service systemd"
    echo "  logs            - Tampilkan log"
    echo "  help            - Tampilkan bantuan ini"
    echo ""
    echo "Contoh:"
    echo "  $0 setup           # Setup username dan password"
    echo "  $0 login           # Login sekali"
    echo "  $0 daemon          # Jalankan sebagai daemon"
    echo "  $0 status          # Cek status koneksi"
    echo "  $0 force-reconnect # Paksa reconnect"
}

# Fungsi untuk cek apakah script Python ada
check_python_script() {
    if [ ! -f "$PYTHON_SCRIPT" ]; then
        echo "Error: Script Python tidak ditemukan di $PYTHON_SCRIPT"
        exit 1
    fi
}

# Fungsi untuk cek apakah Python3 tersedia
check_python3() {
    if ! command -v python3 &> /dev/null; then
        echo "Error: Python3 tidak ditemukan. Install Python3 terlebih dahulu."
        echo "Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip"
        exit 1
    fi
}

# Fungsi untuk install dependencies
install_dependencies() {
    echo "Installing dependencies..."
    
    # Try pip first, fallback to apt if pip fails
    echo "Trying pip installation..."
    if pip3 install --user requests beautifulsoup4 2>/dev/null; then
        echo "Dependencies installed via pip"
    else
        echo "pip installation failed, trying apt..."
        
        # Update package list
        sudo apt update
        
        # Install Python packages via apt
        sudo apt install -y python3-requests python3-bs4 python3-lxml
        
        # Check if packages are available in apt
        if ! dpkg -l | grep -q python3-requests; then
            echo "Some packages not available in apt, trying pip with --break-system-packages..."
            if pip3 install --break-system-packages requests beautifulsoup4 lxml; then
                echo "Dependencies installed via pip with --break-system-packages"
            else
                echo "Failed to install Python dependencies"
                echo "Please install manually:"
                echo "sudo apt install python3-requests python3-bs4 python3-lxml"
                echo "Or: pip3 install --break-system-packages requests beautifulsoup4 lxml"
                exit 1
            fi
        else
            echo "Dependencies installed via apt"
        fi
    fi
    
    # Buat direktori konfigurasi
    sudo mkdir -p "$CONFIG_DIR"
    sudo chown $USER:$USER "$CONFIG_DIR"
    
    # Buat file log
    sudo touch "$LOG_FILE"
    sudo chown $USER:$USER "$LOG_FILE"
    
    echo "Dependencies berhasil diinstall!"
}

# Fungsi untuk setup konfigurasi
setup_config() {
    check_python_script
    check_python3
    
    echo "=== Setup WiFi Auto Login ==="
    echo "Masukkan kredensial untuk hotspot:"
    echo ""
    
    python3 "$PYTHON_SCRIPT" --setup
}

# Fungsi untuk login sekali
do_login() {
    check_python_script
    check_python3
    
    echo "Mencoba login ke hotspot..."
    python3 "$PYTHON_SCRIPT"
}

# Fungsi untuk jalankan daemon
run_daemon() {
    check_python_script
    check_python3
    
    echo "Menjalankan WiFi Auto Login Daemon dengan auto reconnect 3 jam..."
    echo "Tekan Ctrl+C untuk menghentikan"
    python3 "$PYTHON_SCRIPT" --daemon
}

# Fungsi untuk cek status koneksi
check_connection_status() {
    check_python_script
    check_python3
    
    python3 "$PYTHON_SCRIPT" --status
}

# Fungsi untuk force reconnect
force_reconnect() {
    check_python_script
    check_python3
    
    echo "Melakukan force reconnect..."
    python3 "$PYTHON_SCRIPT" --force-reconnect
}

# Fungsi untuk install service
install_service() {
    check_python_script
    check_python3
    
    echo "Installing WiFi Auto Login Service..."
    
    # Install dependencies
    install_dependencies
    
    # Buat service file
    sudo tee /etc/systemd/system/wifi-auto-login.service > /dev/null <<EOF
[Unit]
Description=WiFi Auto Login Service
After=network.target

[Service]
Type=simple
User=$USER
ExecStart=/usr/bin/python3 $PYTHON_SCRIPT --daemon
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd dan enable service
    sudo systemctl daemon-reload
    sudo systemctl enable wifi-auto-login.service
    
    echo "Service berhasil diinstall!"
    echo "Untuk menjalankan: sudo systemctl start wifi-auto-login"
    echo "Untuk cek status: sudo systemctl status wifi-auto-login"
}

# Fungsi untuk uninstall service
uninstall_service() {
    echo "Uninstalling WiFi Auto Login Service..."
    
    # Stop dan disable service
    sudo systemctl stop wifi-auto-login.service 2>/dev/null || true
    sudo systemctl disable wifi-auto-login.service 2>/dev/null || true
    
    # Hapus service file
    sudo rm -f /etc/systemd/system/wifi-auto-login.service
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Hapus file konfigurasi dan log (opsional)
    read -p "Hapus file konfigurasi dan log? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo rm -rf "$CONFIG_DIR"
        sudo rm -f "$LOG_FILE"
        echo "File konfigurasi dan log dihapus."
    fi
    
    echo "Service berhasil diuninstall!"
}

# Fungsi untuk cek status service
check_service_status() {
    if systemctl is-active --quiet wifi-auto-login.service; then
        echo "Status: Service sedang berjalan"
        echo ""
        echo "Log terakhir:"
        sudo journalctl -u wifi-auto-login.service -n 10 --no-pager
    else
        echo "Status: Service tidak berjalan"
    fi
}

# Fungsi untuk tampilkan log
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo "=== WiFi Auto Login Log ==="
        tail -f "$LOG_FILE"
    else
        echo "File log tidak ditemukan: $LOG_FILE"
    fi
}

# Main script
case "${1:-help}" in
    setup)
        setup_config
        ;;
    login)
        do_login
        ;;
    daemon)
        run_daemon
        ;;
    status)
        check_connection_status
        ;;
    force-reconnect)
        force_reconnect
        ;;
    install)
        install_service
        ;;
    uninstall)
        uninstall_service
        ;;
    service-status)
        check_service_status
        ;;
    logs)
        show_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Error: Option tidak valid: $1"
        echo ""
        show_help
        exit 1
        ;;
esac 