#!/bin/bash

# WiFi Auto Login Installer
# Script instalasi lengkap untuk Ubuntu/Debian

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/wifi-auto-login"
SERVICE_NAME="wifi-auto-login"
CONFIG_DIR="/etc/wifi_auto_login"
LOG_FILE="/var/log/wifi_auto_login.log"

# Functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "Script ini tidak boleh dijalankan sebagai root"
        exit 1
    fi
}

check_system() {
    print_status "Checking system requirements..."
    
    # Check OS
    if [[ ! -f /etc/os-release ]]; then
        print_error "Sistem operasi tidak dikenali"
        exit 1
    fi
    
    source /etc/os-release
    if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
        print_warning "Script ini diuji untuk Ubuntu/Debian. Sistem lain mungkin tidak kompatibel."
    fi
    
    # Check Python3
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 tidak ditemukan. Install terlebih dahulu:"
        echo "sudo apt update && sudo apt install python3 python3-pip"
        exit 1
    fi
    
    # Check pip3
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 tidak ditemukan. Install terlebih dahulu:"
        echo "sudo apt install python3-pip"
        exit 1
    fi
    
    print_success "System requirements OK"
}

install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Try pip first, fallback to apt if pip fails
    print_status "Trying pip installation..."
    if pip3 install --user requests beautifulsoup4 lxml 2>/dev/null; then
        print_success "Dependencies installed via pip"
    else
        print_warning "pip installation failed, trying apt..."
        
        # Update package list
        sudo apt update
        
        # Install Python packages via apt
        sudo apt install -y python3-requests python3-bs4 python3-lxml
        
        # Check if packages are available in apt
        if ! dpkg -l | grep -q python3-requests; then
            print_warning "Some packages not available in apt, trying pip with --break-system-packages..."
            if pip3 install --break-system-packages requests beautifulsoup4 lxml; then
                print_success "Dependencies installed via pip with --break-system-packages"
            else
                print_error "Failed to install Python dependencies"
                print_error "Please install manually:"
                echo "sudo apt install python3-requests python3-bs4 python3-lxml"
                echo "Or: pip3 install --break-system-packages requests beautifulsoup4 lxml"
                exit 1
            fi
        else
            print_success "Dependencies installed via apt"
        fi
    fi
    
    # Install system packages
    print_status "Installing system packages..."
    sudo apt install -y wireless-tools iw
    
    print_success "All dependencies installed"
}

create_directories() {
    print_status "Creating directories..."
    
    # Create install directory
    sudo mkdir -p "$INSTALL_DIR"
    
    # Create config directory
    sudo mkdir -p "$CONFIG_DIR"
    
    # Set ownership
    sudo chown $USER:$USER "$INSTALL_DIR"
    sudo chown $USER:$USER "$CONFIG_DIR"
    
    print_success "Directories created"
}

copy_files() {
    print_status "Copying files..."
    
    # Copy Python scripts
    sudo cp "$SCRIPT_DIR/wifi_auto_login.py" "$INSTALL_DIR/"
    sudo cp "$SCRIPT_DIR/wifi_detector.py" "$INSTALL_DIR/"
    
    # Copy bash script
    sudo cp "$SCRIPT_DIR/wifi_auto_login.sh" "$INSTALL_DIR/"
    
    # Set permissions
    sudo chmod +x "$INSTALL_DIR/wifi_auto_login.py"
    sudo chmod +x "$INSTALL_DIR/wifi_detector.py"
    sudo chmod +x "$INSTALL_DIR/wifi_auto_login.sh"
    
    # Create symlink
    sudo ln -sf "$INSTALL_DIR/wifi_auto_login.sh" /usr/local/bin/wifi-auto-login
    
    print_success "Files copied"
}

create_log_file() {
    print_status "Creating log file..."
    
    sudo touch "$LOG_FILE"
    sudo chown $USER:$USER "$LOG_FILE"
    
    print_success "Log file created"
}

create_service() {
    print_status "Creating systemd service..."
    
    sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=WiFi Auto Login Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/wifi_auto_login.py --daemon
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Environment
Environment=PYTHONPATH=$INSTALL_DIR

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    sudo systemctl daemon-reload
    
    print_success "Service created"
}

setup_config() {
    print_status "Setting up initial configuration..."
    
    # Create default config
    cat > "$CONFIG_DIR/config.json" <<EOF
{
  "hotspot_url": "http://hotspot.padang.go.id",
  "username": "",
  "password": "",
  "check_interval": 30,
  "max_retries": 3,
  "timeout": 10
}
EOF

    print_success "Configuration file created"
    print_warning "Jangan lupa untuk setup username dan password dengan: wifi-auto-login setup"
}

enable_service() {
    print_status "Enabling service..."
    
    sudo systemctl enable $SERVICE_NAME
    
    print_success "Service enabled"
}

show_usage() {
    echo ""
    echo "=== WiFi Auto Login Installation Complete ==="
    echo ""
    echo "Next steps:"
    echo "1. Setup username dan password:"
    echo "   wifi-auto-login setup"
    echo ""
    echo "2. Test login sekali:"
    echo "   wifi-auto-login login"
    echo ""
    echo "3. Start service:"
    echo "   sudo systemctl start $SERVICE_NAME"
    echo ""
    echo "4. Check status:"
    echo "   sudo systemctl status $SERVICE_NAME"
    echo ""
    echo "5. View logs:"
    echo "   wifi-auto-login logs"
    echo ""
    echo "Service akan auto-start saat boot"
    echo ""
}

uninstall() {
    print_status "Uninstalling WiFi Auto Login..."
    
    # Stop and disable service
    sudo systemctl stop $SERVICE_NAME 2>/dev/null || true
    sudo systemctl disable $SERVICE_NAME 2>/dev/null || true
    
    # Remove service file
    sudo rm -f /etc/systemd/system/$SERVICE_NAME.service
    
    # Remove symlink
    sudo rm -f /usr/local/bin/wifi-auto-login
    
    # Remove install directory
    sudo rm -rf "$INSTALL_DIR"
    
    # Remove config and log (ask first)
    read -p "Hapus file konfigurasi dan log? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo rm -rf "$CONFIG_DIR"
        sudo rm -f "$LOG_FILE"
        print_success "Configuration and log files removed"
    fi
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    print_success "Uninstallation complete"
}

main() {
    echo "WiFi Auto Login Installer"
    echo "========================"
    echo ""
    
    # Check if uninstall
    if [[ "$1" == "uninstall" ]]; then
        uninstall
        exit 0
    fi
    
    # Check root
    check_root
    
    # Check system
    check_system
    
    # Install dependencies
    install_dependencies
    
    # Create directories
    create_directories
    
    # Copy files
    copy_files
    
    # Create log file
    create_log_file
    
    # Create service
    create_service
    
    # Setup config
    setup_config
    
    # Enable service
    enable_service
    
    # Show usage
    show_usage
    
    print_success "Installation completed successfully!"
}

# Run main function
main "$@" 