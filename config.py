"""
=============================================================================
 Tarım 5.0: Mobil Baz İstasyonu (Drone/İHA) Yoluyla Veri Toplama
 Konfigürasyon Parametreleri
=============================================================================
"""

import numpy as np

# ─────────────────────────────────────────────
# ALAN PARAMETRELERİ
# ─────────────────────────────────────────────
ALAN_GENISLIK = 500          # metre (x ekseni)
ALAN_YUKSEKLIK = 500         # metre (y ekseni)

# ─────────────────────────────────────────────
# SENSÖR DÜĞÜM PARAMETRELERİ
# ─────────────────────────────────────────────
SENSOR_SAYISI = 30           # Toplam sensör düğüm sayısı
SENSOR_BASLANGIC_ENERJI = 0.5   # Joule (başlangıç enerjisi)
SENSOR_BELLEK_KAPASITESI = 100   # Maksimum saklanabilecek paket sayısı

# Veri üretim parametreleri
VERI_URETIM_ARALIGI = 10    # saniye - her kaç saniyede bir veri üretilir
VERI_PAKET_BOYUTU = 4000    # bit (4 Kbit = sıcaklık, nem, toprak nem verisi)

# ─────────────────────────────────────────────
# DRONE / İHA PARAMETRELERİ
# ─────────────────────────────────────────────
DRONE_HIZ = 10               # m/s (İHA uçuş hızı)
DRONE_YUKSEKLIK = 50         # metre (uçuş yüksekliği)
DRONE_ILETISIM_MENZIL = 60  # metre (iletişim menzili - 3D mesafe)
DRONE_BASLANGIC_NOKTASI = np.array([0.0, 0.0])  # Kalkış noktası
DRONE_BEKLEME_SURESI = 2    # saniye - her sensörde bekleme süresi
DRONE_TUR_ARALIGI = 300     # saniye - turlar arası bekleme süresi

# ─────────────────────────────────────────────
# ENERJİ MODELİ PARAMETRELERİ (First Order Radio Model)
# ─────────────────────────────────────────────
E_ELEC = 50e-9              # nJ/bit - Elektronik enerji (TX/RX devresi)
E_FS = 10e-12               # pJ/bit/m^2 - Serbest alan modeli (d < d0)
E_MP = 0.0013e-12           # pJ/bit/m^4 - Çok yollu kayıp modeli (d >= d0)
E_DA = 5e-9                 # nJ/bit - Veri birleştirme enerjisi
D_CROSSOVER = 87            # metre - serbest alan / çok yollu eşik mesafesi

# ─────────────────────────────────────────────
# MULTI-HOP KARŞILAŞTIRMA PARAMETRELERİ
# ─────────────────────────────────────────────
BAZ_ISTASYONU_KONUM = np.array([250.0, 550.0])  # Sabit baz istasyonu konumu
MULTI_HOP_MENZIL = 80       # metre - multi-hop iletişim menzili

# ─────────────────────────────────────────────
# SİMÜLASYON PARAMETRELERİ
# ─────────────────────────────────────────────
SIMULASYON_SURESI = 3600     # saniye (1 saat)
RASTGELE_TOHUM = 42         # Tekrarlanabilirlik için sabit tohum

# ─────────────────────────────────────────────
# GÖRSELLEŞTİRME PARAMETRELERİ
# ─────────────────────────────────────────────
RENK_SENSOR_AKTIF = '#2ecc71'      # Yeşil
RENK_SENSOR_OLU = '#e74c3c'        # Kırmızı
RENK_SENSOR_DUSUK = '#f39c12'      # Turuncu
RENK_DRONE_YOL = '#3498db'         # Mavi
RENK_DRONE = '#e74c3c'             # Kırmızı
RENK_BAZ_ISTASYONU = '#8e44ad'     # Mor
RENK_ILETISIM = '#1abc9c'          # Turkuaz
