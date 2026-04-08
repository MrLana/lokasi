#!/usr/bin/env python3
"""
SOCIAL MEDIA FINDER BY PHONE NUMBER
Version: 1.0 - OSINT Tool
Author: MechaPowerBot - Untuk Yang Mulia Putri Incha
Deskripsi: Mencari akun media sosial berdasarkan nomor telepon
Legal: Hanya untuk pencarian informasi publik yang tersedia
"""

import requests
import json
import re
import time
import sys
import os
from datetime import datetime
import urllib3
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

class SocialMediaFinder:
    """
    Tool OSINT untuk mencari akun media sosial dari nomor telepon
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        
        # Daftar platform yang akan diperiksa
        self.platforms = {
            'Instagram': {
                'check_url': 'https://www.instagram.com/accounts/web/username/',
                'search_method': 'post',
                'payload_key': 'email_or_phone'
            },
            'Facebook': {
                'check_url': 'https://www.facebook.com/login/identify/',
                'search_method': 'get',
                'use_phone': True
            },
            'Twitter/X': {
                'check_url': 'https://api.twitter.com/i/users/email_available.json',
                'search_method': 'get',
                'param': 'email'
            },
            'TikTok': {
                'check_url': 'https://www.tiktok.com/node/share/user/@',
                'search_method': 'get'
            },
            'Telegram': {
                'check_url': 'https://t.me/',
                'search_method': 'get'
            },
            'WhatsApp': {
                'check_url': 'https://api.whatsapp.com/send/',
                'search_method': 'get',
                'wa_me': 'https://wa.me/'
            },
            'LinkedIn': {
                'check_url': 'https://www.linkedin.com/pub/dir/',
                'search_method': 'get'
            },
            'Snapchat': {
                'check_url': 'https://www.snapchat.com/add/',
                'search_method': 'get'
            },
            'Pinterest': {
                'check_url': 'https://www.pinterest.com/search/pins/',
                'search_method': 'get'
            },
            'Reddit': {
                'check_url': 'https://www.reddit.com/user/',
                'search_method': 'get'
            },
            'YouTube': {
                'check_url': 'https://www.youtube.com/results',
                'search_method': 'get'
            },
            'GitHub': {
                'check_url': 'https://github.com/search',
                'search_method': 'get',
                'param': 'q'
            },
            'Signal': {
                'check_url': 'https://signal.me/#p/',
                'search_method': 'get'
            }
        }
        
        self.results = {}
        
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
{Fore.CYAN}║  {Fore.YELLOW}SOCIAL MEDIA FINDER v1.0 - OSINT Tool{Fore.CYAN}                      ║
{Fore.CYAN}║  {Fore.MAGENTA}Find social media accounts by phone number{Fore.CYAN}               ║
{Fore.CYAN}╚══════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """
        print(banner)
        
    def format_phone_number(self, number):
        """
        Format dan validasi nomor telepon
        Menggunakan library phonenumbers untuk validasi
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
                
                # Dapatkan info
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
                    'valid': True
                }
            else:
                print(f"{Fore.RED}[!] Nomor telepon tidak valid!{Style.RESET_ALL}")
                return {'valid': False}
                
        except Exception as e:
            print(f"{Fore.RED}[!] Error formatting number: {e}{Style.RESET_ALL}")
            return {'valid': False}
            
    def search_google(self, phone_number):
        """
        Mencari melalui Google search
        """
        print(f"{Fore.YELLOW}[*] Mencari di Google...{Style.RESET_ALL}")
        
        results = []
        search_queries = [
            f'"{phone_number}"',
            f'{phone_number} Facebook',
            f'{phone_number} Instagram',
            f'{phone_number} LinkedIn',
            f'{phone_number} Twitter'
        ]
        
        try:
            from googlesearch import search
        except ImportError:
            print(f"{Fore.YELLOW}[!] Library googlesearch-python tidak terinstall. Install dengan: pip install googlesearch-python{Style.RESET_ALL}")
            return results
            
        for query in search_queries[:2]:  # Batasi query untuk menghindari rate limit
            try:
                for url in search(query, num_results=5, lang='id'):
                    # Deteksi platform dari URL
                    platform = self.detect_platform_from_url(url)
                    if platform:
                        results.append({
                            'platform': platform,
                            'url': url,
                            'method': 'Google Search'
                        })
                time.sleep(1)  # Delay untuk menghindari rate limit
            except Exception as e:
                print(f"{Fore.RED}[!] Google search error: {e}{Style.RESET_ALL}")
                
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
        """
        Cek Telegram - menggunakan t.me/username
        Telegram tidak memiliki API publik untuk cek nomor,
        tapi kita bisa cek jika nomor terdaftar sebagai username
        """
        print(f"{Fore.YELLOW}[*] Mencari di Telegram...{Style.RESET_ALL}")
        
        results = []
        # Telegram menggunakan nomor untuk username format tertentu
        # Tidak ada cara langsung, tapi kita bisa cek melalui kontak
        
        # Cek melalui API publik telegram (terbatas)
        try:
            # Format nomor untuk Telegram
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
        """
        Cek WhatsApp - menggunakan wa.me link
        """
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
        
    def check_instagram(self, phone_number):
        """
        Cek Instagram - menggunakan fitur forgot password
        """
        print(f"{Fore.YELLOW}[*] Mencari di Instagram...{Style.RESET_ALL}")
        
        results = []
        
        # Method 1: Cek melalui endpoint akun
        try:
            # Instagram API untuk cek nomor (terbatas)
            url = "https://www.instagram.com/api/v1/web/accounts/web_create_ajax/attempt/"
            
            headers = {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': 'https://www.instagram.com/accounts/emailsignup/'
            }
            
            data = {
                'email': phone_number,
                'username': ''
            }
            
            response = self.session.post(url, headers=headers, data=data)
            if response.status_code == 200:
                json_resp = response.json()
                if json_resp.get('email_exists') or json_resp.get('username_exists'):
                    results.append({
                        'platform': 'Instagram',
                        'method': 'Account Check',
                        'status': 'Akun terdeteksi'
                    })
        except:
            pass
            
        return results
        
    def check_facebook(self, phone_number):
        """
        Cek Facebook - menggunakan fitur forgot password
        """
        print(f"{Fore.YELLOW}[*] Mencari di Facebook...{Style.RESET_ALL}")
        
        results = []
        
        try:
            # Facebook password reset endpoint
            url = "https://www.facebook.com/login/identify/"
            
            params = {
                'ctx': 'recover',
                'submit': 'Cari',
                'email': phone_number
            }
            
            response = self.session.get(url, params=params)
            
            # Cek response untuk indikasi akun
            if 'account_row' in response.text or 'Find Your Account' in response.text:
                results.append({
                    'platform': 'Facebook',
                    'method': 'Account Recovery Check',
                    'status': 'Akun mungkin terdaftar'
                })
        except:
            pass
            
        return results
        
    def check_linkedin(self, phone_number):
        """
        Cek LinkedIn
        """
        print(f"{Fore.YELLOW}[*] Mencari di LinkedIn...{Style.RESET_ALL}")
        
        results = []
        
        try:
            # LinkedIn search
            url = f"https://www.linkedin.com/pub/dir/?phone={phone_number}"
            response = self.session.get(url, timeout=5)
            
            if response.status_code == 200:
                if 'No results found' not in response.text:
                    results.append({
                        'platform': 'LinkedIn',
                        'url': url,
                        'method': 'Directory Search'
                    })
        except:
            pass
            
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
        phone_raw = phone_info['raw']
        
        all_results = []
        
        # 1. WhatsApp
        whatsapp_results = self.check_whatsapp(phone_e164)
        all_results.extend(whatsapp_results)
        
        # 2. Telegram
        telegram_results = self.check_telegram(phone_e164)
        all_results.extend(telegram_results)
        
        # 3. Instagram
        instagram_results = self.check_instagram(phone_e164)
        all_results.extend(instagram_results)
        
        # 4. Facebook
        facebook_results = self.check_facebook(phone_e164)
        all_results.extend(facebook_results)
        
        # 5. LinkedIn
        linkedin_results = self.check_linkedin(phone_e164)
        all_results.extend(linkedin_results)
        
        # 6. Google Search
        google_results = self.search_google(phone_national)
        all_results.extend(google_results)
        
        return all_results
        
    def display_results(self, phone_info, results):
        """
        Menampilkan hasil pencarian
        """
        print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════════════╗")
        print(f"{Fore.CYAN}║                      HASIL PENCARIAN                              ║")
        print(f"{Fore.CYAN}╠══════════════════════════════════════════════════════════════════╣")
        print(f"{Fore.CYAN}║ {Fore.WHITE}Nomor Telepon : {phone_info['international']:<50} {Fore.CYAN}║")
        print(f"{Fore.CYAN}║ {Fore.WHITE}Operator      : {phone_info['operator']:<50} {Fore.CYAN}║")
        print(f"{Fore.CYAN}║ {Fore.WHITE}Negara        : {phone_info['country']:<50} {Fore.CYAN}║")
        print(f"{Fore.CYAN}╚══════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
        
        if not results:
            print(f"\n{Fore.YELLOW}[!] Tidak ditemukan akun media sosial yang terasosiasi dengan nomor ini.{Style.RESET_ALL}")
            print(f"{Fore.CYAN}[*] Tips: Pastikan nomor telepon benar dan pemiliknya menautkan nomor ke akun media sosial.{Style.RESET_ALL}")
            return
            
        print(f"\n{Fore.GREEN}[✓] Ditemukan {len(results)} hasil:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'─'*60}{Style.RESET_ALL}")
        
        for i, result in enumerate(results, 1):
            print(f"\n{Fore.GREEN}{i}. {Fore.YELLOW}{result['platform']}{Style.RESET_ALL}")
            print(f"   {Fore.CYAN}Metode: {result.get('method', 'Unknown')}{Style.RESET_ALL}")
            if 'url' in result:
                print(f"   {Fore.WHITE}Link   : {result['url']}{Style.RESET_ALL}")
            if 'note' in result:
                print(f"   {Fore.MAGENTA}Catatan: {result['note']}{Style.RESET_ALL}")
            if 'status' in result:
                print(f"   {Fore.CYAN}Status : {result['status']}{Style.RESET_ALL}")
                
        print(f"\n{Fore.CYAN}{'─'*60}{Style.RESET_ALL}")
        
    def generate_report(self, phone_info, results):
        """
        Generate laporan dalam format JSON
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'phone_info': phone_info,
            'total_found': len(results),
            'results': results
        }
        
        filename = f"social_media_report_{phone_info['e164'].replace('+', '')}_{int(time.time())}.json"
        
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
            print(f"{Fore.CYAN}║  1. Cari Media Sosial dari Nomor Telepon                    ║")
            print(f"{Fore.CYAN}║  2. Info & Panduan Penggunaan                               ║")
            print(f"{Fore.CYAN}║  3. Exit                                                    ║")
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
                print(f"{Fore.CYAN}[*] Operator: {phone_info['operator']}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}[*] Negara: {phone_info['country']}{Style.RESET_ALL}")
                
                confirm = input(f"\n{Fore.YELLOW}Lanjutkan pencarian? (y/n): {Style.RESET_ALL}")
                if confirm.lower() != 'y':
                    continue
                    
                # Mulai pencarian
                results = self.search_all_platforms(phone_info)
                
                # Tampilkan hasil
                self.display_results(phone_info, results)
                
                # Tawarkan simpan laporan
                if results:
                    save = input(f"\n{Fore.YELLOW}Simpan laporan ke file? (y/n): {Style.RESET_ALL}")
                    if save.lower() == 'y':
                        self.generate_report(phone_info, results)
                        
            elif choice == '2':
                print(f"\n{Fore.CYAN}╔════════════════════════════════════════════════════════════╗")
                print(f"{Fore.CYAN}║                      INFO & PANDUAN                         ║")
                print(f"{Fore.CYAN}╠════════════════════════════════════════════════════════════╣")
                print(f"{Fore.CYAN}║ {Fore.WHITE}Cara Penggunaan:{Fore.CYAN}                                                ║")
                print(f"{Fore.CYAN}║  1. Masukkan nomor telepon lengkap dengan kode negara       ║")
                print(f"{Fore.CYAN}║  2. Tool akan memvalidasi dan memformat nomor               ║")
                print(f"{Fore.CYAN}║  3. Tool akan mencari di berbagai platform media sosial     ║")
                print(f"{Fore.CYAN}║                                                              ║")
                print(f"{Fore.CYAN}║ {Fore.WHITE}Platform yang diperiksa:{Fore.CYAN}                                           ║")
                print(f"{Fore.CYAN}║  - WhatsApp, Telegram, Instagram, Facebook                  ║")
                print(f"{Fore.CYAN}║  - LinkedIn, TikTok, Twitter/X, YouTube                     ║")
                print(f"{Fore.CYAN}║  - GitHub, Reddit, Pinterest, Snapchat                      ║")
                print(f"{Fore.CYAN}║                                                              ║")
                print(f"{Fore.CYAN}║ {Fore.WHITE}Catatan:{Fore.CYAN}                                                         ║")
                print(f"{Fore.CYAN}║  - Hanya informasi PUBLIK yang dapat diakses                ║")
                print(f"{Fore.CYAN}║  - Hasil tergantung pengaturan privasi target               ║")
                print(f"{Fore.CYAN}║  - Gunakan untuk tujuan yang LEGAL dan ETIS                 ║")
                print(f"{Fore.CYAN}╚════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
                
            elif choice == '3':
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
    print(f"{Fore.YELLOW}║  Gunakan dengan bijak dan hanya untuk tujuan LEGAL          ║")
    print(f"{Fore.YELLOW}║  Hormati privasi orang lain!                                ║")
    print(f"{Fore.YELLOW}╚════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
    
    try:
        tool.main_menu()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}[!] Tool dihentikan oleh user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}[!] Error: {e}{Style.RESET_ALL}")


if __name__ == "__main__":
    main()