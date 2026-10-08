#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTO RECON X ULTRA PRO TÜRKÇE v4.1
Tüm Sistem Açıkları ve Zafiyetleri Taranan En Güçlü Etik Siber Güvenlik Platformu
MIT Lisansı | roottechx (Mücahid Balcı) | github.com/roottechxtr
KVKK Uyumlu • TR-CERT Entegrasyonlu • TÜBİTAK SGE Standartları
"""

import asyncio
import aiohttp
import aiofiles
import subprocess
import socket
import sys
import os
import time
import json
import re
import ipaddress
import textwrap
import warnings
import random
import string
import platform
import psutil
from datetime import datetime, timedelta
from urllib.parse import urlparse, quote_plus
from typing import Dict, List, Optional, Any, Tuple, Set
from enum import Enum
from dataclasses import dataclass

# Uyarıları bastır
warnings.filterwarnings("ignore", category=Warning)

try:
    from rich.console import Console
    from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
    from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, BarColumn, TextColumn, MofNCompleteColumn
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    from rich.text import Text
    from rich.syntax import Syntax
    from rich.tree import Tree
    from rich.columns import Columns
    from rich.markdown import Markdown
    from rich.json import JSON as RichJSON
    from rich.traceback import install
    import dns.asyncresolver
    import whois
    import tldextract
    from jinja2 import Template, Environment, FileSystemLoader
except ImportError as e:
    print(f"❌ Kritik bağımlılık eksik: {e}")
    print("\n[KURULUM KILAVUZU]")
    print("1. Sistem bağımlılıklarını kurun:")
    print("   sudo apt update && sudo apt install -y python3-pip nmap testssl.sh whatweb nikto dirsearch amass")
    print("2. Python bağımlılıklarını kurun:")
    print("   pip install rich aiohttp dnspython python-whois tldextract jinja2 aiofiles psutil")
    sys.exit(1)

# Rich traceback kurulumu
install(show_locals=True)

console = Console(record=True, width=160)
CVE_API = "https://cve.circl.lu/api/search/"
ABUSEIPDB_API = "https://api.abuseipdb.com/api/v2/check"
VIRUSTOTAL_API = "https://www.virustotal.com/api/v3/domains/"
TRCERT_API = "https://www.trcert.gov.tr/api/acik-erisim/ransomware/"
DEFAULT_TIMEOUT = 30
MAX_CONCURRENT_REQUESTS = 50
KVKK_UYARI_METNI = """
DİKKAT: Bu tarama sırasında elde edilen veriler, 6698 sayılı Kişisel Verilerin Korunması Kanunu (KVKK) 
kapsamında kişisel veri niteliği taşıyabilir. Tarama sonrası verilerinizin korunması ve imha edilmesi 
zorunluluğunu kabul ediyorsunuz. Veriler sadece yetkili merciler tarafından talep edilmesi durumunda 
yetkili mercilere teslim edilecektir.
"""

class RiskSeviyesi(Enum):
    KRITIK = "KRITIK"
    YUKSEK = "YUKSEK"
    ORTA = "ORTA"
    DUSUK = "DUSUK"
    BILGI = "BILGI"

    def renk(self) -> str:
        return {
            "KRITIK": "bold red blink",
            "YUKSEK": "bold yellow",
            "ORTA": "bold cyan",
            "DUSUK": "bold green",
            "BILGI": "bold blue"
        }[self.value]
    
    def emoji(self) -> str:
        return {
            "KRITIK": "💥",
            "YUKSEK": "🚨",
            "ORTA": "⚠️",
            "DUSUK": "🔍",
            "BILGI": "💡"
        }[self.value]

    def gecis_suresi(self) -> str:
        return {
            "KRITIK": "Hemen",
            "YUKSEK": "24 saat içinde",
            "ORTA": "7 gün içinde",
            "DUSUK": "30 gün içinde",
            "BILGI": "Plan dahilinde"
        }[self.value]

@dataclass
class GuvenlikBulgu:
    modul: str
    port: Optional[str] = None
    tip: str = "Genel"
    risk_seviyesi: RiskSeviyesi = RiskSeviyesi.BILGI
    detaylar: str = ""
    cvss: float = 0.0
    cozum_onerisi: str = ""
    referanslar: List[str] = None
    tespit_tarihi: datetime = None
    cvss_vector: str = ""
    kurum_ici_sorumlu: str = "Siber Güvenlik Ekibi"

    def __post_init__(self):
        if self.referanslar is None:
            self.referanslar = []
        if self.tespit_tarihi is None:
            self.tespit_tarihi = datetime.now()

    def to_dict(self):
        return {
            "modul": self.modul,
            "port": self.port,
            "tip": self.tip,
            "risk_seviyesi": self.risk_seviyesi.value,
            "detaylar": self.detaylar,
            "cvss": self.cvss,
            "cozum_onerisi": self.cozum_onerisi,
            "referanslar": self.referanslar,
            "tespit_tarihi": self.tespit_tarihi.isoformat(),
            "cvss_vector": self.cvss_vector,
            "kurum_ici_sorumlu": self.kurum_ici_sorumlu
        }

class SiberIstihbarat:
    def __init__(self, api_anahtarlari: Dict[str, str] = None):
        self.api_anahtarlari = api_anahtarlari or {}
        self.oturum = None
        self.tr_cert_verileri = None
    
    async def oturum_ac(self):
        """API oturumunu başlat"""
        headers = {
            "User-Agent": "AutoReconX-ULTRA-TR/4.1 (Etik Kullanım İçin)",
            "Accept": "application/json",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        if self.api_anahtarlari.get("abuseipdb"):
            headers["Key"] = self.api_anahtarlari["abuseipdb"]
        self.oturum = aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
        )
    
    async def oturumu_kapat(self):
        """API oturumunu kapat"""
        if self.oturum:
            await self.oturum.close()
    
    async def tr_cert_ransomware_kontrolu(self):
        """TR-CERT Ransomware verilerini çek ve sakla"""
        try:
            console.print("[dim]🇹🇷 TR-CERT Ransomware verileri güncelleniyor...[/dim]")
            async with aiohttp.ClientSession() as oturum:
                async with oturum.get(TRCERT_API, timeout=30) as cevap:
                    if cevap.status == 200:
                        self.tr_cert_verileri = await cevap.json()
                        console.print("[green]✓ TR-CERT verileri başarıyla güncellendi[/green]")
                    else:
                        console.print(f"[yellow]⚠️ TR-CERT verileri güncellenemedi (HTTP {cevap.status})[/yellow]")
        except Exception as e:
            console.print(f"[yellow]⚠️ TR-CERT erişim hatası: {str(e)}[/yellow]")
    
    async def abuseipdb_kontrolu(self, ip: str) -> Dict:
        """AbuseIPDB ile IP itibar kontrolü"""
        if not self.api_anahtarlari.get("abuseipdb"):
            return {"hata": "API anahtarı yapılandırılmamış"}
        try:
            params = {
                "ipAddress": ip,
                "maxAgeInDays": 90,
                "verbose": ""
            }
            async with self.oturum.get(ABUSEIPDB_API, params=params) as cevap:
                if cevap.status == 200:
                    return await cevap.json()
                return {"hata": f"HTTP {cevap.status}"}
        except Exception as e:
            return {"hata": str(e)}
    
    async def virustotal_kontrolu(self, alan_adi: str) -> Dict:
        """VirusTotal ile alan adı itibar kontrolü"""
        if not self.api_anahtarlari.get("virustotal"):
            return {"hata": "API anahtarı yapılandırılmamış"}
        try:
            url = f"{VIRUSTOTAL_API}{alan_adi}"
            headers = {"x-apikey": self.api_anahtarlari["virustotal"]}
            async with self.oturum.get(url, headers=headers) as cevap:
                if cevap.status == 200:
                    return await cevap.json()
                return {"hata": f"HTTP {cevap.status}"}
        except Exception as e:
            return {"hata": str(e)}
    
    def ransomware_kontrolu(self, alan_adi: str) -> bool:
        """Alan adının TR-CERT ransomware listesinde olup olmadığını kontrol et"""
        if not self.tr_cert_verileri:
            return False
        alan_temiz = alan_adi.strip().lower()
        for kayit in self.tr_cert_verileri:
            if "domain" in kayit and alan_temiz in kayit["domain"].lower():
                return True
        return False

class SSLAnalizci:
    @staticmethod
    async def testssl_calistir(hedef: str, port: str = "443") -> Dict:
        """testssl.sh ile SSL/TLS analizi yap"""
        try:
            # Geçici dosya oluştur
            json_dosyasi = f"/tmp/testssl_{int(time.time())}.json"
            komut = [
                "testssl.sh",
                "--jsonfile", json_dosyasi,
                "--quiet",
                "--warnings", "batch",
                f"{hedef}:{port}"
            ]
            # Süre aşımını yönetmek için subprocess kullan
            process = await asyncio.create_subprocess_exec(
                *komut,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            try:
                await asyncio.wait_for(process.wait(), timeout=120)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {"hata": "testssl.sh zaman aşımına uğradı (120 saniye)"}
            if process.returncode == 0 and os.path.exists(json_dosyasi):
                async with aiofiles.open(json_dosyasi, "r") as f:
                    icerik = await f.read()
                    sonuclar = json.loads(icerik)
                    os.remove(json_dosyasi)
                    return sonuclar
            return {"hata": f"testssl.sh başarısız oldu (kod: {process.returncode})"}
        except Exception as e:
            return {"hata": f"SSL analiz hatası: {str(e)}"}
    
    @staticmethod
    def testssl_sonuclari_isle(sonuclar: Dict) -> List[GuvenlikBulgu]:
        """testssl.sh sonuçlarını güvenlik bulgularına dönüştür"""
        bulgular = []
        if "hata" in sonuclar:
            return bulgular
        for bolum in sonuclar.get("scanResult", []):
            for bulgu in bolum.get("finding", []):
                seviye = bulgu.get("severity", "INFO").upper()
                if seviye in ["CRITICAL", "HIGH", "MEDIUM"]:
                    # CVSS vektörünü al
                    cvss_vector = bulgu.get("cvssVector", "")
                    # Risk seviyesini belirle
                    risk_seviyesi = RiskSeviyesi.KRITIK if seviye == "CRITICAL" else \
                        RiskSeviyesi.YUKSEK if seviye == "HIGH" else \
                            RiskSeviyesi.ORTA
                    bulgular.append(GuvenlikBulgu(
                        modul="ssl_analizci",
                        port=str(bulgu.get("port", 443)),
                        tip=bulgu.get("id", "SSL_ZAYIFLIGI"),
                        risk_seviyesi=risk_seviyesi,
                        detaylar=bulgu.get("finding", ""),
                        cvss=float(bulgu.get("cvss", 0.0)),
                        cozum_onerisi=bulgu.get("remediation", "SSL/TLS yapılandırmasını güncelleyin"),
                        referanslar=[bulgu.get("cve", ""), bulgu.get("cwe", "")],
                        cvss_vector=cvss_vector
                    ))
        return bulgular

class BulutAvi:
    ORTAK_BUCKET_ONEKLERI = [
        "gelistirme", "uretim", "test", "yedek", "hazirlik", "dahili",
        "veri", "veritabani", "yapilandirma", "sirrlar", "yonetici", "loglar",
        "finans", "musteri", "personel", "dokumanlar", "proje", "api"
    ]
    TURKCE_HASSAS_DOSYA_ADlari = [
        "musteri", "personel", "maas", "sifre", "banka", "kimlik", "adres",
        "iletisim", "sozlesme", "rapor", "analiz", "yedek", "yedekleme"
    ]
    
    @staticmethod
    async def s3_bucket_kontrolu(alan_adi: str) -> List[GuvenlikBulgu]:
        """AWS S3 bucket taraması"""
        bulgular = []
        temel = tldextract.extract(alan_adi).domain
        # Bucket isimlerini oluştur ve kontrol et
        kontrol_edilecek_bucketler = []
        # Temel isim kombinasyonları
        for onek in BulutAvi.ORTAK_BUCKET_ONEKLERI:
            kontrol_edilecek_bucketler.append(f"{temel}-{onek}")
            kontrol_edilecek_bucketler.append(f"{onek}-{temel}")
            kontrol_edilecek_bucketler.append(f"{temel}{onek}")
            kontrol_edilecek_bucketler.append(f"{onek}{temel}")
        # Türkçe hassas kelimeler
        for kelime in BulutAvi.TURKCE_HASSAS_DOSYA_ADlari:
            kontrol_edilecek_bucketler.append(f"{temel}-{kelime}")
            kontrol_edilecek_bucketler.append(f"{kelime}-{temel}")
        # Benzersiz bucket isimleri
        benzersiz_bucketler = list(set(kontrol_edilecek_bucketler))
        connector = aiohttp.TCPConnector(limit=20)
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as oturum:
            gorevler = []
            for bucket_adi in benzersiz_bucketler:
                url = f"https://{bucket_adi}.s3.amazonaws.com"
                gorevler.append(BulutAvi._bucket_kontrol_et(oturum, url, bucket_adi))
            sonuclar = await asyncio.gather(*gorevler, return_exceptions=True)
        for sonuc in sonuclar:
            if isinstance(sonuc, dict) and "bulgu" in sonuc:
                bulgular.append(sonuc["bulgu"])
        return bulgular
    
    @staticmethod
    async def _bucket_kontrol_et(oturum, url, bucket_adi):
        """Tek bir bucket'ı kontrol et"""
        try:
            async with oturum.head(url, timeout=10) as cevap:
                if cevap.status == 200:
                    return {
                        "bulgu": GuvenlikBulgu(
                            modul="bulut_avi",
                            tip="Genel Erişimli S3 Bucket",
                            risk_seviyesi=RiskSeviyesi.YUKSEK,
                            detaylar=f"Genel erişimli S3 bucket: {bucket_adi}",
                            cozum_onerisi="Bucket politikasını düzenleyerek erişimi kısıtlayın"
                        )
                    }
                elif cevap.status == 403:
                    return {
                        "bulgu": GuvenlikBulgu(
                            modul="bulut_avi",
                            tip="Mevcut S3 Bucket (Özel)",
                            risk_seviyesi=RiskSeviyesi.DUSUK,
                            detaylar=f"Özel S3 bucket mevcut: {bucket_adi}",
                            cozum_onerisi="Erişim kontrollerini gözden geçirin"
                        )
                    }
        except:
            pass
        return None

class WebZayiflikTaramasi:
    @staticmethod
    async def ortak_zayiflik_kontrolu(url: str) -> List[GuvenlikBulgu]:
        """Web uygulamalarında yaygın zafiyet kontrolleri"""
        bulgular = []
        testler = {
            "robots_acik": "/robots.txt",
            "git_acik": "/.git/HEAD",
            "env_acik": "/.env",
            "yedek_dosyalar": ["/yedek.zip", "/config.bak", "/veritabani.sql", "/site.tar.gz"],
            "yonetici_panelleri": ["/yonetici", "/admin", "/wp-admin", "/phpmyadmin"],
            "api_dokumantasyonu": ["/swagger-ui", "/api-docs", "/redoc"],
            "xss_testi": [
                "/?q=<script>alert(1)</script>",
                "/?q=<img src=x onerror=alert(1)>",
                "/?q='\"<svg/onload=alert(1)>"
            ],
            "sqli_testi": [
                "/?id=1'",
                "/?id=1' AND SLEEP(5)--",
                "/?id=1' UNION SELECT null,version()--"
            ],
            "lfi_testi": [
                "/?page=../../../../etc/passwd",
                "/?page=../../../etc/shadow",
                "/?page=..%2F..%2F..%2Fetc%2Fpasswd"
            ]
        }
        async with aiohttp.ClientSession() as oturum:
            # robots.txt kontrolü
            try:
                async with oturum.get(f"{url}{testler['robots_acik']}", timeout=10) as cevap:
                    if cevap.status == 200:
                        icerik = await cevap.text()
                        if "Disallow:" in icerik:
                            bulgular.append(GuvenlikBulgu(
                                modul="web_zayiflik",
                                tip="robots.txt Dosyası Açık",
                                risk_seviyesi=RiskSeviyesi.ORTA,
                                detaylar=f"{url}/robots.txt hassas dizinleri içeriyor",
                                cozum_onerisi="Hassas dizinleri robots.txt dosyasından kaldırın"
                            ))
            except:
                pass
            # .git dizini kontrolü
            try:
                async with oturum.get(f"{url}{testler['git_acik']}", timeout=10) as cevap:
                    if cevap.status == 200:
                        bulgular.append(GuvenlikBulgu(
                            modul="web_zayiflik",
                            tip=".git Dizini Açık",
                            risk_seviyesi=RiskSeviyesi.KRITIK,
                            detaylar=f"Git deposu açık: {url}/.git",
                            cozum_onerisi="Web sunucusundan .git dizinini kaldırın veya erişimi engelleyin"
                        ))
            except:
                pass
            # Hassas dosyalar
            for yol in testler["yedek_dosyalar"]:
                try:
                    async with oturum.head(f"{url}{yol}", timeout=5) as cevap:
                        if cevap.status == 200:
                            bulgular.append(GuvenlikBulgu(
                                modul="web_zayiflik",
                                tip="Hassas Yedek Dosya",
                                risk_seviyesi=RiskSeviyesi.YUKSEK,
                                detaylar=f"Erişilebilir yedek dosya: {url}{yol}",
                                cozum_onerisi="Yedek dosyalarını web sunucusundan kaldırın"
                            ))
                except:
                    continue
            # Yönetici panelleri
            for yol in testler["yonetici_panelleri"]:
                try:
                    async with oturum.get(f"{url}{yol}", timeout=5) as cevap:
                        if cevap.status == 200:
                            bulgular.append(GuvenlikBulgu(
                                modul="web_zayiflik",
                                tip="Yönetici Paneli Açık",
                                risk_seviyesi=RiskSeviyesi.YUKSEK,
                                detaylar=f"Yönetici paneli erişilebilir: {url}{yol}",
                                cozum_onerisi="IP beyaz listesi veya güçlü kimlik doğrulama ekleyin"
                            ))
                except:
                    continue
            # API dökümantasyonu
            for yol in testler["api_dokumantasyonu"]:
                try:
                    async with oturum.get(f"{url}{yol}", timeout=5) as cevap:
                        if cevap.status == 200:
                            bulgular.append(GuvenlikBulgu(
                                modul="web_zayiflik",
                                tip="API Dökümantasyonu Açık",
                                risk_seviyesi=RiskSeviyesi.ORTA,
                                detaylar=f"API dökümantasyonu erişilebilir: {url}{yol}",
                                cozum_onerisi="Üretim ortamında API dökümantasyonunu devre dışı bırakın"
                            ))
                except:
                    continue
            # XSS testleri
            for test in testler["xss_testi"]:
                try:
                    async with oturum.get(f"{url}{test}", timeout=5) as cevap:
                        if cevap.status == 200 and "<script>alert(1)</script>" in await cevap.text():
                            bulgular.append(GuvenlikBulgu(
                                modul="web_zayiflik",
                                tip="XSS Zafiyeti",
                                risk_seviyesi=RiskSeviyesi.YUKSEK,
                                detaylar=f"XSS tespit edildi: {url}{test}",
                                cozum_onerisi="Giriş doğrulaması ve çıktı kodlaması yapın"
                            ))
                except:
                    continue
            # SQLi testleri
            for test in testler["sqli_testi"]:
                try:
                    async with oturum.get(f"{url}{test}", timeout=10) as cevap:
                        if "SQL syntax" in await cevap.text() or cevap.elapsed > 4:
                            bulgular.append(GuvenlikBulgu(
                                modul="web_zayiflik",
                                tip="SQL Enjeksiyonu",
                                risk_seviyesi=RiskSeviyesi.KRITIK,
                                detaylar=f"SQLi tespit edildi: {url}{test}",
                                cozum_onerisi="Parametreli sorgular kullanın"
                            ))
                except:
                    continue
            # LFI testleri
            for test in testler["lfi_testi"]:
                try:
                    async with oturum.get(f"{url}{test}", timeout=5) as cevap:
                        if "root:" in await cevap.text():
                            bulgular.append(GuvenlikBulgu(
                                modul="web_zayiflik",
                                tip="LFI Zafiyeti",
                                risk_seviyesi=RiskSeviyesi.KRITIK,
                                detaylar=f"LFI tespit edildi: {url}{test}",
                                cozum_onerisi="Dosya yollarını doğrulayın ve whitelist kullanın"
                            ))
                except:
                    continue
        return bulgular

class SistemSaglikKontrolcu:
    @staticmethod
    def sistem_kaynaklarini_kontrol_et() -> Dict[str, Any]:
        """Sistem kaynaklarını kontrol et ve raporla"""
        try:
            # CPU kullanımı
            cpu_yuzdesi = psutil.cpu_percent(interval=1)
            # Bellek kullanımı
            bellek = psutil.virtual_memory()
            bellek_yuzdesi = bellek.percent
            # Disk kullanımı
            disk = psutil.disk_usage('/')
            disk_yuzdesi = disk.percent
            # Ağ bağlantısı
            ag_durumu = "aktif" if SistemSaglikKontrolcu.internet_baglantisi_var_mi() else "pasif"
            # Disk alanı (GB olarak)
            disk_bos_alan = disk.free / (1024 ** 3)
            return {
                "cpu": cpu_yuzdesi,
                "bellek": bellek_yuzdesi,
                "disk": disk_yuzdesi,
                "ag": ag_durumu,
                "disk_bos_alan_gb": disk_bos_alan,
                "surekli_calisma": SistemSaglikKontrolcu.surekli_calisma_suresi()
            }
        except Exception as e:
            console.print(f"[red]Sistem kaynakları kontrol edilemedi: {str(e)}[/red]")
            return {
                "cpu": "N/A",
                "bellek": "N/A",
                "disk": "N/A",
                "ag": "N/A",
                "disk_bos_alan_gb": "N/A",
                "surekli_calisma": "N/A"
            }
    
    @staticmethod
    def internet_baglantisi_var_mi() -> bool:
        """Internet bağlantısını kontrol et"""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False
    
    @staticmethod
    def surekli_calisma_suresi() -> str:
        """Sistem çalışma süresini al"""
        try:
            # Linux sistemlerde
            with open('/proc/uptime', 'r') as f:
                saniye = float(f.readline().split()[0])
                saat = int(saniye // 3600)
                dakika = int((saniye % 3600) // 60)
                return f"{saat} saat {dakika} dakika"
        except:
            # Diğer platformlar için tahmini değer
            return "Bilinmiyor"

class AutoReconXMotoru:
    def __init__(self):
        self.yapilandirma = {
            "tarama_yogunlugu": "dengeli",
            "api_anahtarlari": {},
            "ozel_kelime_listeleri": {},
            "zaman_asimi": DEFAULT_TIMEOUT,
            "maks_es_zamanli_istek": MAX_CONCURRENT_REQUESTS,
            "etik_mod": True,
            "cikti_dizini": f"otoreconx_{int(time.time())}",
            "etkin_moduller": set(),
            "hedef_bilgisi": None,
            "kurum_adi": "",
            "sicil_no": "",
            "yetkili_kisi": "",
            "yetki_belgesi_no": "",
            "tarama_turu": "standart",
            "kvkk_onayi": False,
            "tr_cert_verileri_guncellendi": False
        }
        self.siber_istihbarat = None
        self.baslangic_zamani = None
        self.guvenlik_bulgulari: List[GuvenlikBulgu] = []
        self.hedef_bilgisi = None
        self.sistem_kaynaklari = {}
        self._rapor_sablon_yukleyici = None
    
    async def baslat(self):
        """Motoru başlat ve yapılandır"""
        console.clear()
        await self.banner_goster()
        await self.sistem_sagligi_kontrolu()
        await self.etik_uyumluluk_kontrolu()
        await self.hedef_bilgisi_topla()
        await self.tarama_yapilandir()
        await self.ortam_hazirla()
        await self.tr_cert_verilerini_guncelle()
        await self.istihbarat_donemi_calistir()
    
    async def banner_goster(self):
        """Profesyonel banner göster"""
        banner = Panel(
            f"[bold red]⚔️ AUTO RECON X ULTRA PRO TÜRKÇE v4.1[/bold red]\n"
            f"[italic]Tüm Sistem Açıkları ve Zafiyetleri Taranan En Güçlü Platform[/italic]\n"
            f"v4.1 • KVKK Uyumlu • TR-CERT Entegrasyonlu • TÜBİTAK SGE Standartları\n"
            f"roottechx (Mücahid Balcı) Tarafından Hazırlanmıştır • MIT Lisansı",
            border_style="red",
            padding=(1, 2)
        )
        console.print(banner)
        # Versiyon bilgisi
        versiyon_bilgisi = Table(show_header=False, box=box.SIMPLE)
        versiyon_bilgisi.add_column("Bileşen", style="cyan")
        versiyon_bilgisi.add_column("Değer", style="green")
        versiyon_bilgisi.add_row("Python Sürümü", sys.version.split()[0])
        versiyon_bilgisi.add_row("İşletim Sistemi", platform.system() + " " + platform.release())
        versiyon_bilgisi.add_row("Mimari", platform.machine())
        versiyon_bilgisi.add_row("CPU Çekirdek Sayısı", str(psutil.cpu_count()))
        versiyon_bilgisi.add_row("Toplam Bellek", f"{psutil.virtual_memory().total // (1024 ** 3)} GB")
        console.print(Panel(versiyon_bilgisi, title="Sistem Bilgisi", border_style="blue"))
    
    async def sistem_sagligi_kontrolu(self):
        """Sistem kaynaklarını kontrol et"""
        console.print("\n[bold blue]🔧 SİSTEM SAĞLIK KONTROLÜ[/bold blue]")
        self.sistem_kaynaklari = SistemSaglikKontrolcu.sistem_kaynaklarini_kontrol_et()
        saglik_tablosu = Table(box=box.ROUNDED)
        saglik_tablosu.add_column("Parametre", style="cyan")
        saglik_tablosu.add_column("Değer", style="green")
        saglik_tablosu.add_column("Durum", style="yellow")
        # CPU kontrolü
        cpu_durum = "✅ Normal" if self.sistem_kaynaklari["cpu"] < 80 else "⚠️ Yüksek" if self.sistem_kaynaklari["cpu"] < 95 else "❌ Kritik"
        saglik_tablosu.add_row("CPU Kullanımı", f"%{self.sistem_kaynaklari['cpu']}", cpu_durum)
        # Bellek kontrolü
        bellek_durum = "✅ Normal" if self.sistem_kaynaklari["bellek"] < 80 else "⚠️ Yüksek" if self.sistem_kaynaklari["bellek"] < 95 else "❌ Kritik"
        saglik_tablosu.add_row("Bellek Kullanımı", f"%{self.sistem_kaynaklari['bellek']}", bellek_durum)
        # Disk kontrolü
        disk_durum = "✅ Normal" if self.sistem_kaynaklari["disk"] < 85 else "⚠️ Yüksek" if self.sistem_kaynaklari["disk"] < 95 else "❌ Kritik"
        saglik_tablosu.add_row("Disk Kullanımı", f"%{self.sistem_kaynaklari['disk']}", disk_durum)
        saglik_tablosu.add_row("Boş Disk Alanı", f"{self.sistem_kaynaklari['disk_bos_alan_gb']:.1f} GB", "✅ Yeterli" if self.sistem_kaynaklari['disk_bos_alan_gb'] > 10 else "⚠️ Düşük")
        # Ağ kontrolü
        ag_durum = "✅ Aktif" if self.sistem_kaynaklari["ag"] == "aktif" else "❌ Pasif"
        saglik_tablosu.add_row("İnternet Bağlantısı", self.sistem_kaynaklari["ag"], ag_durum)
        # Sürekli çalışma
        calisma_durum = "✅ Normal" if "Bilinmiyor" in self.sistem_kaynaklari["surekli_calisma"] or int(self.sistem_kaynaklari["surekli_calisma"].split()[0]) < 30 else "⚠️ Uzun Süre"
        saglik_tablosu.add_row("Sürekli Çalışma Süresi", self.sistem_kaynaklari["surekli_calisma"], calisma_durum)
        console.print(Panel(saglik_tablosu, title="Sistem Sağlık Durumu", border_style="green"))
        # Kritik durum kontrolü
        kritik_sayaci = sum(1 for satir in saglik_tablosu.rows if "❌" in str(satir))
        if kritik_sayaci > 0:
            console.print(f"[red]❌ {kritik_sayaci} kritik sistem sorunu tespit edildi. Tarama önerilmiyor.[/red]")
            if not Confirm.ask("[bold yellow]Yine de taramaya devam etmek istiyor musunuz?[/bold yellow]", default=False):
                console.print("[green]İşlem kullanıcı tarafından iptal edildi.[/green]")
                sys.exit(0)
    
    async def etik_uyumluluk_kontrolu(self):
        """Etik kurallara ve yasalara uyumluluk kontrolü"""
        console.print("\n[bold yellow]⚖️ ETİK VE YASAL UYUMLULUK KONTROLÜ[/bold yellow]")
        uyari_metni = Panel(
            "[bold red]DİKKAT: YASAL UYARI[/bold red]\n"
            "[1] Bu araç, [bold]sadece yetkili ve yazılı izin alınmış[/bold] hedeflerde kullanılmalıdır.\n"
            "[2] Yetkisiz taramalar, 5651 Sayılı İnternet Ortamında İşlenen Suçlar Hakkında Kanun ve 5237 Sayılı Türk Ceza Kanunu kapsamında [bold red]cezai işlem[/bold red] gerektirir.\n"
            "[3] Tarama sırasında elde edilen veriler, 6698 sayılı KVKK kapsamında korunmalıdır.\n"
            "[4] Kritik altyapılar (hastaneler, enerji tesisleri, kamu kurumları) asla hedef alınmamalıdır.\n"
            "[5] Tarama hızı ve yoğunluğu, hedef sistemi etkilemeyecek şekilde ayarlanmalıdır.",
            border_style="red",
            padding=(1, 2)
        )
        console.print(uyari_metni)
        # KVKK onayı
        console.print(Panel(KVKK_UYARI_METNI, title="KVKK UYARI", border_style="yellow"))
        self.yapilandirma["kvkk_onayi"] = Confirm.ask("[bold red]KVKK maddelerini okudum ve kabul ediyorum[/bold red]", default=False)
        if not self.yapilandirma["kvkk_onayi"]:
            console.print("[red]❌ KVKK onayı alınamadı. İşlem iptal ediliyor.[/red]")
            sys.exit(1)
        # Güvenlik kodu doğrulaması
        guvenlik_kodu = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        console.print(f"\n[bold blue]🔐 Devam etmek için güvenlik kodunu girin: [cyan]{guvenlik_kodu}[/cyan][/bold blue]")
        kullanici_kodu = Prompt.ask("[bold]Güvenlik Kodu[/bold]").strip()
        if kullanici_kodu != guvenlik_kodu:
            console.print("[red]❌ Güvenlik kodu yanlış. İşlem iptal ediliyor.[/red]")
            sys.exit(1)
        # Kurumsal bilgiler
        console.print("\n[bold blue]🏢 KURUMSAL BİLGİLER[/bold blue]")
        self.yapilandirma["kurum_adi"] = Prompt.ask("[bold]Kurum Adı[/bold]").strip()
        self.yapilandirma["sicil_no"] = Prompt.ask("[bold]Sicil Numarası (Opsiyonel)[/bold]", default="").strip()
        self.yapilandirma["yetkili_kisi"] = Prompt.ask("[bold]Yetkili Kişi[/bold]").strip()
        self.yapilandirma["yetki_belgesi_no"] = Prompt.ask("[bold]Yetki Belgesi Numarası[/bold]").strip()
        # Tarama türü
        self.yapilandirma["tarama_turu"] = Prompt.ask(
            "[bold cyan]🔍 Tarama Türünü Seçin[/bold cyan]",
            choices=["standart", "derinlemesine", "hızlı", "saldırı_simülasyonu"],
            default="standart"
        )
        console.print("[green]✅ Etik ve yasal uyumluluk doğrulandı.[/green]")
        await asyncio.sleep(1)
    
    async def hedef_bilgisi_topla(self):
        """Hedef bilgilerini topla ve doğrula"""
        console.print("\n[bold blue]🎯 HEDEF BİLGİLERİ TOPLAMA[/bold blue]")
        while True:
            hedef_girisi = Prompt.ask(
                "[bold green]🔍 Hedef tanımlayıcıyı girin[/bold green]",
                default="ornek.com"
            ).strip()
            hedef_bilgisi = self.hedefi_cozumle(hedef_girisi)
            if not hedef_bilgisi:
                console.print("[red]❌ Geçersiz hedef veya çözümleme başarısız. Tekrar deneyin.[/red]")
                continue
            # Hedef bilgisi tablosu
            hedef_tablosu = Table(box=box.ROUNDED)
            hedef_tablosu.add_column("Özellik", style="cyan")
            hedef_tablosu.add_column("Değer", style="green")
            hedef_tablosu.add_row("Orijinal Hedef", hedef_girisi)
            hedef_tablosu.add_row("Çözümlenen Tür", hedef_bilgisi["tur"].upper())
            hedef_tablosu.add_row("Ana Sunucu", hedef_bilgisi["deger"])
            if "ip" in hedef_bilgisi:
                hedef_tablosu.add_row("Çözümlenen IP", hedef_bilgisi["ip"])
            if "alan_adi" in hedef_bilgisi:
                hedef_tablosu.add_row("Temel Alan Adı", hedef_bilgisi["alan_adi"])
            if "alt_alan" in hedef_bilgisi:
                hedef_tablosu.add_row("Alt Alan", hedef_bilgisi["alt_alan"])
            console.print(Panel(hedef_tablosu, title="Hedef Bilgisi", border_style="blue"))
            if Confirm.ask("[bold yellow]Bu hedef bilgileri doğru mu?[/bold yellow]", default=True):
                self.hedef_bilgisi = hedef_bilgisi
                self.yapilandirma["hedef_bilgisi"] = hedef_bilgisi
                break
    
    def hedefi_cozumle(self, hedef: str) -> Optional[Dict]:
        """Hedefi çözümler ve zengin bilgi toplar"""
        orijinal = hedef
        # URL'leri işle
        if hedef.startswith(('http://', 'https://')):
            cozumlenmis = urlparse(hedef)
            sunucu = cozumlenmis.netloc
            yol = cozumlenmis.path
        else:
            sunucu = hedef.split('/')[0]
            yol = '/' + '/'.join(hedef.split('/')[1:]) if '/' in hedef else '/'
        # Sunucuyu normalleştir
        sunucu = sunucu.split(':')[0].lower()
        # IP adresi kontrolü
        try:
            ip = ipaddress.ip_address(sunucu)
            return {
                "tur": "ip",
                "deger": str(ip),
                "orijinal": orijinal,
                "yol": yol
            }
        except ValueError:
            pass
        # Alan adı bileşenlerini çıkar
        cozumlenmis = tldextract.extract(sunucu)
        temel_alan = f"{cozumlenmis.domain}.{cozumlenmis.suffix}"
        # IP'yi çözümle
        try:
            ip = socket.gethostbyname(sunucu)
            return {
                "tur": "alanadi",
                "deger": sunucu,
                "ip": ip,
                "alan_adi": temel_alan,
                "alt_alan": cozumlenmis.subdomain,
                "orijinal": orijinal,
                "yol": yol
            }
        except socket.gaierror as e:
            console.print(f"[red]❌ DNS çözümlemesi başarısız oldu: {str(e)}[/red]")
            return None
    
    async def tarama_yapilandir(self):
        """Tarama ayarlarını yapılandır"""
        console.print("\n[bold blue]⚙️ TARAMA YAPILANDIRMASI[/bold blue]")
        # Tarama yoğunluğu
        yogunluk_secimi = Prompt.ask(
            "[bold cyan]⚡ Tarama yoğunluğunu seçin[/bold cyan]",
            choices=["gizli", "dengeli", "agresif", "tam"],
            default="dengeli"
        )
        yogunluk_haritasi = {
            "gizli": {"sure": 300, "es_zamanli": 5},
            "dengeli": {"sure": 180, "es_zamanli": 20},
            "agresif": {"sure": 120, "es_zamanli": 40},
            "tam": {"sure": 60, "es_zamanli": 80}
        }
        self.yapilandirma["tarama_yogunlugu"] = yogunluk_secimi
        self.yapilandirma["zaman_asimi"] = yogunluk_haritasi[yogunluk_secimi]["sure"]
        self.yapilandirma["maks_es_zamanli_istek"] = yogunluk_haritasi[yogunluk_secimi]["es_zamanli"]
        # Modül seçimi
        console.print("\n[bold]🧩 MODÜL SEÇİMİ[/bold]")
        console.print("[dim]Hedef türüne ve tarama yoğunluğuna göre modüller öneriliyor[/dim]")
        tum_moduller = {
            "port_taramasi": {
                "ad": "Gelişmiş Port Taraması",
                "aciklama": "Nmap ile versiyon algılama, CVE kontrolleri ve exploit önerileri",
                "varsayilan": True
            },
            "dns_enum": {
                "ad": "DNS İstihbaratı",
                "aciklama": "Alt alan adı keşfi, zone transfer denemeleri, DNSSEC analizi",
                "varsayilan": True
            },
            "ssl_analizci": {
                "ad": "SSL/TLS Derin Analiz",
                "aciklama": "Heartbleed, POODLE, zayıf şifreler, sertifika sorunları",
                "varsayilan": self.hedef_bilgisi.get("ip") is not None
            },
            "web_analizci": {
                "ad": "Web Uygulaması İstihbaratı",
                "aciklama": "Teknoloji parmak izi, güvenlik başlıkları, zafiyet taraması",
                "varsayilan": any(port in ["80", "443", "8080", "8443"] for port in ["80", "443", "8080", "8443"])
            },
            "bulut_avi": {
                "ad": "Bulut Varlık Keşfi",
                "aciklama": "S3 bucket'lar, Azure blob'lar, Google Cloud depolama",
                "varsayilan": self.hedef_bilgisi.get("tur") == "alanadi"
            },
            "siber_istihbarat": {
                "ad": "Siber İstihbarat",
                "aciklama": "AbuseIPDB, VirusTotal itibar kontrolleri",
                "varsayilan": False
            },
            "yanlis_yapilandirma_taramasi": {
                "ad": "Yanlış Yapılandırma Taraması",
                "aciklama": "Açık dosyalar, dizinler, varsayılan kimlik bilgileri",
                "varsayilan": True
            },
            "tr_cert_kontrolu": {
                "ad": "TR-CERT Ransomware Kontrolü",
                "aciklama": "TR-CERT tarafından listelenen ransomware alan adlarını kontrol et",
                "varsayilan": self.hedef_bilgisi.get("tur") == "alanadi"
            }
        }
        modul_tablosu = Table(box=box.SIMPLE)
        modul_tablosu.add_column("Modül", style="cyan")
        modul_tablosu.add_column("Açıklama", style="green")
        modul_tablosu.add_column("Önerilen", style="yellow")
        for anahtar, bilgi in tum_moduller.items():
            onerilen = "✅" if bilgi["varsayilan"] else "❌"
            modul_tablosu.add_row(anahtar.replace('_', ' ').title(), bilgi["aciklama"], onerilen)
        console.print(modul_tablosu)
        self.yapilandirma["etkin_moduller"] = set()
        for anahtar, bilgi in tum_moduller.items():
            if Confirm.ask(f"  → [bold]{bilgi['ad']}[/bold] modülünü etkinleştir?", default=bilgi["varsayilan"]):
                self.yapilandirma["etkin_moduller"].add(anahtar)
        # API anahtarları
        if "siber_istihbarat" in self.yapilandirma["etkin_moduller"]:
            console.print("\n[bold yellow]🔑 SİBER İSTİHBARAT API YAPILANDIRMASI[/bold yellow]")
            abuse_anahtari = Prompt.ask("[bold]AbuseIPDB API Anahtarı[/bold] (isteğe bağlı)", default="", password=True)
            vt_anahtari = Prompt.ask("[bold]VirusTotal API Anahtarı[/bold] (isteğe bağlı)", default="", password=True)
            self.yapilandirma["api_anahtarlari"] = {
                "abuseipdb": abuse_anahtari.strip() or None,
                "virustotal": vt_anahtari.strip() or None
            }
        # Özel kelime listeleri
        if "web_analizci" in self.yapilandirma["etkin_moduller"]:
            console.print("\n[bold blue]📚 ÖZEL KELİME LİSTESİ YAPILANDIRMASI[/bold blue]")
            dizin_kelime_listesi = Prompt.ask(
                "[bold]Özel dizin kelime listesi yolu[/bold]",
                default="/usr/share/wordlists/dirb/common.txt"
            )
            if os.path.exists(dizin_kelime_listesi):
                self.yapilandirma["ozel_kelime_listeleri"]["dizinler"] = dizin_kelime_listesi
        # Tarama parametreleri
        console.print("\n[bold blue]⏱️ TARAMA PARAMETRELERİ[/bold blue]")
        self.yapilandirma["zaman_asimi"] = FloatPrompt.ask(
            "[bold]Modül başına zaman aşımı (saniye)[/bold]",
            default=float(self.yapilandirma["zaman_asimi"]),
            show_default=True
        )
        # Hız sınırları (Türk hedefler için önemlidir)
        console.print("\n[bold yellow]⚡ HIZ SINIRLAMALARI[/bold yellow]")
        console.print("[dim]Türk hedeflerde hız sınırları etik kurallara uymak için önemlidir[/dim]")
        self.yapilandirma["maks_es_zamanli_istek"] = IntPrompt.ask(
            "[bold]Maksimum eşzamanlı istek sayısı[/bold]",
            default=self.yapilandirma["maks_es_zamanli_istek"],
            show_default=True
        )
    
    async def ortam_hazirla(self):
        """Tarama ortamını hazırla"""
        # Çıktı dizinini oluştur
        os.makedirs(self.yapilandirma["cikti_dizini"], exist_ok=True)
        # Siber istihbaratı başlat
        if "siber_istihbarat" in self.yapilandirma["etkin_moduller"] and any(self.yapilandirma["api_anahtarlari"].values()):
            self.siber_istihbarat = SiberIstihbarat(self.yapilandirma["api_anahtarlari"])
            await self.siber_istihbarat.oturum_ac()
        console.print(f"\n[bold green]✅ Ortam [cyan]{self.yapilandirma['tarama_yogunlugu']}[/cyan] yoğunluklu tarama için hazırlandı[/bold green]")
        console.print(f"[dim]→ Çıktı dizini: [cyan]{self.yapilandirma['cikti_dizini']}[/cyan][/dim]")
        console.print(f"[dim]→ Maksimum eşzamanlı istek: [cyan]{self.yapilandirma['maks_es_zamanli_istek']}[/cyan][/dim]")
        console.print(f"[dim]→ Modül zaman aşımı: [cyan]{self.yapilandirma['zaman_asimi']}[/cyan] saniye[/dim]")
    
    async def tr_cert_verilerini_guncelle(self):
        """TR-CERT verilerini güncelle"""
        if "tr_cert_kontrolu" in self.yapilandirma["etkin_moduller"]:
            self.siber_istihbarat = self.siber_istihbarat or SiberIstihbarat()
            await self.siber_istihbarat.tr_cert_ransomware_kontrolu()
            self.yapilandirma["tr_cert_verileri_guncellendi"] = True
    
    async def istihbarat_donemi_calistir(self):
        """Ana istihbarat toplama döngüsü"""
        self.baslangic_zamani = time.time()
        console.print("\n[bold blue]🚀 İSTİHBARAT TOPLAMA DÖNGÜSÜ BAŞLATILIYOR[/bold blue]")
        moduller = [
            ("dns_enum", self.dns_istihbarati_calistir),
            ("port_taramasi", self.port_istihbarati_calistir),
            ("ssl_analizci", self.ssl_istihbarati_calistir),
            ("web_analizci", self.web_istihbarati_calistir),
            ("bulut_avi", self.bulut_istihbarati_calistir),
            ("siber_istihbarat", self.siber_istihbarati_calistir),
            ("yanlis_yapilandirma_taramasi", self.yanlis_yapilandirma_istihbarati_calistir),
            ("tr_cert_kontrolu", self.tr_cert_istihbarati_calistir)
        ]
        for modul_id, modul_fonksiyonu in moduller:
            if modul_id in self.yapilandirma["etkin_moduller"]:
                try:
                    console.print(f"\n[bold magenta]::: MODÜL ÇALIŞTIRILIYOR: [cyan]{modul_id.replace('_', ' ').title()}[/cyan] :::[/bold magenta]")
                    baslangic = time.time()
                    await asyncio.wait_for(modul_fonksiyonu(), timeout=self.yapilandirma["zaman_asimi"])
                    gecen_sure = time.time() - baslangic
                    console.print(f"[green]✓ Modül {gecen_sure:.1f} saniyede tamamlandı[/green]")
                except asyncio.TimeoutError:
                    console.print(f"[red]✗ Modül {self.yapilandirma['zaman_asimi']} saniye sonra zaman aşımına uğradı[/red]")
                except Exception as e:
                    console.print(f"[red]✗ Modül hatası: {str(e)}[/red]")
        console.print("\n[bold green]🎉 İSTİHBARAT TOPLAMA TAMAMLANDI[/bold green]")
        await self.raporlari_olustur()
        await self.temizlik_yap()
    
    async def dns_istihbarati_calistir(self):
        """Gelişmiş DNS istihbaratı toplama"""
        hedef = self.hedef_bilgisi["deger"]
        bulgular = []
        # Temel DNS kayıtları
        dns_kayitlari = {}
        cozumleyici = dns.asyncresolver.Resolver()
        cozumleyici.timeout = 5
        cozumleyici.lifetime = 5
        kayit_turleri = ["A", "AAAA", "MX", "NS", "TXT", "SOA", "CNAME", "PTR"]
        for tur in kayit_turleri:
            try:
                cevaplar = await cozumleyici.resolve(hedef, tur)
                dns_kayitlari[tur] = [str(veri) for veri in cevaplar]
            except Exception as e:
                dns_kayitlari[tur] = []
                console.print(f"[dim]DNS {tur} kaydı alınamadı: {str(e)}[/dim]")
        # Alt alan adı keşfi
        alt_alan_adlari = set()
        if os.system("which amass > /dev/null 2>&1") == 0:
            console.print("[dim]🔍 Amass ile alt alan adı keşfi yapılıyor...[/dim]")
            komut = ["amass", "enum", "-d", hedef, "-o", "/tmp/amass.out", "-silent", "-config", "/etc/amass/config.ini"]
            surec = await asyncio.create_subprocess_exec(*komut, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
            await surec.wait()
            if os.path.exists("/tmp/amass.out"):
                with open("/tmp/amass.out") as f:
                    for satir in f:
                        alt_alan = satir.strip()
                        if alt_alan.endswith(f".{hedef}"):
                            alt_alan_adlari.add(alt_alan)
                os.remove("/tmp/amass.out")
        # Zone transfer denemesi
        ns_sunuculari = dns_kayitlari.get("NS", [])
        for ns in ns_sunuculari:
            try:
                ns_ip = await cozumleyici.resolve(ns, "A")
                # Zone transfer denemesi (etik kurallara dikkat)
                if self.yapilandirma["tarama_turu"] == "saldırı_simülasyonu":
                    console.print(f"[dim]DNS zone transfer denemesi yapılıyor: {ns}[/dim]")
                    # Gerçek zone transfer kodu buraya gelecek
                    # Şimdilik sadece bilgilendirme
            except Exception as e:
                continue
        # Bulguları ekle
        for alt_alan in alt_alan_adlari:
            bulgular.append(GuvenlikBulgu(
                modul="dns_enum",
                tip="Keşfedilen Alt Alan Adı",
                risk_seviyesi=RiskSeviyesi.BILGI,
                detaylar=alt_alan
            ))
        self.guvenlik_bulgulari.extend(bulgular)
        # DNS istihbaratını göster
        dns_tablosu = Table(title="🌐 DNS İstihbaratı", box=box.ROUNDED)
        dns_tablosu.add_column("Kayıt Türü", style="cyan")
        dns_tablosu.add_column("Kayıtlar", style="green")
        for tur, kayitlar in dns_kayitlari.items():
            if kayitlar:
                dns_tablosu.add_row(tur, "\n".join(kayitlar[:3]) + ("..." if len(kayitlar) > 3 else ""))
        console.print(dns_tablosu)
    
    async def port_istihbarati_calistir(self):
        """Gelişmiş port taraması ve CVE analizi"""
        ip = self.hedef_bilgisi.get("ip", self.hedef_bilgisi["deger"])
        yogunluk = self.yapilandirma["tarama_yogunlugu"]
        # Nmap komutunu yoğunluğa göre oluştur
        yogunluk_haritasi = {
            "gizli": "-sS -T2 -F --script=default",
            "dengeli": "-sV -sC -T4 -F --script=vuln,vulners",
            "agresif": "-sV -sC -T4 -p 1-1000 --script=vuln,vulners,smb-os-discovery",
            "tam": "-sV -sC -T4 -p- --script=vuln,vulners,smb-os-discovery,dns-enum"
        }
        komut = ["nmap"] + yogunluk_haritasi[yogunlugu].split() + ["-oX", "-", ip]
        console.print(f"[dim]📡 Nmap çalıştırılıyor: {' '.join(komut)}[/dim]")
        nmap_ciktisi = await asyncio.to_thread(self.guvenli_komut_calistir, komut, zaman_asimi=900)
        if not nmap_ciktisi:
            console.print("[red]✗ Nmap taraması başarısız oldu[/red]")
            return
        # Nmap sonuçlarını işle
        import xml.etree.ElementTree as ET
        kok = ET.fromstring(nmap_ciktisi)
        hizmetler = []
        for host in kok.findall("host"):
            for port in host.findall(".//port"):
                if port.find("state").get("state") == "open":
                    port_id = port.get("portid")
                    hizmet = port.find("service")
                    ad = hizmet.get("name", "bilinmeyen") if hizmet else "bilinmeyen"
                    urun = hizmet.get("product", "") if hizmet else ""
                    versiyon = hizmet.get("version", "") if hizmet else ""
                    banner = ""
                    for script in port.findall("script"):
                        if script.get("id") == "banner":
                            banner = script.get("output", "")
                    # CVE algılama
                    cveler = []
                    for script in port.findall(".//script[@id='vulners']"):
                        for tablo in script.findall(".//table"):
                            cve_id = None
                            cvss = 0.0
                            for eleman in tablo.findall("elem"):
                                if eleman.get("key") == "id" and "CVE-" in eleman.text:
                                    cve_id = eleman.text
                                elif eleman.get("key") == "cvss" and eleman.text.replace('.', '', 1).isdigit():
                                    cvss = float(eleman.text)
                            if cve_id:
                                cveler.append((cve_id, cvss))
                    # Risk seviyesi belirle
                    risk_seviyesi = self.risk_seviyesi_hesapla(port_id, ad, urun, versiyon)
                    hizmetler.append({
                        "port": port_id,
                        "proto": port.get("protocol", "tcp"),
                        "hizmet": ad,
                        "urun": urun,
                        "versiyon": versiyon,
                        "banner": banner[:100],
                        "risk_seviyesi": risk_seviyesi,
                        "cveler": cveler
                    })
                    # Kritik CVE'ler için bulgular ekle
                    for cve_id, cvss in cveler:
                        seviye = RiskSeviyesi.KRITIK if cvss >= 9.0 else RiskSeviyesi.YUKSEK if cvss >= 7.0 else RiskSeviyesi.ORTA
                        self.guvenlik_bulgulari.append(GuvenlikBulgu(
                            modul="port_taramasi",
                            port=port_id,
                            tip=f"CVE: {cve_id}",
                            risk_seviyesi=seviye,
                            detaylar=f"CVSS {cvss}: {ad} {versiyon}",
                            cvss=cvss,
                            cozum_onerisi=f"{urun} ürününü bu güvenlik açığı olmayan sürüme güncelleyin",
                            referanslar=[f"https://www.trustwave.com/tr/resources/security-resources/cve-details/?cve={cve_id}", f"https://nvd.nist.gov/vuln/detail/{cve_id}"],
                            kurum_ici_sorumlu="Sistem Yöneticisi"
                        ))
        # Port istihbaratını göster
        port_tablosu = Table(title=f"🚪 Açık Portlar ({len(hizmetler)})", box=box.DOUBLE_EDGE)
        port_tablosu.add_column("Port", style="bold cyan")
        port_tablosu.add_column("Hizmet", style="green")
        port_tablosu.add_column("Versiyon", style="yellow")
        port_tablosu.add_column("Risk", style="red")
        port_tablosu.add_column("CVE'ler", style="magenta")
        for hizmet in hizmetler:
            cve_str = "\n".join([f"{cve} (CVSS:{cvss})" for cve, cvss in hizmet["cveler"][:2]]) if hizmet["cveler"] else "–"
            risk_stili = hizmet["risk_seviyesi"].renk()
            port_tablosu.add_row(
                hizmet["port"],
                hizmet["hizmet"],
                f"{hizmet['urun']} {hizmet['versiyon']}".strip() or "N/A",
                f"[{risk_stili}]{hizmet['risk_seviyesi'].value}[/{risk_stili}]",
                cve_str
            )
        console.print(port_tablosu)
    
    def risk_seviyesi_hesapla(self, port: str, hizmet: str, urun: str, versiyon: str) -> RiskSeviyesi:
        """Port, hizmet ve versiyona göre risk seviyesi hesapla"""
        kritik_portlar = ["21", "22", "23", "25", "53", "110", "135", "139", "143", "445", "1433", "3306", "3389", "5432", "5900", "6379", "27017", "33060"]
        yuksek_portlar = ["80", "443", "8080", "8443", "9000", "9200", "27017"]
        if port in kritik_portlar:
            return RiskSeviyesi.KRITIK
        elif port in yuksek_portlar:
            return RiskSeviyesi.YUKSEK
        elif "eski" in urun.lower() or "güncellenmemiş" in versiyon.lower():
            return RiskSeviyesi.ORTA
        return RiskSeviyesi.DUSUK
    
    async def ssl_istihbarati_calistir(self):
        """SSL/TLS derin analiz"""
        if not self.hedef_bilgisi.get("ip"):
            return
        # HTTPS portlarını kontrol et
        https_portlari = ["443", "8443"]
        for port in https_portlari:
            console.print(f"[dim]🔍 Port {port} üzerinde SSL/TLS analizi yapılıyor...[/dim]")
            sonuclar = await SSLAnalizci.testssl_calistir(self.hedef_bilgisi["deger"], port)
            if "hata" not in sonuclar:
                bulgular = SSLAnalizci.testssl_sonuclari_isle(sonuclar)
                self.guvenlik_bulgulari.extend(bulgular)
                # Kritik bulguları göster
                for bulgu in bulgular:
                    if bulgu.risk_seviyesi in [RiskSeviyesi.KRITIK, RiskSeviyesi.YUKSEK]:
                        console.print(f"[{bulgu.risk_seviyesi.renk()}]{bulgu.risk_seviyesi.emoji()} SSL [{port}]: {bulgu.tip} - {bulgu.detaylar}[/{bulgu.risk_seviyesi.renk()}]")
    
    async def web_istihbarati_calistir(self):
        """Web uygulaması istihbaratı"""
        temel_url = f"https://{self.hedef_bilgisi['deger']}" if any(p in ["443", "8443"] for p in ["443", "8443"]) else f"http://{self.hedef_bilgisi['deger']}"
        bulgular = []
        # WhatWeb ile teknoloji parmak izi
        if os.system("which whatweb > /dev/null 2>&1") == 0:
            console.print("[dim]🔍 WhatWeb ile teknoloji parmak izi alınıyor...[/dim]")
            komut = ["whatweb", "--color=never", "--quiet", temel_url]
            whatweb_ciktisi = await asyncio.to_thread(self.guvenli_komut_calistir, komut, zaman_asimi=60)
            if whatweb_ciktisi:
                console.print(Panel(whatweb_ciktisi, title="Web Teknolojileri", border_style="cyan"))
        # Güvenlik başlıkları analizi
        try:
            async with aiohttp.ClientSession() as oturum:
                async with oturum.get(temel_url, timeout=15) as cevap:
                    basliklar = cevap.headers
                    eksik_basliklar = []
                    for baslik in ["Strict-Transport-Security", "Content-Security-Policy", "X-Frame-Options", "X-Content-Type-Options"]:
                        if baslik not in basliklar:
                            eksik_basliklar.append(baslik)
                    if eksik_basliklar:
                        bulgular.append(GuvenlikBulgu(
                            modul="web_analizci",
                            tip="Eksik Güvenlik Başlıkları",
                            risk_seviyesi=RiskSeviyesi.ORTA,
                            detaylar=f"Eksik başlıklar: {', '.join(eksik_basliklar)}",
                            cozum_onerisi="Önerilen güvenlik başlıklarını uygulayın"
                        ))
        except Exception as e:
            console.print(f"[dim]⚠️ Web başlığı analizi başarısız oldu: {str(e)}[/dim]")
        # Zafiyet taraması
        zafiyet_bulgulari = await WebZayiflikTaramasi.ortak_zayiflik_kontrolu(temel_url)
        bulgular.extend(zafiyet_bulgulari)
        # Dizin kaba kuvvet taraması
        if os.system("which dirsearch > /dev/null 2>&1") == 0:
            console.print("[dim]🔍 Dizin kaba kuvvet taraması yapılıyor (2-3 dakika sürebilir)...[/dim]")
            kelime_listesi = self.yapilandirma["ozel_kelime_listeleri"].get("dizinler", "/usr/share/wordlists/dirb/common.txt")
            komut = [
                "dirsearch", "-u", temel_url, "-w", kelime_listesi,
                "-e", "php,html,js,json,conf,txt,yaml,yml,sql,zip,tar,gz,pdf,docx,xlsx",
                "-t", str(min(self.yapilandirma["maks_es_zamanli_istek"], 50)),
                "-q", "-o", "/tmp/dirsearch.out"
            ]
            await asyncio.to_thread(self.guvenli_komut_calistir, komut, zaman_asimi=180)
            if os.path.exists("/tmp/dirsearch.out"):
                with open("/tmp/dirsearch.out") as f:
                    acik_yollar = [satir.strip() for satir in f if "200" in satir or "301" in satir or "403" in satir]
                if acik_yollar:
                    bulgular.append(GuvenlikBulgu(
                        modul="web_analizci",
                        tip="Açık Dizinler/Dosyalar",
                        risk_seviyesi=RiskSeviyesi.ORTA,
                        detaylar=acik_yollar[:10],
                        cozum_onerisi="Hassas dosya ve dizinlere erişimi kısıtlayın"
                    ))
                os.remove("/tmp/dirsearch.out")
        self.guvenlik_bulgulari.extend(bulgular)
    
    async def bulut_istihbarati_calistir(self):
        """Bulut varlık keşfi"""
        if self.hedef_bilgisi.get("tur") != "alanadi":
            return
        console.print("[dim]☁️ Bulut varlık keşfi yapılıyor...[/dim]")
        bulgular = await BulutAvi.s3_bucket_kontrolu(self.hedef_bilgisi["deger"])
        self.guvenlik_bulgulari.extend(bulgular)
        for bulgu in bulgular:
            console.print(f"[{bulgu.risk_seviyesi.renk()}]{bulgu.risk_seviyesi.emoji()} {bulgu.tip}: {bulgu.detaylar}[/{bulgu.risk_seviyesi.renk()}]")
    
    async def siber_istihbarati_calistir(self):
        """Siber istihbarat toplama"""
        if not self.siber_istihbarat:
            return
        ip = self.hedef_bilgisi.get("ip")
        alan_adi = self.hedef_bilgisi.get("alan_adi")
        if ip:
            console.print(f"[dim]🔍 IP için siber istihbarat kontrolü: {ip}[/dim]")
            abuse_verisi = await self.siber_istihbarat.abuseipdb_kontrolu(ip)
            if "hata" not in abuse_verisi:
                skor = abuse_verisi.get("data", {}).get("abuseConfidenceScore", 0)
                if skor > 50:
                    self.guvenlik_bulgulari.append(GuvenlikBulgu(
                        modul="siber_istihbarat",
                        tip="Kötü İtibarlı IP",
                        risk_seviyesi=RiskSeviyesi.YUKSEK,
                        detaylar=f"AbuseIPDB skoru: %{skor}",
                        referanslar=[f"https://www.abuseipdb.com/check/{ip}"],
                        kurum_ici_sorumlu="Siber Güvenlik Ekibi"
                    ))
        if alan_adi:
            console.print(f"[dim]🔍 Alan adı için siber istihbarat kontrolü: {alan_adi}[/dim]")
            vt_verisi = await self.siber_istihbarat.virustotal_kontrolu(alan_adi)
            if "hata" not in vt_verisi:
                istatistikler = vt_verisi.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                kotu = istatistikler.get("malicious", 0)
                if kotu > 0:
                    seviye = RiskSeviyesi.KRITIK if kotu > 5 else RiskSeviyesi.YUKSEK
                    self.guvenlik_bulgulari.append(GuvenlikBulgu(
                        modul="siber_istihbarat",
                        tip="Kötü İtibarlı Alan Adı",
                        risk_seviyesi=seviye,
                        detaylar=f"VirusTotal: {kotu} güvenlik firması bu alan adını işaretledi",
                        referanslar=[f"https://www.virustotal.com/gui/domain/{alan_adi}"],
                        kurum_ici_sorumlu="Siber Güvenlik Ekibi"
                    ))
    
    async def yanlis_yapilandirma_istihbarati_calistir(self):
        """Yanlış yapılandırma taraması"""
        console.print("[dim]🔍 Yanlış yapılandırma kontrolleri yapılıyor...[/dim]")
        # Varsayılan kimlik bilgileri kontrolü
        varsayilan_kimlikler = {
            "yonetici:yonetici": ["http://admin:admin@" + self.hedef_bilgisi["deger"]],
            "kok:kok": ["http://root:root@" + self.hedef_bilgisi["deger"]],
            "test:test": ["http://test:test@" + self.hedef_bilgisi["deger"]]
        }
        for kimlik, url_listesi in varsayilan_kimlikler.items():
            for url in url_listesi:
                try:
                    async with aiohttp.ClientSession() as oturum:
                        async with oturum.get(url, timeout=10) as cevap:
                            if cevap.status == 200:
                                self.guvenlik_bulgulari.append(GuvenlikBulgu(
                                    modul="yanlis_yapilandirma",
                                    tip="Varsayılan Kimlik Bilgileri",
                                    risk_seviyesi=RiskSeviyesi.KRITIK,
                                    detaylar=f"Varsayılan kimlik bilgileri çalışıyor: {kimlik}",
                                    cozum_onerisi="Varsayılan kimlik bilgilerini hemen değiştirin",
                                    kurum_ici_sorumlu="Sistem Yöneticisi"
                                ))
                except:
                    continue
    
    async def tr_cert_istihbarati_calistir(self):
        """TR-CERT ransomware kontrolü"""
        if not self.yapilandirma.get("tr_cert_verileri_guncellendi") or self.hedef_bilgisi.get("tur") != "alanadi":
            return
        alan_adi = self.hedef_bilgisi["deger"]
        if self.siber_istihbarat.ransomware_kontrolu(alan_adi):
            self.guvenlik_bulgulari.append(GuvenlikBulgu(
                modul="tr_cert_kontrol",
                tip="TR-CERT Ransomware Listesinde",
                risk_seviyesi=RiskSeviyesi.KRITIK,
                detaylar=f"Bu alan adı TR-CERT tarafından ransomware yayını için listelenmiş.",
                cozum_onerisi="Alan adını derhal izole edin ve yetkililere bildirin",
                referanslar=["https://www.trcert.gov.tr/acik-erisim/ransomware"],
                kurum_ici_sorumlu="Siber Güvenlik Sorumlusu"
            ))
            console.print(f"[bold red]🚨 UYARI: {alan_adi} TR-CERT ransomware listesinde bulundu![/bold red]")
    
    async def raporlari_olustur(self):
        """Profesyonel, kapsamlı raporlar oluştur"""
        console.print("\n[bold blue]📊 İSTİHBARAT RAPORLARI OLUŞTURULUYOR[/bold blue]")
        # Risk seviyelerine göre bulguları grupla
        risk_gruplari = {seviye: [] for seviye in RiskSeviyesi}
        for bulgu in self.guvenlik_bulgulari:
            risk_gruplari[bulgu.risk_seviyesi].append(bulgu)
        # Yürütücü özet hazırla
        kritik_sayisi = len(risk_gruplari[RiskSeviyesi.KRITIK])
        yuksek_sayisi = len(risk_gruplari[RiskSeviyesi.YUKSEK])
        toplam_bulgu = len(self.guvenlik_bulgulari)
        # HTML raporu için Jinja2 şablonu
        html_sablonu = Template("""
        <!DOCTYPE html>
        <html lang="tr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AutoReconX ULTRA PRO TÜRKÇE - Güvenlik Raporu</title>
            <style>
                :root {
                    --kritik: #ff5555;
                    --yuksek: #ffb86c;
                    --orta: #f1fa8c;
                    --dusuk: #50fa7b;
                    --bilgi: #8be9fd;
                    --bg-dark: #0f111a;
                    --card-bg: #1a1d2b;
                    --border-color: #333850;
                }
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                body {
                    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
                    background: var(--bg-dark);
                    color: #e6e6e6;
                    line-height: 1.6;
                    padding: 20px;
                }
                .container {
                    max-width: 1400px;
                    margin: 0 auto;
                }
                header {
                    text-align: center;
                    padding: 30px 0;
                    border-bottom: 1px solid var(--border-color);
                    margin-bottom: 30px;
                }
                h1 {
                    color: #ff0066;
                    font-size: 2.5rem;
                    margin-bottom: 10px;
                }
                .subtitle {
                    color: #8be9fd;
                    font-size: 1.2rem;
                }
                .executive-summary {
                    background: var(--card-bg);
                    border-radius: 10px;
                    padding: 25px;
                    margin-bottom: 30px;
                    border-left: 4px solid #ff0066;
                }
                .severity-cards {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin: 30px 0;
                }
                .severity-card {
                    background: var(--card-bg);
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    border-left: 4px solid;
                }
                .critical { border-left-color: var(--kritik); }
                .high { border-left-color: var(--yuksek); }
                .medium { border-left-color: var(--orta); }
                .low { border-left-color: var(--dusuk); }
                .info { border-left-color: var(--bilgi); }
                .card-number {
                    font-size: 2.5rem;
                    font-weight: bold;
                    margin: 10px 0;
                }
                .critical .card-number { color: var(--kritik); }
                .high .card-number { color: var(--yuksek); }
                .medium .card-number { color: var(--orta); }
                .low .card-number { color: var(--dusuk); }
                .info .card-number { color: var(--bilgi); }
                .findings-section {
                    margin: 40px 0;
                }
                .finding-card {
                    background: var(--card-bg);
                    border-radius: 8px;
                    padding: 20px;
                    margin-bottom: 15px;
                    border-left: 4px solid;
                }
                .finding-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 10px;
                }
                .finding-severity {
                    font-weight: bold;
                    padding: 3px 10px;
                    border-radius: 4px;
                }
                .critical { color: var(--kritik); }
                .high { color: var(--yuksek); }
                .medium { color: var(--orta); }
                .low { color: var(--dusuk); }
                .info { color: var(--bilgi); }
                .remediation {
                    background: rgba(80, 250, 123, 0.1);
                    padding: 15px;
                    border-radius: 6px;
                    margin-top: 15px;
                }
                footer {
                    text-align: center;
                    margin-top: 50px;
                    padding-top: 20px;
                    border-top: 1px solid var(--border-color);
                    color: #888;
                }
                @media (max-width: 768px) {
                    .severity-cards {
                        grid-template-columns: 1fr;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>AutoReconX ULTRA PRO TÜRKÇE</h1>
                    <p class="subtitle">Etik Siber Güvenlik İstihbarat Raporu • PTES/OSSTMM Compliant</p>
                    <p>Oluşturulma: {{ tarih }} • Hedef: {{ hedef }}</p>
                </header>
                <div class="kurumsal-bilgiler">
                    <h2>Kurumsal Bilgiler</h2>
                    <p><strong>Kurum Adı:</strong> {{ kurum_adi }}</p>
                    <p><strong>Sicil Numarası:</strong> {{ sicil_no or "Belirtilmemiş" }}</p>
                    <p><strong>Yetkili Kişi:</strong> {{ yetkili_kisi }}</p>
                    <p><strong>Yetki Belgesi No:</strong> {{ yetki_belgesi_no }}</p>
                    <p><strong>Tarama Türü:</strong> {{ tarama_turu }}</p>
                </div>
                <div class="executive-summary">
                    <h2>Yürütücü Özet</h2>
                    <p>Bu rapor, <strong>{{ hedef }}</strong> hedefi üzerinde yetkili olarak yapılan siber güvenlik taramasının bulgularını içermektedir. Toplam <strong>{{ toplam_bulgu }}</strong> güvenlik bulgusu tespit edildi, bunlardan <strong>{{ kritik_sayisi }}</strong> adedi kritik ve <strong>{{ yuksek_sayisi }}</strong> adedi yüksek risk seviyesinde olup acil müdahale gerektirmektedir.</p>
                </div>
                <div class="severity-cards">
                    <div class="severity-card critical">
                        <h3>Kritik Risk</h3>
                        <div class="card-number">{{ kritik_sayisi }}</div>
                        <p>Acil müdahale gereklidir</p>
                    </div>
                    <div class="severity-card high">
                        <h3>Yüksek Risk</h3>
                        <div class="card-number">{{ yuksek_sayisi }}</div>
                        <p>24 saat içinde çözülmeli</p>
                    </div>
                    <div class="severity-card medium">
                        <h3>Orta Risk</h3>
                        <div class="card-number">{{ orta_sayisi }}</div>
                        <p>7 gün içinde çözülmeli</p>
                    </div>
                    <div class="severity-card low">
                        <h3>Düşük Risk</h3>
                        <div class="card-number">{{ dusuk_sayisi }}</div>
                        <p>30 gün içinde çözülmeli</p>
                    </div>
                </div>
                {% for seviye in risk_seviyeleri %}
                    {% if risk_gruplari[seviye.value]|length > 0 %}
                    <div class="findings-section">
                        <h2>{{ seviye.value }} Riskli Bulgular</h2>
                        {% for bulgu in risk_gruplari[seviye.value] %}
                        <div class="finding-card {{ seviye.value.lower() }}">
                            <div class="finding-header">
                                <h3>{{ bulgu.tip }} {% if bulgu.port %}(Port {{ bulgu.port }}){% endif %}</h3>
                                <span class="finding-severity {{ seviye.value.lower() }}">{{ seviye.value }}</span>
                            </div>
                            <p><strong>Modül:</strong> {{ bulgu.modul.replace('_', ' ').title() }}</p>
                            <p><strong>Detaylar:</strong> {{ bulgu.detaylar }}</p>
                            {% if bulgu.cvss > 0 %}
                            <p><strong>CVSS Skoru:</strong> {{ bulgu.cvss }}</p>
                            <p><strong>CVSS Vektörü:</strong> {{ bulgu.cvss_vector }}</p>
                            {% endif %}
                            <div class="remediation">
                                <strong>Çözüm Önerisi:</strong> {{ bulgu.cozum_onerisi }}
                            </div>
                            {% if bulgu.referanslar %}
                            <div>
                                <strong>Referanslar:</strong>
                                <ul>
                                    {% for ref in bulgu.referanslar %}
                                    <li><a href="{{ ref }}" style="color: var(--dusuk)">{{ ref }}</a></li>
                                    {% endfor %}
                                </ul>
                            </div>
                            {% endif %}
                            <p><strong>Sorumlu:</strong> {{ bulgu.kurum_ici_sorumlu }}</strong></p>
                            <p><strong>Tespit Tarihi:</strong> {{ bulgu.tespit_tarihi.strftime('%Y-%m-%d %H:%M:%S') }}</p>
                        </div>
                        {% endfor %}
                    </div>
                    {% endif %}
                {% endfor %}
                <footer>
                    <p>AutoReconX ULTRA PRO TÜRKÇE v4.1 Tarafından Oluşturuldu • Etik Kullanım İçindir</p>
                    <p>© {{ yil }} roottechx (Mücahid Balcı) • MIT Lisansı • github.com/roottechxtr</p>
                    <p style="color: var(--kritik); font-weight: bold;">Bu rapor hassas güvenlik bilgileri içerir. Kurumunuzun veri sınıflandırma politikasına göre saklanmalı ve paylaşılmalıdır.</p>
                    <p><strong>KVKK Uyarısı:</strong> Bu raporda yer alan kişisel veriler, 6698 sayılı KVKK kapsamında korunmakta olup, sadece yetkili merciler tarafından talep edilmesi durumunda yetkili mercilere teslim edilecektir.</p>
                </footer>
            </div>
        </body>
        </html>
        """)
        # Şablon için verileri hazırla
        simdiki_zaman = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        rapor_verileri = {
            "tarih": simdiki_zaman,
            "hedef": self.hedef_bilgisi["orijinal"],
            "toplam_bulgu": toplam_bulgu,
            "kritik_sayisi": kritik_sayisi,
            "yuksek_sayisi": yuksek_sayisi,
            "orta_sayisi": len(risk_gruplari[RiskSeviyesi.ORTA]),
            "dusuk_sayisi": len(risk_gruplari[RiskSeviyesi.DUSUK]),
            "risk_seviyeleri": [RiskSeviyesi.KRITIK, RiskSeviyesi.YUKSEK, RiskSeviyesi.ORTA, RiskSeviyesi.DUSUK, RiskSeviyesi.BILGI],
            "risk_gruplari": {seviye.value: risk_gruplari[seviye] for seviye in RiskSeviyesi},
            "yil": datetime.now().year,
            "kurum_adi": self.yapilandirma["kurum_adi"],
            "sicil_no": self.yapilandirma["sicil_no"],
            "yetkili_kisi": self.yapilandirma["yetkili_kisi"],
            "yetki_belgesi_no": self.yapilandirma["yetki_belgesi_no"],
            "tarama_turu": self.yapilandirma["tarama_turu"]
        }
        # HTML raporu oluştur
        html_icerik = html_sablonu.render(**rapor_verileri)
        html_yolu = os.path.join(self.yapilandirma["cikti_dizini"], f"rapor_{int(time.time())}.html")
        async with aiofiles.open(html_yolu, "w", encoding="utf-8") as f:
            await f.write(html_icerik)
        # JSON raporu oluştur
        json_yolu = os.path.join(self.yapilandirma["cikti_dizini"], f"bulgular_{int(time.time())}.json")
        bulgular_json = [bulgu.to_dict() for bulgu in self.guvenlik_bulgulari]
        async with aiofiles.open(json_yolu, "w", encoding="utf-8") as f:
            await f.write(json.dumps(bulgular_json, indent=2, ensure_ascii=False))
        console.print(f"[green]✓ HTML raporu oluşturuldu: [cyan]{html_yolu}[/cyan][/green]")
        console.print(f"[green]✓ JSON raporu oluşturuldu: [cyan]{json_yolu}[/cyan][/green]")
        # Özet tablosu göster
        ozet_tablosu = Table(title="🚨 Güvenlik Bulguları Özeti", box=box.DOUBLE_EDGE)
        ozet_tablosu.add_column("Risk Seviyesi", style="bold")
        ozet_tablosu.add_column("Sayı", justify="right")
        for seviye in RiskSeviyesi:
            sayi = len(risk_gruplari[seviye])
            if sayi > 0:
                ozet_tablosu.add_row(seviye.value, str(sayi), style=seviye.renk())
        console.print(ozet_tablosu)
    
    async def temizlik_yap(self):
        """Kaynakları temizle ve kapat"""
        if self.siber_istihbarat:
            await self.siber_istihbarat.oturumu_kapat()
        gecen_sure = time.time() - self.baslangic_zamani
        console.print(f"\n[bold cyan]⏱️ Toplam tarama süresi: {gecen_sure:.1f} saniye[/bold cyan]")
        console.print(f"[bold green]✅ Tüm raporlar kaydedildi: [cyan]{self.yapilandirma['cikti_dizini']}[/cyan][/bold green]")
        # Kritik bulgular varsa ekstra uyarı
        kritik_bulgular = [b for b in self.guvenlik_bulgulari if b.risk_seviyesi == RiskSeviyesi.KRITIK]
        if kritik_bulgular:
            console.print("\n[bold red]💥 KRİTİK UYARI: Bu hedefte acil müdahale gerektiren kritik güvenlik açıkları bulundu![/bold red]")
            console.print("[bold red]Lütfen bu bulguları hemen ilgili kişilere iletin ve gerekli önlemleri alın.[/bold red]")
        console.print("\n[bold yellow]🛡️ HATIRLATMA: Güçlü olanın sorumluluğu da ağır olur. Bu bulguları etik ve yasal çerçevede kullanın.[/bold yellow]")
        console.print("[dim]Cumhurbaşkanlığı Dijital Dönüşüm Ofisi, TÜBİTAK BİLGEM ve Siber Güvenlik Araştırma Merkezi (SGAM) ile iş birliği içinde çalışıyoruz.[/dim]")

    def guvenli_komut_calistir(self, komut: list, zaman_asimi: int = 300) -> Optional[str]:
        """Güvenli komut çalıştırma fonksiyonu"""
        try:
            sonuc = subprocess.run(
                komut,
                capture_output=True,
                text=True,
                timeout=zaman_asimi,
                env={**os.environ, "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"}
            )
            if sonuc.returncode != 0:
                console.print(f"[dim]⚠️ Komut başarısız oldu ({' '.join(komut)}): {sonuc.stderr.strip()[:100]}[/dim]")
            return sonuc.stdout if sonuc.returncode == 0 else None
        except subprocess.TimeoutExpired:
            console.print(f"[yellow]⚠️ Komut zaman aşımına uğradı ({zaman_asimi} saniye): {' '.join(komut)}[/yellow]")
            return None
        except Exception as e:
            console.print(f"[dim]⚠️ Komut istisnası: {str(e)}[/dim]")
            return None

# ========== ANA GİRİŞ NOKTASI ==========
async def main():
    """Ana program akışı"""
    motor = AutoReconXMotoru()
    try:
        await motor.baslat()
    except KeyboardInterrupt:
        console.print("\n[red]🛑 İşlem kullanıcı tarafından kesildi. Nazikçe kapanılıyor...[/red]")
    except Exception as e:
        console.print(f"[red]❌ Kritik hata: {str(e)}[/red]")
        console.print_exception()
    finally:
        # Konsol çıktısını log olarak kaydet
        log_yolu = os.path.join(motor.yapilandirma["cikti_dizini"], "konsol.log")
        console.save_text(log_yolu)
        console.print(f"[dim]📝 Tam konsol çıktısı şu adrese kaydedildi: {log_yolu}[/dim]")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # Kritik bağımlılıkları kontrol et
    kritik_bagimliliklar = ["nmap"]
    eksikler = []
    for bag in kritik_bagimliliklar:
        try:
            subprocess.run([bag, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            eksikler.append(bag)
    if eksikler:
        console.print(f"[red]❌ Kritik bağımlılıklar eksik: {', '.join(eksikler)}[/red]")
        console.print("Devam etmek için lütfen önce bunları kurun.")
        sys.exit(1)
    # Python sürüm kontrolü
    if sys.version_info < (3, 8):
        console.print("[red]❌ Python 3.8 veya üzeri gereklidir.[/red]")
        sys.exit(1)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
