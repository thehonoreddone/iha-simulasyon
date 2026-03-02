"""
=============================================================================
 Tarım 5.0: Mobil Baz İstasyonu (Drone/İHA) Yoluyla Veri Toplama
 
 Ana Çalıştırma Betiği
 
 Proje: Kablosuz Algılayıcı Ağlarda Mobil Veri Toplama Simülasyonu
 
 Bu simülasyon iki senaryoyu karşılaştırır:
   1. Mobil Baz İstasyonu (Drone): Sensörler veriyi bellekte saklar,
      drone belirli aralıklarla uçarak veri toplar.
   2. Sabit Baz İstasyonu (Multi-hop): Sensörler veriyi multi-hop
      yönlendirme ile baz istasyonuna iletir.
 
 Çıktılar:
   - Konsol raporu (enerji, paket, aktif sensör istatistikleri)
   - 7 adet görselleştirme grafiği (sonuclar/ klasörüne kaydedilir)
 
 Kullanım:
   python main.py
=============================================================================
"""

import sys
import time
import numpy as np
from datetime import datetime

from config import (
    SENSOR_SAYISI, ALAN_GENISLIK, ALAN_YUKSEKLIK,
    SIMULASYON_SURESI, RASTGELE_TOHUM,
    DRONE_HIZ, DRONE_YUKSEKLIK, DRONE_ILETISIM_MENZIL,
    VERI_URETIM_ARALIGI, DRONE_TUR_ARALIGI,
    SENSOR_BASLANGIC_ENERJI, VERI_PAKET_BOYUTU
)
from simulation import TarimSimulasyonu
from visualization import tum_grafikleri_olustur


def baslik_yazdir():
    """Proje başlığını yazdırır."""
    print("\n" + "=" * 70)
    print(r"""
  ████████╗ █████╗ ██████╗ ██╗███╗   ███╗    ███████╗   ██████╗ 
  ╚══██╔══╝██╔══██╗██╔══██╗██║████╗ ████║    ██╔════╝   ██╔═══╝ 
     ██║   ███████║██████╔╝██║██╔████╔██║    ███████╗   ██║  ██╗
     ██║   ██╔══██║██╔══██╗██║██║╚██╔╝██║    ╚════██║   ██║  ██║
     ██║   ██║  ██║██║  ██║██║██║ ╚═╝ ██║    ███████║██╗╚██████╗
     ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝     ╚═╝    ╚══════╝╚═╝ ╚═════╝
    """)
    print("  Mobil Baz Istasyonu (Drone/IHA) Yoluyla Veri Toplama")
    print("  Kablosuz Algilayici Aglar - Simulasyon Projesi")
    print(f"  Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)


def parametreleri_yazdir():
    """Simülasyon parametrelerini yazdırır."""
    print("\n" + "-" * 50)
    print("  SIMULASYON PARAMETRELERI")
    print("-" * 50)
    print(f"  Alan Boyutu         : {ALAN_GENISLIK}m x {ALAN_YUKSEKLIK}m")
    print(f"  Sensor Sayisi       : {SENSOR_SAYISI}")
    print(f"  Baslangic Enerjisi  : {SENSOR_BASLANGIC_ENERJI*1000:.0f} mJ")
    print(f"  Veri Paket Boyutu   : {VERI_PAKET_BOYUTU} bit")
    print(f"  Veri Uretim Araligi : {VERI_URETIM_ARALIGI} s")
    print(f"  Drone Hizi          : {DRONE_HIZ} m/s")
    print(f"  Drone Yuksekligi    : {DRONE_YUKSEKLIK} m")
    print(f"  Iletisim Menzili    : {DRONE_ILETISIM_MENZIL} m")
    print(f"  Drone Tur Araligi   : {DRONE_TUR_ARALIGI} s")
    print(f"  Simulasyon Suresi   : {SIMULASYON_SURESI} s ({SIMULASYON_SURESI/60:.0f} dk)")
    print(f"  Rastgele Tohum      : {RASTGELE_TOHUM}")
    print("-" * 50)


def main():
    """Ana çalıştırma fonksiyonu."""
    baslangic_zamani = time.time()
    
    baslik_yazdir()
    parametreleri_yazdir()
    
    # ── Simülasyon nesnesi oluştur ──
    sim = TarimSimulasyonu(
        simulasyon_suresi=SIMULASYON_SURESI,
        sensor_sayisi=SENSOR_SAYISI,
        rastgele_tohum=RASTGELE_TOHUM
    )
    
    # ══════════════════════════════════════
    # SENARYO 1: Drone (Mobil Baz İstasyonu)
    # ══════════════════════════════════════
    print("\n  [1/3] Drone simulasyonu baslatiliyor...")
    drone_sonuclari = sim.drone_simulasyonu_calistir()
    
    # ══════════════════════════════════════
    # SENARYO 2: Multi-hop (Sabit Baz İstasyonu)
    # ══════════════════════════════════════
    print("\n  [2/3] Multi-hop simulasyonu baslatiliyor...")
    multihop_sonuclari = sim.multihop_simulasyonu_calistir()
    
    # ══════════════════════════════════════
    # KARŞILAŞTIRMA RAPORU
    # ══════════════════════════════════════
    sonuclar = sim.karsilastirma_raporu()
    
    # ══════════════════════════════════════
    # GRAFİKLER
    # ══════════════════════════════════════
    print("\n  [3/3] Grafikler olusturuluyor...")
    tum_grafikleri_olustur(
        drone_sonuclari, 
        multihop_sonuclari, 
        sim.enerji_log
    )
    
    # ══════════════════════════════════════
    # SONUÇ
    # ══════════════════════════════════════
    bitis_zamani = time.time()
    gecen_sure = bitis_zamani - baslangic_zamani
    
    print("\n" + "=" * 70)
    print("  SIMULASYON TAMAMLANDI!")
    print(f"  Toplam Sure: {gecen_sure:.1f} saniye")
    print(f"  Ciktilar: sonuclar/ klasorunde 7 grafik")
    print("=" * 70)
    
    # Özet
    d = drone_sonuclari
    m = multihop_sonuclari
    
    d_harcanan = 100 - d['ortalama_enerji']
    m_harcanan = 100 - m['ortalama_enerji']
    
    print("\n  ╔══════════════════════════════════════════════════╗")
    print("  ║  TEMEL BULGULAR                                 ║")
    print("  ╠══════════════════════════════════════════════════╣")
    
    if m_harcanan > 0 and d_harcanan > 0:
        tasarruf = ((m_harcanan - d_harcanan) / m_harcanan) * 100
        omur_orani = m_harcanan / d_harcanan
        t_str = f"%{tasarruf:.1f}"
        o_str = f"{omur_orani:.1f}x"
        print(f"  ║  Drone ile enerji tasarrufu    : {t_str:<15}    ║")
        print(f"  ║  Tahmini ag omru artisi        : {o_str:<15}    ║")
    
    da_str = f"{d['aktif_sensor_sayisi']}/{SENSOR_SAYISI}"
    ma_str = f"{m['aktif_sensor_sayisi']}/{SENSOR_SAYISI}"
    print(f"  ║  Drone aktif sensor (sonda)    : {da_str:<15}    ║")
    print(f"  ║  Multi-hop aktif sensor (sonda): {ma_str:<15}    ║")
    print("  ╚══════════════════════════════════════════════════╝")
    
    return sonuclar


if __name__ == "__main__":
    main()
