#!/usr/bin/env python3
"""
Auto Login WiFi Hotspot Script
Untuk hotspot yang memerlukan login page seperti http://hotspot.padang.go.id
"""

import requests
import time
import json
import os
import sys
import logging
from urllib.parse import urljoin, urlparse
from datetime import datetime

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/wifi_auto_login.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class WiFiAutoLogin:
    def __init__(self, config_file='/etc/wifi_auto_login/config.json'):
        self.config_file = config_file
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.config = self.load_config()
        self.last_login_time = None
        self.reconnect_interval = 3 * 60 * 60  # 3 jam dalam detik
        self.load_last_login_time()
        
    def load_config(self):
        """Load konfigurasi dari file JSON"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            else:
                # Konfigurasi default
                default_config = {
                    "hotspot_url": "http://hotspot.padang.go.id",
                    "username": "",
                    "password": "",
                    "check_interval": 30,  # detik
                    "max_retries": 3,
                    "timeout": 10,
                    "auto_reconnect_interval": 3 * 60 * 60,  # 3 jam dalam detik
                    "force_reconnect": True
                }
                self.save_config(default_config)
                return default_config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def save_config(self, config):
        """Simpan konfigurasi ke file JSON"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def save_last_login_time(self):
        """Simpan waktu login terakhir ke file"""
        try:
            if self.last_login_time:
                config = self.config.copy()
                config['last_login_time'] = self.last_login_time.isoformat()
                self.save_config(config)
        except Exception as e:
            logger.error(f"Error saving last login time: {e}")
    
    def load_last_login_time(self):
        """Muat waktu login terakhir dari file"""
        try:
            if 'last_login_time' in self.config:
                self.last_login_time = datetime.fromisoformat(self.config['last_login_time'])
                logger.info(f"Last login time loaded: {self.last_login_time}")
        except Exception as e:
            logger.error(f"Error loading last login time: {e}")
            self.last_login_time = None
    
    def get_status_info(self):
        """Dapatkan informasi status koneksi dan reconnect"""
        current_time = datetime.now()
        status_info = {
            'internet_connected': self.check_internet_connection(),
            'last_login_time': self.last_login_time,
            'current_time': current_time,
            'force_reconnect_enabled': self.config.get('force_reconnect', True),
            'reconnect_interval_hours': self.config.get('auto_reconnect_interval', 24*60*60) / 3600
        }
        
        if self.last_login_time:
            time_since_login = (current_time - self.last_login_time).total_seconds()
            status_info['time_since_login_seconds'] = time_since_login
            status_info['time_since_login_hours'] = time_since_login / 3600
            status_info['next_reconnect_in_hours'] = max(0, (self.config.get('auto_reconnect_interval', 24*60*60) - time_since_login) / 3600)
        else:
            status_info['time_since_login_seconds'] = None
            status_info['time_since_login_hours'] = None
            status_info['next_reconnect_in_hours'] = None
        
        return status_info
    
    def check_internet_connection(self):
        """Cek apakah sudah terhubung ke internet"""
        try:
            # Coba akses Google DNS
            response = self.session.get('http://8.8.8.8', timeout=5)
            return True
        except:
            try:
                # Coba akses Cloudflare DNS
                response = self.session.get('http://1.1.1.1', timeout=5)
                return True
            except:
                return False
    
    def check_hotspot_captive_portal(self):
        """Cek apakah ada captive portal"""
        try:
            # Coba akses situs yang biasanya diblokir oleh captive portal
            response = self.session.get('http://www.google.com', timeout=5)
            if 'hotspot' in response.url.lower() or 'login' in response.url.lower():
                return True
            return False
        except:
            return True
    
    def get_hotspot_login_page(self):
        """Dapatkan halaman login hotspot"""
        try:
            response = self.session.get(self.config['hotspot_url'], timeout=self.config['timeout'])
            logger.info(f"Hotspot login page accessed: {response.url}")
            return response
        except Exception as e:
            logger.error(f"Error accessing hotspot login page: {e}")
            return None
    
    def find_login_form(self, response):
        """Temukan form login dalam halaman"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Cari form login
            forms = soup.find_all('form')
            for form in forms:
                # Cek apakah form memiliki input username/password
                inputs = form.find_all('input')
                has_username = any(input.get('name', '').lower() in ['username', 'user', 'email', 'login'] for input in inputs)
                has_password = any(input.get('type') == 'password' for input in inputs)
                
                if has_username and has_password:
                    return form
            
            return None
        except ImportError:
            logger.error("BeautifulSoup not installed. Install with: pip3 install beautifulsoup4")
            return None
        except Exception as e:
            logger.error(f"Error parsing login form: {e}")
            return None
    
    def submit_login(self, form, response):
        """Submit form login"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Dapatkan action URL
            action_url = form.get('action')
            if not action_url:
                action_url = response.url
            elif not action_url.startswith('http'):
                action_url = urljoin(response.url, action_url)
            
            # Siapkan data form
            form_data = {}
            inputs = form.find_all('input')
            
            for input_field in inputs:
                name = input_field.get('name')
                value = input_field.get('value', '')
                
                if name:
                    if 'username' in name.lower() or 'user' in name.lower() or 'email' in name.lower() or 'login' in name.lower():
                        form_data[name] = self.config['username']
                    elif input_field.get('type') == 'password':
                        form_data[name] = self.config['password']
                    else:
                        form_data[name] = value
            
            # Submit form
            logger.info(f"Submitting login form to: {action_url}")
            login_response = self.session.post(action_url, data=form_data, timeout=self.config['timeout'])
            
            return login_response
            
        except Exception as e:
            logger.error(f"Error submitting login form: {e}")
            return None
    
    def login(self, force_reconnect=False):
        """Proses login utama"""
        if not self.config.get('username') or not self.config.get('password'):
            logger.error("Username atau password belum dikonfigurasi")
            return False
        
        try:
            # Dapatkan halaman login
            response = self.get_hotspot_login_page()
            if not response:
                return False
            
            # Temukan form login
            form = self.find_login_form(response)
            if not form:
                logger.error("Form login tidak ditemukan")
                return False
            
            # Submit login
            login_response = self.submit_login(form, response)
            if not login_response:
                return False
            
            # Cek apakah login berhasil
            if self.check_internet_connection():
                self.last_login_time = datetime.now()
                self.save_last_login_time()
                if force_reconnect:
                    logger.info("Force reconnect berhasil! Internet terhubung.")
                else:
                    logger.info("Login berhasil! Internet terhubung.")
                return True
            else:
                logger.warning("Login mungkin gagal, internet belum terhubung")
                return False
                
        except Exception as e:
            logger.error(f"Error during login process: {e}")
            return False
    
    def run_daemon(self):
        """Jalankan sebagai daemon untuk terus memantau koneksi"""
        logger.info("Memulai WiFi Auto Login Daemon dengan auto reconnect 3 jam")
        
        while True:
            try:
                current_time = datetime.now()
                force_reconnect_needed = False
                
                # Cek apakah perlu force reconnect (setelah 3 jam)
                if (self.last_login_time and 
                    self.config.get('force_reconnect', True) and
                    (current_time - self.last_login_time).total_seconds() >= self.config.get('auto_reconnect_interval', 3*60*60)):
                    logger.info("Sudah 3 jam sejak login terakhir, melakukan force reconnect...")
                    force_reconnect_needed = True
                
                # Cek apakah sudah terhubung ke internet
                if not self.check_internet_connection() or force_reconnect_needed:
                    if force_reconnect_needed:
                        logger.info("Melakukan force reconnect untuk menghindari expire login...")
                    else:
                        logger.info("Tidak ada koneksi internet, mencoba login...")
                    
                    # Coba login beberapa kali
                    for attempt in range(self.config.get('max_retries', 3)):
                        logger.info(f"Percobaan login ke-{attempt + 1}")
                        if self.login(force_reconnect=force_reconnect_needed):
                            break
                        time.sleep(2)
                else:
                    logger.debug("Internet sudah terhubung")
                
                # Tunggu sebelum cek lagi
                time.sleep(self.config.get('check_interval', 30))
                
            except KeyboardInterrupt:
                logger.info("Daemon dihentikan oleh user")
                break
            except Exception as e:
                logger.error(f"Error in daemon: {e}")
                time.sleep(10)

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='WiFi Auto Login untuk Hotspot')
    parser.add_argument('--config', default='/etc/wifi_auto_login/config.json', 
                       help='Path ke file konfigurasi')
    parser.add_argument('--daemon', action='store_true', 
                       help='Jalankan sebagai daemon')
    parser.add_argument('--setup', action='store_true', 
                       help='Setup konfigurasi awal')
    parser.add_argument('--status', action='store_true', 
                       help='Tampilkan status koneksi dan reconnect')
    parser.add_argument('--force-reconnect', action='store_true', 
                       help='Paksa reconnect sekarang')
    
    args = parser.parse_args()
    
    auto_login = WiFiAutoLogin(args.config)
    
    if args.setup:
        # Setup konfigurasi
        print("=== Setup WiFi Auto Login ===")
        username = input("Username: ")
        password = input("Password: ")
        
        auto_login.config['username'] = username
        auto_login.config['password'] = password
        auto_login.save_config(auto_login.config)
        
        print("Konfigurasi berhasil disimpan!")
        
    elif args.status:
        # Tampilkan status
        status = auto_login.get_status_info()
        print("=== Status WiFi Auto Login ===")
        print(f"Internet terhubung: {'Ya' if status['internet_connected'] else 'Tidak'}")
        print(f"Force reconnect aktif: {'Ya' if status['force_reconnect_enabled'] else 'Tidak'}")
        print(f"Interval reconnect: {status['reconnect_interval_hours']:.1f} jam")
        
        if status['last_login_time']:
            print(f"Login terakhir: {status['last_login_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Waktu sejak login: {status['time_since_login_hours']:.1f} jam")
            if status['next_reconnect_in_hours'] > 0:
                print(f"Reconnect berikutnya dalam: {status['next_reconnect_in_hours']:.1f} jam")
            else:
                print("Reconnect akan dilakukan pada cek berikutnya")
        else:
            print("Belum ada login sebelumnya")
        
    elif args.force_reconnect:
        # Paksa reconnect
        print("Melakukan force reconnect...")
        if auto_login.login(force_reconnect=True):
            print("Force reconnect berhasil!")
        else:
            print("Force reconnect gagal!")
            sys.exit(1)
        
    elif args.daemon:
        # Jalankan sebagai daemon
        auto_login.run_daemon()
    else:
        # Jalankan sekali
        if auto_login.login():
            print("Login berhasil!")
        else:
            print("Login gagal!")
            sys.exit(1)

if __name__ == "__main__":
    main() 