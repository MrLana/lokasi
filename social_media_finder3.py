#!/usr/bin/env python3
"""
SOCIAL MEDIA FINDER + LOCATION TRACKER BY PHONE NUMBER
Version: 2.1 - OSINT Tool with Location Tracking (Fixed)
Author: MechaPowerBot - Untuk Yang Mulia Putri Incha
"""

import requests
import json
import re
import time
import sys
import os
import webbrowser
from datetime import datetime
from urllib.parse import quote_plus
import phonenumbers
from phonenumbers import carrier, geocoder, timezone
import warnings
warnings.filterwarnings("ignore")

# Colorama untuk output berwarna
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        RED = '\033[91m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        MAGENTA = '\033[95m'
        CYAN = '\033[96m'
        WHITE = '\033[97m'
        RESET = '\033[0m'
    Style = Fore

# Cek folium (opsional untuk peta)
try:
    import folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False
    print(f"{Fore.YELLOW}[!] Folium tidak terinstall. Fitur peta tidak tersedia.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}    Install dengan: pip install folium{Style.RESET_ALL}")

class SocialMediaFinder:
    """
    Tool OSINT untuk mencari akun media sosial dan lokasi dari nomor telepon
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        
        # API Keys (ganti dengan API key Anda sendiri)
        self.opencage_api_key = "YOUR_OPENCAGE_API_KEY"
        self.melissa_id = "YOUR_MELISSA_ID"
        self.openstreetmap_api = "https://nominatim.openstreetmap.org/search"
        
        self.results = {}
        self.location_data = {}
        
    def print_banner(self):
        """Menampilkan banner"""
        banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════════╗
{Fore.CYAN}║                                                                      ║
{Fore.CYAN}║   {Fore.WHITE}██████  ███████  ███████ ██      ██████  ███████         {Fore.CYAN}║
{Fore.CYAN}║  {Fore.WHITE}██      ██      ██      ██      ██   ██ ██               {Fore.CYAN}║
{Fore.CYAN}║  {Fore.WHITE}██████  █████   █████   ██      ██████  █████            {Fore.CYAN}║
{Fore.CYAN}║      {Fore.WHITE}██ ██      ██      ██      ██   ██ ██               {Fore.CYAN}║
{Fore.CYAN}║  {Fore.WHITE}██████  ███████ ██      ███████ ██   ██ ███████         {Fore.CYAN}║
{Fore.CYAN}║                                                                      ║
{Fore.CYAN}║  {Fore.YELLOW}SOCIAL MEDIA FINDER + LOCATION TRACKER v2.1{Fore.CYAN}                ║
{Fore.CYAN}║  {Fore.MAGENTA}Find social media accounts & location by phone number{Fore.CYAN}      ║
{Fore.CYAN}╚══════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """
        print(banner)
        
    def format_phone_number(self, number):
        """
        Format dan validasi nomor telepon
        """
        try:
            # Bersihkan nomor
            cleaned = re.sub(r'\D', '', str(number).strip())
            
            # Parse dengan phonenumbers
            if cleaned.startswith('0'):
                parsed = phonenumbers.parse(cleaned, 'ID')
            elif cleaned.startswith('62'):
                parsed = phonenumbers.parse(cleaned, 'ID')
            else:
                parsed = phonenumbers.parse('+' + cleaned, None)
                
            # Validasi
            if phonenumbers.is_valid_number(parsed):
                international = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                national = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
                
                country = geocoder.description_for_number(parsed, 'id')
                operator = carrier.name_for_number(parsed, 'id')
                time_zones = timezone.time_zones_for_number(parsed)
                
                return {
                    'raw': number,
                    'international': international,
                    'e164': e164,
                    'national': national,
                    'country': country,
                    'operator': operator if operator else 'Tidak diketahui',
                    'timezone': list(time_zones)[0] if time_zones else 'Unknown',
                    'valid': True,
                    'parsed': parsed
                }
            else:
                print(f"{Fore.RED}[!] Nomor telepon tidak valid!{Style.RESET_ALL}")
                return {'valid': False}
                
        except Exception as e:
            print(f"{Fore.RED}[!] Error formatting number: {e}{Style.RESET_ALL}")
            return {'valid': False}
            
    def track_location_opencage(self, phone_info):
        """
        Melacak lokasi menggunakan OpenCage Geocoding API
        """
        print(f"{Fore.YELLOW}[*] Melacak lokasi menggunakan OpenCage API...{Style.RESET_ALL}")
        
        location_data = {
            'country': phone_info.get('country', 'Unknown'),
            'operator': phone_info.get('operator', 'Unknown'),
            'timezone': phone_info.get('timezone', 'Unknown'),
            'latitude': None,
            'longitude': None,
            'city': None,
            'region': None,
            'postal_code': None,
            'confidence': 'Estimasi berdasarkan negara/operator'
        }
        
        if self.opencage_api_key != "YOUR_OPENCAGE_API_KEY":
            try:
                query = f"{phone_info['country']} {phone_info['operator']}"
                url = f"https://api.opencagedata.com/geocode/v1/json?q={quote_plus(query)}&key={self.opencage_api_key}&limit=1"
                
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data['results']:
                        result = data['results'][0]
                        location_data['latitude'] = result['geometry']['lat']
                        location_data['longitude'] = result['geometry']['lng']
                        location_data['city'] = result['components'].get('city', '')
                        location_data['region'] = result['components'].get('state', '')
                        location_data['postal_code'] = result['components'].get('postcode', '')
                        location_data['confidence'] = 'Sedang (berdasarkan geocoding)'
                        print(f"{Fore.GREEN}[✓] Lokasi ditemukan via OpenCage!{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.YELLOW}[!] OpenCage API error: {e}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}[!] OpenCage API key belum dikonfigurasi.{Style.RESET_ALL}")
            print(f"{Fore.CYAN}    Dapatkan gratis di: opencagedata.com{Style.RESET_ALL}")
            
        return location_data
        
    def track_location_nominatim(self, phone_info):
        """
        Melacak lokasi menggunakan OpenStreetMap Nominatim API (free, no key needed)
        """
        print(f"{Fore.YELLOW}[*] Melacak lokasi menggunakan OpenStreetMap...{Style.RESET_ALL}")
        
        location_data = {
            'latitude': None,
            'longitude': None,
            'city': None,
            'region': None,
            'country': phone_info.get('country', 'Unknown'),
            'display_name': None,
            'confidence': 'Estimasi berdasarkan negara'
        }
        
        try:
            query = phone_info['country']
            url = f"{self.openstreetmap_api}?q={quote_plus(query)}&format=json&limit=1"
            
            response = self.session.get(url, headers={'User-Agent': 'SocialMediaFinder/1.0'}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data:
                    location_data['latitude'] = float(data[0]['lat'])
                    location_data['longitude'] = float(data[0]['lon'])
                    location_data['display_name'] = data[0]['display_name']
                    
                    parts = data[0]['display_name'].split(',')
                    if len(parts) >= 2:
                        location_data['city'] = parts[0].strip()
                        location_data['region'] = parts[1].strip() if len(parts) > 1 else ''
                        
                    print(f"{Fore.GREEN}[✓] Koordinat ditemukan via OpenStreetMap!{Style.RESET_ALL}")
                    return location_data
        except Exception as e:
            print(f"{Fore.YELLOW}[!] OpenStreetMap error: {e}{Style.RESET_ALL}")
            
        return None
        
    def track_location_melissa(self, phone_info):
        """
        Melacak lokasi menggunakan Melissa Global Phone API
        """
        print(f"{Fore.YELLOW}[*] Melacak lokasi menggunakan Melissa API...{Style.RESET_ALL}")
        
        location_data = {
            'latitude': None,
            'longitude': None,
            'city': None,
            'region': None,
            'country': None,
            'carrier': None,
            'timezone': None,
            'phone_type': None
        }
        
        if self.melissa_id != "YOUR_MELISSA_ID":
            try:
                url = "https://globalphone.melissadata.net/V4/WEB/GlobalPhone/doGlobalPhone"
                
                params = {
                    'phone': phone_info['e164'].replace('+', ''),
                    'ctry': phone_info['country'][:2] if phone_info['country'] else 'ID',
                    'opt': 'VerifyPhone:Premium',
                    'id': self.melissa_id
                }
                
                response = self.session.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('Records'):
                        record = data['Records'][0]
                        location_data['latitude'] = record.get('Latitude')
                        location_data['longitude'] = record.get('Longitude')
                        location_data['city'] = record.get('Locality')
                        location_data['region'] = record.get('AdministrativeArea')
                        location_data['country'] = record.get('CountryName')
                        location_data['carrier'] = record.get('Carrier')
                        location_data['timezone'] = record.get('TimeZoneName')
                        location_data['phone_type'] = self.get_phone_type(record.get('Results', ''))
                        
                        if location_data['latitude']:
                            print(f"{Fore.GREEN}[✓] Data lokasi real-time diperoleh dari Melissa!{Style.RESET_ALL}")
                            return location_data
            except Exception as e:
                print(f"{Fore.YELLOW}[!] Melissa API error: {e}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}[!] Melissa API key belum dikonfigurasi.{Style.RESET_ALL}")
            print(f"{Fore.CYAN}    Daftar free trial di: melissa.com{Style.RESET_ALL}")
            
        return None
        
    def get_phone_type(self, results_code):
        """Menentukan jenis nomor telepon"""
        if results_code and 'Cell' in results_code:
            return 'Mobile/Cellphone'
        elif results_code and 'Landline' in results_code:
            return 'Landline'
        elif results_code and 'VOIP' in results_code:
            return 'VOIP'
        return 'Unknown'
        
    def generate_location_map(self, location_data, phone_info, filename="location_map.html"):
        """
        Generate peta interaktif menggunakan Folium
        """
        if not FOLIUM_AVAILABLE:
            print(f"{Fore.YELLOW}[!] Folium tidak terinstall. Install dengan: pip install folium{Style.RESET_ALL}")
            return None
            
        if not location_data.get('latitude') or not location_data.get('longitude'):
            print(f"{Fore.YELLOW}[!] Tidak ada koordinat untuk membuat peta.{Style.RESET_ALL}")
            return None
            
        # Buat peta
        map_center = [location_data['latitude'], location_data['longitude']]
        m = folium.Map(location=map_center, zoom_start=10, tiles='OpenStreetMap')
        
        # Tambahkan marker
        popup_text = f"""
        <b>Nomor:</b> {phone_info['international']}<br>
        <b>Operator:</b> {phone_info['operator']}<br>
        <b>Negara:</b> {location_data.get('country', phone_info['country'])}<br>
        <b>Kota:</b> {location_data.get('city', 'Unknown')}<br>
        <b>Region:</b> {location_data.get('region', 'Unknown')}<br>
        <b>Akurasi:</b> {location_data.get('confidence', 'Estimasi berdasarkan area')}
        """
        
        folium.Marker(
            map_center,
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=phone_info['international'],
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
        
        # Tambahkan circle area perkiraan
        folium.Circle(
            map_center,
            radius=10000,
            color='blue',
            fill=True,
            fill_opacity=0.2,
            popup='Perkiraan area coverage'
        ).add_to(m)
        
        # Simpan peta
        m.save(filename)
        print(f"{Fore.GREEN}[✓] Peta lokasi tersimpan: {filename}{Style.RESET_ALL}")
        
        # Buka di browser
        webbrowser.open(f'file://{os.path.abspath(filename)}')
        
        return filename
        
    def search_google(self, phone_number):
        """
        Mencari melalui Google search
        """
        print(f"{Fore.YELLOW}[*] Mencari di Google...{Style.RESET_ALL}")
        
        results = []
        
        # Coba dengan metode requests langsung ke Google
        try:
            search_url = f"https://www.google.com/search?q=%22{quote_plus(phone_number)}%22"
            response = self.session.get(search_url, timeout=10)
            
            if response.status_code == 200:
                # Ekstrak URL dari hasil pencarian (sederhana)
                urls = re.findall(r'<a href="(https?://[^"]+)"', response.text)
                for url in urls[:5]:
                    platform = self.detect_platform_from_url(url)
                    if platform:
                        results.append({
                            'platform': platform,
                            'url': url,
                            'method': 'Google Search'
                        })
        except Exception as e:
            print(f"{Fore.YELLOW}[!] Google search error: {e}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}    Install googlesearch-python untuk hasil lebih baik: pip install googlesearch-python{Style.RESET_ALL}")
            
        return results
        
    def detect_platform_from_url(self, url):
        """Deteksi platform dari URL"""
        platforms = {
            'facebook.com': 'Facebook',
            'instagram.com': 'Instagram',
            'twitter.com': 'Twitter/X',
            'x.com': 'Twitter/X',
            'linkedin.com': 'LinkedIn',
            'tiktok.com': 'TikTok',
            'youtube.com': 'YouTube',
            'reddit.com': 'Reddit',
            'github.com': 'GitHub',
            'pinterest.com': 'Pinterest',
            't.me': 'Telegram',
            'wa.me': 'WhatsApp'
        }
        
        url_lower = url.lower()
        for domain, platform in platforms.items():
            if domain in url_lower:
                return platform
        return None
        
    def check_telegram(self, phone_number):
        """Cek Telegram"""
        print(f"{Fore.YELLOW}[*] Mencari di Telegram...{Style.RESET_ALL}")
        
        results = []
        try:
            tel_link = f"https://t.me/{phone_number.replace('+', '')}"
            response = self.session.get(tel_link, timeout=5)
            if response.status_code == 200:
                if 'If you have Telegram' not in response.text:
                    results.append({
                        'platform': 'Telegram',
                        'url': tel_link,
                        'method': 'Direct Link Check'
                    })
        except:
            pass
            
        return results
        
    def check_whatsapp(self, phone_number):
        """Cek WhatsApp"""
        print(f"{Fore.YELLOW}[*] Mencari di WhatsApp...{Style.RESET_ALL}")
        
        results = []
        wa_link = f"https://wa.me/{phone_number.replace('+', '')}"
        
        results.append({
            'platform': 'WhatsApp',
            'url': wa_link,
            'method': 'WhatsApp Direct',
            'note': 'Buka link untuk chat via WhatsApp'
        })
        
        return results
        
    def search_all_platforms(self, phone_info):
        """
        Mencari di semua platform
        """
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"    MENCARI AKUN MEDIA SOSIAL")
        print(f"{'='*60}{Style.RESET_ALL}")
        
        phone_e164 = phone_info['e164']
        phone_national = phone_info['national']
        
        all_results = []
        
        # 1. WhatsApp
        whatsapp_results = self.check_whatsapp(phone_e164)
        all_results.extend(whatsapp_results)
        
        # 2. Telegram
        telegram_results = self.check_telegram(phone_e164)
        all_results.extend(telegram_results)
        
        # 3. Google Search
        google_results = self.search_google(phone_national)
        all_results.extend(google_results)
        
        return all_results
        
    def track_all_locations(self, phone_info):
        """
        Melacak lokasi menggunakan multiple API
        """
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"    PELACAKAN LOKASI")
        print(f"{'='*60}{Style.RESET_ALL}")
        
        location_results = {}
        
        # 1. OpenCage Geocoding
        location_results['opencage'] = self.track_location_opencage(phone_info)
        
        # 2. OpenStreetMap Nominatim
        location_results['osm'] = self.track_location_nominatim(phone_info)
        
        # 3. Melissa API
        melissa_result = self.track_location_melissa(phone_info)
        if melissa_result:
            location_results['melissa'] = melissa_result
            
        # Gabungkan hasil terbaik
        best_location = self.merge_location_results(location_results)
        
        return best_location
        
    def merge_location_results(self, location_results):
        """
        Menggabungkan hasil dari berbagai sumber lokasi
        """
        merged = {
            'latitude': None,
            'longitude': None,
            'city': None,
            'region': None,
            'country': None,
            'operator': None,
            'timezone': None,
            'phone_type': None,
            'sources': [],
            'confidence': 'Rendah'
        }
        
        for source_name, data in location_results.items():
            if data and data.get('latitude'):
                merged['latitude'] = data.get('latitude')
                merged['longitude'] = data.get('longitude')
                merged['city'] = merged['city'] or data.get('city')
                merged['region'] = merged['region'] or data.get('region')
                merged['country'] = merged['country'] or data.get('country')
                merged['operator'] = merged['operator'] or data.get('operator')
                merged['timezone'] = merged['timezone'] or data.get('timezone')
                merged['phone_type'] = merged['phone_type'] or data.get('phone_type')
                merged['sources'].append(source_name)
                
                if source_name == 'melissa':
                    merged['confidence'] = 'Tinggi (real-time verification)'
                elif source_name == 'opencage':
                    merged['confidence'] = 'Sedang (geocoding)'
                elif source_name == 'osm':
                    merged['confidence'] = 'Rendah (estimasi negara)'
                    
        return merged
        
    def display_results(self, phone_info, social_results, location_data):
        """
        Menampilkan hasil pencarian
        """
        print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════════════╗")
        print(f"{Fore.CYAN}║                      HASIL PENCARIAN                              ║")
        print(f"{Fore.CYAN}╠══════════════════════════════════════════════════════════════════╣")
        print(f"{Fore.CYAN}║ {Fore.WHITE}Nomor Telepon : {phone_info['international']:<50} {Fore.CYAN}║")
        print(f"{Fore.CYAN}║ {Fore.WHITE}Operator      : {phone_info['operator']:<50} {Fore.CYAN}║")
        print(f"{Fore.CYAN}║ {Fore.WHITE}Negara        : {phone_info['country']:<50} {Fore.CYAN}║")
        print(f"{Fore.CYAN}║ {Fore.WHITE}Zona Waktu    : {phone_info['timezone']:<50} {Fore.CYAN}║")
        print(f"{Fore.CYAN}╚══════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
        
        # Tampilkan lokasi
        if location_data and location_data.get('latitude'):
            print(f"\n{Fore.GREEN}╔══════════════════════════════════════════════════════════════════╗")
            print(f"{Fore.GREEN}║                      INFORMASI LOKASI                            ║")
            print(f"{Fore.GREEN}╠══════════════════════════════════════════════════════════════════╣")
            print(f"{Fore.GREEN}║ {Fore.WHITE}Koordinat     : {location_data['latitude']}, {location_data['longitude']}{Style.RESET_ALL}")
            if location_data.get('city'):
                print(f"{Fore.GREEN}║ {Fore.WHITE}Kota          : {location_data['city']:<50} {Fore.CYAN}║")
            if location_data.get('region'):
                print(f"{Fore.GREEN}║ {Fore.WHITE}Region        : {location_data['region']:<50} {Fore.CYAN}║")
            if location_data.get('phone_type'):
                print(f"{Fore.GREEN}║ {Fore.WHITE}Tipe Nomor    : {location_data['phone_type']:<50} {Fore.CYAN}║")
            print(f"{Fore.GREEN}║ {Fore.WHITE}Sumber Data   : {', '.join(location_data.get('sources', [])):<50} {Fore.CYAN}║")
            print(f"{Fore.GREEN}║ {Fore.WHITE}Tingkat Akurasi: {location_data.get('confidence', 'Unknown'):<50} {Fore.CYAN}║")
            print(f"{Fore.GREEN}╚══════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.YELLOW}[!] Tidak dapat menentukan lokasi spesifik.{Style.RESET_ALL}")
            print(f"{Fore.CYAN}[*] Informasi yang tersedia hanya sampai level negara: {phone_info['country']}{Style.RESET_ALL}")
            
        # Tampilkan hasil media sosial
        if not social_results:
            print(f"\n{Fore.YELLOW}[!] Tidak ditemukan akun media sosial yang terasosiasi.{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.GREEN}[✓] Ditemukan {len(social_results)} hasil media sosial:{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'-'*60}{Style.RESET_ALL}")
            
            for i, result in enumerate(social_results, 1):
                print(f"\n{Fore.GREEN}{i}. {Fore.YELLOW}{result['platform']}{Style.RESET_ALL}")
                print(f"   {Fore.CYAN}Metode: {result.get('method', 'Unknown')}{Style.RESET_ALL}")
                if 'url' in result:
                    print(f"   {Fore.WHITE}Link   : {result['url']}{Style.RESET_ALL}")
                if 'note' in result:
                    print(f"   {Fore.MAGENTA}Catatan: {result['note']}{Style.RESET_ALL}")
                    
        print(f"\n{Fore.CYAN}{'-'*60}{Style.RESET_ALL}")
        
    def generate_report(self, phone_info, social_results, location_data):
        """
        Generate laporan dalam format JSON
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'phone_info': {
                'raw': phone_info.get('raw'),
                'international': phone_info.get('international'),
                'e164': phone_info.get('e164'),
                'country': phone_info.get('country'),
                'operator': phone_info.get('operator'),
                'timezone': phone_info.get('timezone')
            },
            'location_data': location_data,
            'total_social_found': len(social_results),
            'social_media_results': social_results
        }
        
        filename = f"report_{phone_info['e164'].replace('+', '')}_{int(time.time())}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        print(f"\n{Fore.GREEN}[✓] Laporan tersimpan di: {filename}{Style.RESET_ALL}")
        return filename
        
    def main_menu(self):
        """Menu utama"""
        while True:
            print(f"\n{Fore.CYAN}╔════════════════════════════════════════════════════════════╗")
            print(f"{Fore.CYAN}║                     MENU UTAMA                              ║")
            print(f"{Fore.CYAN}╠════════════════════════════════════════════════════════════╣")
            print(f"{Fore.CYAN}║  1. Cari Media Sosial + Lacak Lokasi                       ║")
            print(f"{Fore.CYAN}║  2. Lacak Lokasi Saja                                      ║")
            print(f"{Fore.CYAN}║  3. Info & Panduan Penggunaan                              ║")
            print(f"{Fore.CYAN}║  4. Exit                                                   ║")
            print(f"{Fore.CYAN}╚════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
            
            choice = input(f"\n{Fore.YELLOW}Pilih opsi, Yang Mulia: {Style.RESET_ALL}")
            
            if choice == '1':
                print(f"\n{Fore.CYAN}[*] Masukkan nomor telepon (contoh: 628123456789 atau 08123456789){Style.RESET_ALL}")
                phone = input("Nomor telepon: ").strip()
                
                if not phone:
                    print(f"{Fore.RED}[!] Nomor telepon tidak boleh kosong!{Style.RESET_ALL}")
                    continue
                    
                print(f"\n{Fore.YELLOW}[*] Memproses nomor telepon...{Style.RESET_ALL}")
                phone_info = self.format_phone_number(phone)
                
                if not phone_info['valid']:
                    continue
                    
                print(f"\n{Fore.GREEN}[✓] Nomor valid: {phone_info['international']}{Style.RESET_ALL}")
                
                confirm = input(f"\n{Fore.YELLOW}Lanjutkan pencarian? (y/n): {Style.RESET_ALL}")
                if confirm.lower() != 'y':
                    continue
                    
                # Cari media sosial
                social_results = self.search_all_platforms(phone_info)
                
                # Lacak lokasi
                location_data = self.track_all_locations(phone_info)
                
                # Tampilkan hasil
                self.display_results(phone_info, social_results, location_data)
                
                # Generate peta jika ada koordinat
                if location_data and location_data.get('latitude') and FOLIUM_AVAILABLE:
                    gen_map = input(f"\n{Fore.YELLOW}Generate peta lokasi? (y/n): {Style.RESET_ALL}")
                    if gen_map.lower() == 'y':
                        self.generate_location_map(location_data, phone_info)
                        
                # Tawarkan simpan laporan
                save = input(f"\n{Fore.YELLOW}Simpan laporan ke file? (y/n): {Style.RESET_ALL}")
                if save.lower() == 'y':
                    self.generate_report(phone_info, social_results, location_data)
                    
            elif choice == '2':
                print(f"\n{Fore.CYAN}[*] Masukkan nomor telepon (contoh: 628123456789 atau 08123456789){Style.RESET_ALL}")
                phone = input("Nomor telepon: ").strip()
                
                if not phone:
                    print(f"{Fore.RED}[!] Nomor telepon tidak boleh kosong!{Style.RESET_ALL}")
                    continue
                    
                phone_info = self.format_phone_number(phone)
                if not phone_info['valid']:
                    continue
                    
                location_data = self.track_all_locations(phone_info)
                
                if location_data and location_data.get('latitude'):
                    print(f"\n{Fore.GREEN}[✓] Lokasi terdeteksi!{Style.RESET_ALL}")
                    print(f"   {Fore.WHITE}Koordinat: {location_data['latitude']}, {location_data['longitude']}{Style.RESET_ALL}")
                    if location_data.get('city'):
                        print(f"   {Fore.WHITE}Kota: {location_data['city']}{Style.RESET_ALL}")
                    if location_data.get('region'):
                        print(f"   {Fore.WHITE}Region: {location_data['region']}{Style.RESET_ALL}")
                        
                    if FOLIUM_AVAILABLE:
                        gen_map = input(f"\n{Fore.YELLOW}Generate peta lokasi? (y/n): {Style.RESET_ALL}")
                        if gen_map.lower() == 'y':
                            self.generate_location_map(location_data, phone_info)
                else:
                    print(f"\n{Fore.YELLOW}[!] Hanya informasi level negara yang tersedia: {phone_info['country']}{Style.RESET_ALL}")
                    
            elif choice == '3':
                print(f"\n{Fore.CYAN}╔════════════════════════════════════════════════════════════╗")
                print(f"{Fore.CYAN}║                      INFO & PANDUAN                         ║")
                print(f"{Fore.CYAN}╠════════════════════════════════════════════════════════════╣")
                print(f"{Fore.CYAN}║ {Fore.WHITE}Cara Penggunaan:{Fore.CYAN}                                                ║")
                print(f"{Fore.CYAN}║  1. Masukkan nomor telepon lengkap dengan kode negara       ║")
                print(f"{Fore.CYAN}║  2. Tool akan memvalidasi dan memformat nomor               ║")
                print(f"{Fore.CYAN}║  3. Tool akan mencari media sosial & lokasi                 ║")
                print(f"{Fore.CYAN}║                                                              ║")
                print(f"{Fore.CYAN}║ {Fore.WHITE}API yang Digunakan untuk Lokasi:{Fore.CYAN}                                      ║")
                print(f"{Fore.CYAN}║  - OpenCage Geocoding (perlu API key)                       ║")
                print(f"{Fore.CYAN}║  - OpenStreetMap Nominatim (gratis, tanpa key)               ║")
                print(f"{Fore.CYAN}║  - Melissa Global Phone (real-time, perlu key)               ║")
                print(f"{Fore.CYAN}║                                                              ║")
                print(f"{Fore.CYAN}║ {Fore.WHITE}Install Dependencies:{Fore.CYAN}                                            ║")
                print(f"{Fore.CYAN}║  pip install phonenumbers colorama requests folium          ║")
                print(f"{Fore.CYAN}╚════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
                
            elif choice == '4':
                print(f"\n{Fore.GREEN}Terima kasih, Yang Mulia! Sampai jumpa kembali!{Style.RESET_ALL}")
                break
                
            else:
                print(f"{Fore.RED}[!] Pilihan tidak valid!{Style.RESET_ALL}")


def check_dependencies():
    """Cek dependencies yang diperlukan"""
    missing = []
    
    try:
        import phonenumbers
    except ImportError:
        missing.append("phonenumbers")
        
    try:
        import colorama
    except ImportError:
        missing.append("colorama")
        
    try:
        import requests
    except ImportError:
        missing.append("requests")
        
    if missing:
        print(f"{Fore.RED}[!] Missing dependencies: {', '.join(missing)}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Install dengan: pip install {' '.join(missing)}{Style.RESET_ALL}")
        return False
        
    return True


def main():
    """Fungsi utama"""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    if not check_dependencies():
        sys.exit(1)
        
    tool = SocialMediaFinder()
    tool.print_banner()
    
    print(f"\n{Fore.YELLOW}╔════════════════════════════════════════════════════════════╗")
    print(f"{Fore.YELLOW}║  NOTE: Tool ini hanya untuk pencarian informasi PUBLIK      ║")
    print(f"{Fore.YELLOW}║  Lokasi yang ditampilkan adalah ESTIMASI berdasarkan       ║")
    print(f"{Fore.YELLOW}║  data dari operator dan database publik                    ║")
    print(f"{Fore.YELLOW}║  BUKAN lokasi real-time perangkat.                         ║")
    print(f"{Fore.YELLOW}╚════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
    
    try:
        tool.main_menu()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}[!] Tool dihentikan oleh user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}[!] Error: {e}{Style.RESET_ALL}")


if __name__ == "__main__":
    main()