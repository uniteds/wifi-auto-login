#!/usr/bin/env python3
"""
Test WiFi Connection Script
Untuk mengetes koneksi WiFi dan mendeteksi hotspot
"""

import sys
import time
import subprocess
from wifi_detector import get_network_info, check_hotspot_connection

def test_internet_connection():
    """Test koneksi internet"""
    print("=== Testing Internet Connection ===")
    
    try:
        import requests
        
        test_urls = [
            'http://www.google.com',
            'http://www.cloudflare.com',
            'http://www.github.com'
        ]
        
        for url in test_urls:
            try:
                print(f"Testing {url}...")
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ {url} - OK")
                else:
                    print(f"⚠️  {url} - Status: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"❌ {url} - Error: {e}")
                
    except ImportError:
        print("❌ requests module not installed")
        print("Install with: pip3 install requests")

def test_wifi_info():
    """Test informasi WiFi"""
    print("\n=== Testing WiFi Information ===")
    
    try:
        info = get_network_info()
        
        print(f"WiFi Interfaces: {info.get('wifi_interfaces', [])}")
        
        current = info.get('current_network')
        if current:
            print(f"Current Interface: {current['interface']}")
            print(f"SSID: {current['ssid']}")
            print(f"Connected: {current['connected']}")
            if 'signal_level' in current:
                print(f"Signal Level: {current['signal_level']}")
            if 'frequency' in current:
                print(f"Frequency: {current['frequency']}")
        else:
            print("❌ No WiFi connection detected")
            
        print(f"Is Hotspot: {info.get('is_hotspot', False)}")
        
    except Exception as e:
        print(f"❌ Error getting WiFi info: {e}")

def test_hotspot_detection():
    """Test deteksi hotspot"""
    print("\n=== Testing Hotspot Detection ===")
    
    try:
        is_hotspot = check_hotspot_connection()
        if is_hotspot:
            print("🔒 Hotspot detected - Login required")
        else:
            print("✅ No hotspot detected - Internet should work")
    except Exception as e:
        print(f"❌ Error detecting hotspot: {e}")

def test_hotspot_url():
    """Test akses ke URL hotspot"""
    print("\n=== Testing Hotspot URL ===")
    
    hotspot_url = "http://hotspot.padang.go.id"
    
    try:
        import requests
        
        print(f"Testing {hotspot_url}...")
        response = requests.get(hotspot_url, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Final URL: {response.url}")
        print(f"Content Length: {len(response.text)} characters")
        
        if "login" in response.text.lower() or "hotspot" in response.text.lower():
            print("✅ Login page detected")
        else:
            print("⚠️  Login page not clearly detected")
            
    except Exception as e:
        print(f"❌ Error accessing hotspot URL: {e}")

def test_network_tools():
    """Test tools network yang diperlukan"""
    print("\n=== Testing Network Tools ===")
    
    tools = [
        ('ip', 'ip link show'),
        ('iwgetid', 'iwgetid'),
        ('iwconfig', 'iwconfig'),
        ('ping', 'ping -c 1 8.8.8.8')
    ]
    
    for tool, command in tools:
        try:
            result = subprocess.run(command.split(), 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ {tool} - OK")
            else:
                print(f"⚠️  {tool} - Error: {result.stderr.strip()}")
        except Exception as e:
            print(f"❌ {tool} - Not found or error: {e}")

def main():
    """Main function"""
    print("WiFi Connection Test")
    print("===================")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test network tools
    test_network_tools()
    
    # Test WiFi info
    test_wifi_info()
    
    # Test internet connection
    test_internet_connection()
    
    # Test hotspot detection
    test_hotspot_detection()
    
    # Test hotspot URL
    test_hotspot_url()
    
    print("\n=== Test Complete ===")
    print("Jika hotspot terdeteksi, Anda bisa menggunakan:")
    print("  ./wifi_auto_login.sh setup    # Setup username/password")
    print("  ./wifi_auto_login.sh login    # Test login")
    print("  ./wifi_auto_login.sh daemon   # Jalankan daemon")

if __name__ == "__main__":
    main() 