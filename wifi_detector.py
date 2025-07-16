#!/usr/bin/env python3
"""
WiFi Interface Detector
Untuk mendeteksi interface WiFi dan status koneksi
"""

import subprocess
import re
import json
import os

def get_wifi_interfaces():
    """Dapatkan daftar interface WiFi"""
    try:
        # Gunakan ip link untuk mendapatkan interface
        result = subprocess.run(['ip', 'link', 'show'], 
                              capture_output=True, text=True, timeout=10)
        
        interfaces = []
        for line in result.stdout.split('\n'):
            # Cari interface yang dimulai dengan wl (wireless)
            if re.search(r'\d+:\s+(wl\w+):', line):
                match = re.search(r'\d+:\s+(wl\w+):', line)
                if match:
                    interfaces.append(match.group(1))
        
        return interfaces
    except Exception as e:
        print(f"Error getting WiFi interfaces: {e}")
        return []

def get_current_wifi_network(interface=None):
    """Dapatkan informasi network WiFi yang sedang terhubung"""
    try:
        if not interface:
            interfaces = get_wifi_interfaces()
            if not interfaces:
                return None
            interface = interfaces[0]  # Gunakan interface pertama
        
        # Gunakan iwgetid atau iw untuk mendapatkan SSID
        try:
            # Coba iwgetid dulu
            result = subprocess.run(['iwgetid', '-r', interface], 
                                  capture_output=True, text=True, timeout=10)
        except FileNotFoundError:
            # Fallback ke iw
            result = subprocess.run(['iw', 'dev', interface, 'info'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Parse output iw untuk mendapatkan SSID
                for line in result.stdout.split('\n'):
                    if 'ssid' in line.lower():
                        ssid = line.split()[-1].strip()
                        result = type('obj', (object,), {'returncode': 0, 'stdout': ssid})()
                        break
        
        if result.returncode == 0:
            ssid = result.stdout.strip()
            
            # Dapatkan informasi tambahan dengan iwconfig
            iw_result = subprocess.run(['iwconfig', interface], 
                                     capture_output=True, text=True, timeout=10)
            
            info = {
                'interface': interface,
                'ssid': ssid,
                'connected': True
            }
            
            # Parse iwconfig output untuk informasi tambahan
            if iw_result.returncode == 0:
                output = iw_result.stdout
                
                # Extract signal strength
                signal_match = re.search(r'Signal level=([-\d]+)', output)
                if signal_match:
                    info['signal_level'] = signal_match.group(1)
                
                # Extract frequency
                freq_match = re.search(r'Frequency=([\d.]+)', output)
                if freq_match:
                    info['frequency'] = freq_match.group(1)
            
            return info
        else:
            return {
                'interface': interface,
                'ssid': None,
                'connected': False
            }
            
    except Exception as e:
        print(f"Error getting WiFi network info: {e}")
        return None

def check_hotspot_connection():
    """Cek apakah terhubung ke hotspot yang memerlukan login"""
    try:
        # Coba akses situs yang biasanya diblokir oleh captive portal
        import requests
        
        # Test beberapa situs
        test_urls = [
            'http://www.google.com',
            'http://www.facebook.com',
            'http://www.youtube.com'
        ]
        
        for url in test_urls:
            try:
                response = requests.get(url, timeout=5)
                # Jika redirect ke halaman login, berarti ada captive portal
                if 'hotspot' in response.url.lower() or 'login' in response.url.lower():
                    return True
            except:
                continue
        
        return False
        
    except Exception as e:
        print(f"Error checking hotspot connection: {e}")
        return False

def get_network_info():
    """Dapatkan informasi lengkap network"""
    info = {
        'wifi_interfaces': get_wifi_interfaces(),
        'current_network': None,
        'is_hotspot': False
    }
    
    if info['wifi_interfaces']:
        info['current_network'] = get_current_wifi_network()
        if info['current_network'] and info['current_network']['connected']:
            info['is_hotspot'] = check_hotspot_connection()
    
    return info

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='WiFi Network Detector')
    parser.add_argument('--json', action='store_true', 
                       help='Output dalam format JSON')
    parser.add_argument('--interface', 
                       help='Interface WiFi spesifik')
    
    args = parser.parse_args()
    
    if args.interface:
        network_info = get_current_wifi_network(args.interface)
        if network_info:
            network_info['is_hotspot'] = check_hotspot_connection()
        else:
            network_info = {
                'interface': args.interface,
                'ssid': None,
                'connected': False,
                'is_hotspot': False
            }
    else:
        network_info = get_network_info()
    
    if args.json:
        print(json.dumps(network_info, indent=2))
    else:
        print("=== WiFi Network Information ===")
        print(f"WiFi Interfaces: {network_info.get('wifi_interfaces', [])}")
        
        current = network_info.get('current_network')
        if current:
            print(f"Current Interface: {current['interface']}")
            print(f"SSID: {current['ssid']}")
            print(f"Connected: {current['connected']}")
            if 'signal_level' in current:
                print(f"Signal Level: {current['signal_level']}")
            if 'frequency' in current:
                print(f"Frequency: {current['frequency']}")
        
        print(f"Is Hotspot (requires login): {network_info.get('is_hotspot', False)}")

if __name__ == "__main__":
    main() 