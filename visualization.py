"""
=============================================================================
 Tarım 5.0: Görselleştirme Modülü
 
 Grafikler:
   1. Ağ Topolojisi ve Drone Rotası
   2. Enerji Tüketim Karşılaştırması (Drone vs Multi-hop)
   3. Sensör Enerji Dağılımı (Isı Haritası)
   4. Zaman Serisi Analizi
   5. Drone Rota Animasyonu
   6. Bellek Doluluk Durumu
=============================================================================
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # GUI olmadan çalış
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
import os

from config import (
    ALAN_GENISLIK, ALAN_YUKSEKLIK,
    RENK_SENSOR_AKTIF, RENK_SENSOR_OLU, RENK_SENSOR_DUSUK,
    RENK_DRONE_YOL, RENK_DRONE, RENK_BAZ_ISTASYONU, RENK_ILETISIM,
    DRONE_ILETISIM_MENZIL, BAZ_ISTASYONU_KONUM
)

# Türkçe karakter desteği
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['figure.figsize'] = (12, 8)

CIKTI_KLASORU = "sonuclar"


def klasor_olustur():
    """Çıktı klasörünü oluşturur."""
    if not os.path.exists(CIKTI_KLASORU):
        os.makedirs(CIKTI_KLASORU)


def grafik1_ag_topolojisi_ve_rota(drone_sonuclari: dict, kaydet=True):
    """
    Grafik 1: Sensör ağı topolojisi + Drone rotası.
    """
    klasor_olustur()
    
    sensorler = drone_sonuclari['sensorler']
    drone = drone_sonuclari['drone']
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    
    # Alan sınırları
    ax.set_xlim(-20, ALAN_GENISLIK + 20)
    ax.set_ylim(-20, ALAN_YUKSEKLIK + 20)
    
    # Tarla arkaplanı
    tarla = plt.Rectangle((0, 0), ALAN_GENISLIK, ALAN_YUKSEKLIK, 
                           fill=True, facecolor='#f0f8e8', 
                           edgecolor='#2d5016', linewidth=2, alpha=0.5)
    ax.add_patch(tarla)
    
    # Sensörleri çiz
    for sensor in sensorler:
        if not sensor.aktif:
            renk = RENK_SENSOR_OLU
            marker = 'x'
            boyut = 80
        elif sensor.enerji_yuzdesi < 30:
            renk = RENK_SENSOR_DUSUK
            marker = 'o'
            boyut = 60
        else:
            renk = RENK_SENSOR_AKTIF
            marker = 'o'
            boyut = 60
        
        ax.scatter(sensor.konum[0], sensor.konum[1], c=renk, 
                   marker=marker, s=boyut, zorder=5, edgecolors='black', linewidth=0.5)
        ax.annotate(f'S{sensor.id}', (sensor.konum[0]+5, sensor.konum[1]+5),
                    fontsize=6, color='gray')
    
    # Drone rotasını çiz
    if drone.pozisyon_gecmisi:
        rota_x = [p[0] for p in drone.pozisyon_gecmisi]
        rota_y = [p[1] for p in drone.pozisyon_gecmisi]
        
        ax.plot(rota_x, rota_y, '-', color=RENK_DRONE_YOL, 
                linewidth=1.5, alpha=0.7, zorder=3)
        
        # Oklar (yön göstergesi)
        for i in range(0, len(rota_x)-1, max(1, len(rota_x)//15)):
            dx = rota_x[i+1] - rota_x[i]
            dy = rota_y[i+1] - rota_y[i]
            if abs(dx) > 1 or abs(dy) > 1:
                ax.annotate('', xy=(rota_x[i+1], rota_y[i+1]),
                           xytext=(rota_x[i], rota_y[i]),
                           arrowprops=dict(arrowstyle='->', color=RENK_DRONE_YOL, 
                                          lw=1.5, alpha=0.5))
    
    # Toplama noktalarını çiz
    for zaman, konum, paket in drone.toplama_noktalari:
        daire = plt.Circle(konum, DRONE_ILETISIM_MENZIL, 
                           fill=False, color=RENK_ILETISIM, 
                           linestyle='--', linewidth=0.5, alpha=0.3)
        ax.add_patch(daire)
    
    # Drone başlangıç noktası
    ax.scatter(drone.baslangic_konum[0], drone.baslangic_konum[1], 
               c=RENK_DRONE, marker='^', s=200, zorder=10, 
               edgecolors='black', linewidth=1.5, label='Drone Baslangic')
    
    # Lejant
    legend_elements = [
        mpatches.Patch(color=RENK_SENSOR_AKTIF, label=f'Aktif Sensor (E>30%)'),
        mpatches.Patch(color=RENK_SENSOR_DUSUK, label=f'Dusuk Enerji (E<30%)'),
        mpatches.Patch(color=RENK_SENSOR_OLU, label='Olu Sensor'),
        plt.Line2D([0], [0], color=RENK_DRONE_YOL, linewidth=2, label='Drone Rotasi'),
        plt.Line2D([0], [0], marker='^', color='w', markerfacecolor=RENK_DRONE, 
                   markersize=12, label='Drone Kalkis'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=8)
    
    ax.set_xlabel('X (metre)', fontsize=11)
    ax.set_ylabel('Y (metre)', fontsize=11)
    ax.set_title('Tarim 5.0 - Sensor Agi Topolojisi ve Drone Rotasi', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    
    plt.tight_layout()
    if kaydet:
        plt.savefig(f'{CIKTI_KLASORU}/1_ag_topolojisi_rota.png', bbox_inches='tight')
    plt.close()
    print(f"  [OK] Grafik 1: Ag Topolojisi ve Rota kaydedildi.")


def grafik2_enerji_karsilastirma(drone_sonuclari: dict, 
                                   multihop_sonuclari: dict, kaydet=True):
    """
    Grafik 2: Drone vs Multi-hop enerji karşılaştırması (bar chart).
    """
    klasor_olustur()
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    
    # ── Sol Grafik: Sensör bazında enerji karşılaştırması ──
    ax1 = axes[0]
    
    n = len(drone_sonuclari['enerji_dagilimi'])
    x = np.arange(n)
    genislik = 0.35
    
    drone_enerji = drone_sonuclari['enerji_dagilimi']
    multihop_enerji = multihop_sonuclari['enerji_dagilimi']
    
    bar1 = ax1.bar(x - genislik/2, drone_enerji, genislik, 
                    label='Drone (Mobil)', color='#3498db', alpha=0.8)
    bar2 = ax1.bar(x + genislik/2, multihop_enerji, genislik, 
                    label='Multi-hop (Sabit)', color='#e74c3c', alpha=0.8)
    
    ax1.set_xlabel('Sensor ID', fontsize=11)
    ax1.set_ylabel('Kalan Enerji (%)', fontsize=11)
    ax1.set_title('Sensor Bazinda Kalan Enerji', fontsize=13, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.set_xticks(x[::2])
    ax1.set_xticklabels([f'S{i}' for i in x[::2]], fontsize=8)
    ax1.grid(True, alpha=0.3, axis='y')
    ax1.set_ylim(0, 105)
    
    # ── Sağ Grafik: Özet istatistikler ──
    ax2 = axes[1]
    
    kategoriler = ['Ort. Kalan\nEnerji (%)', 'Min. Kalan\nEnerji (%)', 
                   'Aktif Sensor\n(adet)', 'Iletilen\nPaket (x10)']
    
    drone_degerler = [
        drone_sonuclari['ortalama_enerji'],
        drone_sonuclari['minimum_enerji'],
        drone_sonuclari['aktif_sensor_sayisi'],
        drone_sonuclari['toplam_paket'] / 10,
    ]
    multihop_degerler = [
        multihop_sonuclari['ortalama_enerji'],
        multihop_sonuclari['minimum_enerji'],
        multihop_sonuclari['aktif_sensor_sayisi'],
        multihop_sonuclari['toplam_paket'] / 10,
    ]
    
    x2 = np.arange(len(kategoriler))
    bar3 = ax2.bar(x2 - genislik/2, drone_degerler, genislik, 
                    label='Drone (Mobil)', color='#3498db', alpha=0.8)
    bar4 = ax2.bar(x2 + genislik/2, multihop_degerler, genislik, 
                    label='Multi-hop (Sabit)', color='#e74c3c', alpha=0.8)
    
    # Değer etiketleri
    for bar in [bar3, bar4]:
        for rect in bar:
            height = rect.get_height()
            ax2.annotate(f'{height:.1f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=8)
    
    ax2.set_xticks(x2)
    ax2.set_xticklabels(kategoriler, fontsize=9)
    ax2.set_title('Ozet Karsilastirma', fontsize=13, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    if kaydet:
        plt.savefig(f'{CIKTI_KLASORU}/2_enerji_karsilastirma.png', bbox_inches='tight')
    plt.close()
    print(f"  [OK] Grafik 2: Enerji Karsilastirma kaydedildi.")


def grafik3_enerji_isi_haritasi(drone_sonuclari: dict, 
                                  multihop_sonuclari: dict, kaydet=True):
    """
    Grafik 3: Sensör enerji dağılımı - Isı haritası (scatter plot).
    """
    klasor_olustur()
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    
    for idx, (sonuc, baslik) in enumerate([
        (drone_sonuclari, 'Drone (Mobil Baz Istasyonu)'),
        (multihop_sonuclari, 'Multi-hop (Sabit Baz Istasyonu)')
    ]):
        ax = axes[idx]
        sensorler = sonuc['sensorler']
        
        x = [s.konum[0] for s in sensorler]
        y = [s.konum[1] for s in sensorler]
        enerji = [s.enerji_yuzdesi for s in sensorler]
        
        # Alan
        tarla = plt.Rectangle((0, 0), ALAN_GENISLIK, ALAN_YUKSEKLIK, 
                               fill=True, facecolor='#f0f8e8', 
                               edgecolor='#2d5016', linewidth=1.5, alpha=0.3)
        ax.add_patch(tarla)
        
        # Scatter plot - enerji renk kodlu
        scatter = ax.scatter(x, y, c=enerji, cmap='RdYlGn', 
                             s=100, vmin=0, vmax=100, 
                             edgecolors='black', linewidth=0.5, zorder=5)
        
        # Enerji yüzde etiketleri
        for i, s in enumerate(sensorler):
            ax.annotate(f'{s.enerji_yuzdesi:.0f}%', 
                       (s.konum[0]+8, s.konum[1]+8),
                       fontsize=6, color='black')
        
        plt.colorbar(scatter, ax=ax, label='Kalan Enerji (%)', shrink=0.8)
        
        # Baz istasyonu (multi-hop için)
        if idx == 1:
            ax.scatter(BAZ_ISTASYONU_KONUM[0], BAZ_ISTASYONU_KONUM[1],
                       c=RENK_BAZ_ISTASYONU, marker='s', s=200, zorder=10,
                       edgecolors='black', linewidth=2, label='Baz Istasyonu')
            ax.legend(fontsize=9)
        
        ax.set_xlim(-20, ALAN_GENISLIK + 20)
        ax.set_ylim(-20, ALAN_YUKSEKLIK + 60)
        ax.set_xlabel('X (metre)', fontsize=10)
        ax.set_ylabel('Y (metre)', fontsize=10)
        ax.set_title(baslik, fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')
    
    plt.suptitle('Sensor Enerji Dagilimi - Isi Haritasi', fontsize=14, fontweight='bold')
    plt.tight_layout()
    if kaydet:
        plt.savefig(f'{CIKTI_KLASORU}/3_enerji_isi_haritasi.png', bbox_inches='tight')
    plt.close()
    print(f"  [OK] Grafik 3: Enerji Isi Haritasi kaydedildi.")


def grafik4_zaman_serisi(enerji_log: list, kaydet=True):
    """
    Grafik 4: Zamanla ortalama enerji ve aktif sensör sayısı.
    """
    klasor_olustur()
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    # Drone verileri
    drone_log = [log for log in enerji_log if log['senaryo'] == 'Drone']
    multihop_log = [log for log in enerji_log if log['senaryo'] == 'Multi-hop']
    
    if not drone_log or not multihop_log:
        print("  [!] Zaman serisi verisi yetersiz.")
        plt.close()
        return
    
    # ── Üst Grafik: Ortalama Enerji ──
    ax1 = axes[0]
    
    d_zaman = [log['zaman'] for log in drone_log]
    d_enerji = [log['ortalama_enerji'] for log in drone_log]
    m_zaman = [log['zaman'] for log in multihop_log]
    m_enerji = [log['ortalama_enerji'] for log in multihop_log]
    
    ax1.plot(d_zaman, d_enerji, '-o', color='#3498db', linewidth=2, 
             markersize=4, label='Drone (Mobil)', alpha=0.8)
    ax1.plot(m_zaman, m_enerji, '-s', color='#e74c3c', linewidth=2, 
             markersize=4, label='Multi-hop (Sabit)', alpha=0.8)
    
    ax1.fill_between(d_zaman, d_enerji, alpha=0.1, color='#3498db')
    ax1.fill_between(m_zaman, m_enerji, alpha=0.1, color='#e74c3c')
    
    ax1.set_xlabel('Zaman (saniye)', fontsize=11)
    ax1.set_ylabel('Ortalama Kalan Enerji (%)', fontsize=11)
    ax1.set_title('Zamanla Ortalama Enerji Degisimi', fontsize=13, fontweight='bold')
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, 105)
    
    # ── Alt Grafik: Aktif Sensör Sayısı ──
    ax2 = axes[1]
    
    d_aktif = [log['aktif_sensor'] for log in drone_log]
    m_aktif = [log['aktif_sensor'] for log in multihop_log]
    
    ax2.plot(d_zaman, d_aktif, '-o', color='#3498db', linewidth=2, 
             markersize=4, label='Drone (Mobil)', alpha=0.8)
    ax2.plot(m_zaman, m_aktif, '-s', color='#e74c3c', linewidth=2, 
             markersize=4, label='Multi-hop (Sabit)', alpha=0.8)
    
    ax2.set_xlabel('Zaman (saniye)', fontsize=11)
    ax2.set_ylabel('Aktif Sensor Sayisi', fontsize=11)
    ax2.set_title('Zamanla Aktif Sensor Sayisi', fontsize=13, fontweight='bold')
    ax2.legend(fontsize=11)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    if kaydet:
        plt.savefig(f'{CIKTI_KLASORU}/4_zaman_serisi.png', bbox_inches='tight')
    plt.close()
    print(f"  [OK] Grafik 4: Zaman Serisi kaydedildi.")


def grafik5_drone_rota_detay(drone_sonuclari: dict, kaydet=True):
    """
    Grafik 5: Drone rota detayı - mesafe ve toplama noktaları.
    """
    klasor_olustur()
    
    drone = drone_sonuclari['drone']
    sensorler = drone_sonuclari['sensorler']
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    
    # ── Sol: İlk tur rotası detayı ──
    ax1 = axes[0]
    
    tarla = plt.Rectangle((0, 0), ALAN_GENISLIK, ALAN_YUKSEKLIK, 
                           fill=True, facecolor='#f0f8e8', 
                           edgecolor='#2d5016', linewidth=1.5, alpha=0.3)
    ax1.add_patch(tarla)
    
    # Sensörler
    for s in sensorler:
        renk = RENK_SENSOR_AKTIF if s.aktif else RENK_SENSOR_OLU
        ax1.scatter(s.konum[0], s.konum[1], c=renk, s=50, 
                    edgecolors='black', linewidth=0.5, zorder=5)
        # Menzil dairesi
        daire = plt.Circle(s.konum, DRONE_ILETISIM_MENZIL/2, 
                           fill=False, color='gray', linestyle=':', 
                           linewidth=0.3, alpha=0.3)
        ax1.add_patch(daire)
    
    # Rota (renkli - zamana göre)
    if drone.pozisyon_gecmisi:
        for i in range(len(drone.pozisyon_gecmisi) - 1):
            p1 = drone.pozisyon_gecmisi[i]
            p2 = drone.pozisyon_gecmisi[i + 1] if i + 1 < len(drone.pozisyon_gecmisi) else p1
            renk_oran = i / max(1, len(drone.pozisyon_gecmisi) - 1)
            renk = plt.cm.coolwarm(renk_oran)
            ax1.plot([p1[0], p2[0]], [p1[1], p2[1]], '-', color=renk, linewidth=2, alpha=0.7)
    
    # Kalkış noktası
    ax1.scatter(drone.baslangic_konum[0], drone.baslangic_konum[1],
                c=RENK_DRONE, marker='^', s=200, zorder=10, 
                edgecolors='black', linewidth=2)
    ax1.annotate('KALKIS', (drone.baslangic_konum[0]+10, drone.baslangic_konum[1]+10),
                fontsize=9, fontweight='bold', color=RENK_DRONE)
    
    ax1.set_xlim(-20, ALAN_GENISLIK + 20)
    ax1.set_ylim(-20, ALAN_YUKSEKLIK + 20)
    ax1.set_xlabel('X (metre)', fontsize=10)
    ax1.set_ylabel('Y (metre)', fontsize=10)
    ax1.set_title('Drone Rota Detayi\n(Renk: Zaman ilerlemesi)', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_aspect('equal')
    
    # ── Sağ: Toplama istatistikleri ──
    ax2 = axes[1]
    
    if drone.toplama_noktalari:
        zamanlar = [t[0] for t in drone.toplama_noktalari]
        paketler = [t[2] for t in drone.toplama_noktalari]
        
        # Kümülatif paket
        kumulatif = np.cumsum(paketler)
        
        ax2.fill_between(zamanlar, kumulatif, alpha=0.3, color='#3498db')
        ax2.plot(zamanlar, kumulatif, '-o', color='#3498db', linewidth=2, 
                 markersize=3, label='Kumulatif Paket')
        
        ax2.set_xlabel('Zaman (saniye)', fontsize=11)
        ax2.set_ylabel('Toplam Toplanan Paket', fontsize=11)
        ax2.set_title('Drone Veri Toplama Ilerlemesi', fontsize=12, fontweight='bold')
        ax2.legend(fontsize=10)
        ax2.grid(True, alpha=0.3)
    else:
        ax2.text(0.5, 0.5, 'Veri yok', transform=ax2.transAxes, ha='center', fontsize=14)
    
    plt.tight_layout()
    if kaydet:
        plt.savefig(f'{CIKTI_KLASORU}/5_drone_rota_detay.png', bbox_inches='tight')
    plt.close()
    print(f"  [OK] Grafik 5: Drone Rota Detay kaydedildi.")


def grafik6_bellek_ve_paket(drone_sonuclari: dict, 
                              multihop_sonuclari: dict, kaydet=True):
    """
    Grafik 6: Bellek doluluk durumu ve paket kaybı analizi.
    """
    klasor_olustur()
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # ── Sol Üst: Drone - sensör bazında toplam paket ──
    ax1 = axes[0][0]
    d_sensorler = drone_sonuclari['sensorler']
    
    sensor_ids = [f'S{s.id}' for s in d_sensorler]
    uretilen = [s.toplam_uretilen_paket for s in d_sensorler]
    iletilen = [s.toplam_iletilen_paket for s in d_sensorler]
    kaybedilen = [s.toplam_kaybedilen_paket for s in d_sensorler]
    
    x = np.arange(len(sensor_ids))
    ax1.bar(x, uretilen, 0.3, label='Uretilen', color='#3498db', alpha=0.8)
    ax1.bar(x + 0.3, iletilen, 0.3, label='Iletilen', color='#2ecc71', alpha=0.8)
    ax1.bar(x + 0.6, kaybedilen, 0.3, label='Kaybedilen', color='#e74c3c', alpha=0.8)
    
    ax1.set_xticks(x[::2] + 0.3)
    ax1.set_xticklabels(sensor_ids[::2], fontsize=7, rotation=45)
    ax1.set_title('Drone - Sensor Bazli Paket Analizi', fontsize=11, fontweight='bold')
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3, axis='y')
    
    # ── Sağ Üst: Multi-hop - sensör bazında toplam paket ──
    ax2 = axes[0][1]
    m_sensorler = multihop_sonuclari['sensorler']
    
    uretilen_m = [s.toplam_uretilen_paket for s in m_sensorler]
    iletilen_m = [s.toplam_iletilen_paket for s in m_sensorler]
    
    ax2.bar(x, uretilen_m, 0.35, label='Uretilen', color='#e74c3c', alpha=0.6)
    ax2.bar(x + 0.35, iletilen_m, 0.35, label='Iletilen', color='#e67e22', alpha=0.8)
    
    ax2.set_xticks(x[::2] + 0.175)
    ax2.set_xticklabels(sensor_ids[::2], fontsize=7, rotation=45)
    ax2.set_title('Multi-hop - Sensor Bazli Paket Analizi', fontsize=11, fontweight='bold')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # ── Sol Alt: Enerji harcama dağılımı (box plot) ──
    ax3 = axes[1][0]
    
    d_harcanan = [100 - e for e in drone_sonuclari['enerji_dagilimi']]
    m_harcanan = [100 - e for e in multihop_sonuclari['enerji_dagilimi']]
    
    bp = ax3.boxplot([d_harcanan, m_harcanan], 
                      labels=['Drone', 'Multi-hop'],
                      patch_artist=True,
                      boxprops=dict(linewidth=1.5),
                      medianprops=dict(color='black', linewidth=2))
    
    bp['boxes'][0].set_facecolor('#3498db')
    bp['boxes'][0].set_alpha(0.6)
    bp['boxes'][1].set_facecolor('#e74c3c')
    bp['boxes'][1].set_alpha(0.6)
    
    ax3.set_ylabel('Harcanan Enerji (%)', fontsize=11)
    ax3.set_title('Enerji Harcama Dagilimi', fontsize=11, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='y')
    
    # ── Sağ Alt: Pasta grafik - Genel özet ──
    ax4 = axes[1][1]
    
    toplam_d_paket = sum(iletilen)
    toplam_m_paket = sum(iletilen_m)
    d_aktif = drone_sonuclari['aktif_sensor_sayisi']
    m_aktif = multihop_sonuclari['aktif_sensor_sayisi']
    
    metrikler = [
        f"Drone\nIletilen: {toplam_d_paket}\nAktif: {d_aktif}/{len(d_sensorler)}\nOrt.Enerji: {drone_sonuclari['ortalama_enerji']:.1f}%",
        f"Multi-hop\nIletilen: {toplam_m_paket}\nAktif: {m_aktif}/{len(m_sensorler)}\nOrt.Enerji: {multihop_sonuclari['ortalama_enerji']:.1f}%",
    ]
    
    # Radar benzeri karşılaştırma (basit bar chart)
    karsilastirma = {
        'Enerji Verimi': [drone_sonuclari['ortalama_enerji'], multihop_sonuclari['ortalama_enerji']],
        'Aktif Oran (%)': [d_aktif/len(d_sensorler)*100, m_aktif/len(m_sensorler)*100],
        'Paket Teslim': [min(toplam_d_paket / max(toplam_m_paket, 1) * 100, 200), 100],
    }
    
    labels = list(karsilastirma.keys())
    drone_vals = [v[0] for v in karsilastirma.values()]
    mhop_vals = [v[1] for v in karsilastirma.values()]
    
    x_k = np.arange(len(labels))
    ax4.barh(x_k - 0.2, drone_vals, 0.35, label='Drone', color='#3498db', alpha=0.8)
    ax4.barh(x_k + 0.2, mhop_vals, 0.35, label='Multi-hop', color='#e74c3c', alpha=0.8)
    
    ax4.set_yticks(x_k)
    ax4.set_yticklabels(labels, fontsize=10)
    ax4.set_xlabel('Deger (%)', fontsize=10)
    ax4.set_title('Performans Karsilastirmasi', fontsize=11, fontweight='bold')
    ax4.legend(fontsize=9)
    ax4.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    if kaydet:
        plt.savefig(f'{CIKTI_KLASORU}/6_bellek_paket_analizi.png', bbox_inches='tight')
    plt.close()
    print(f"  [OK] Grafik 6: Bellek ve Paket Analizi kaydedildi.")


def grafik7_multihop_topoloji(multihop_sonuclari: dict, kaydet=True):
    """
    Grafik 7: Multi-hop ağ topolojisi ve yönlendirme bağlantıları.
    """
    klasor_olustur()
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    
    sensorler = multihop_sonuclari['sensorler']
    yonlendirme = multihop_sonuclari['yonlendirme']
    baz = multihop_sonuclari['baz_istasyonu']
    
    # Tarla
    tarla = plt.Rectangle((0, 0), ALAN_GENISLIK, ALAN_YUKSEKLIK, 
                           fill=True, facecolor='#f0f8e8', 
                           edgecolor='#2d5016', linewidth=2, alpha=0.5)
    ax.add_patch(tarla)
    
    # Yönlendirme bağlantılarını çiz
    for sensor in sensorler:
        if sensor.id in yonlendirme:
            yon = yonlendirme[sensor.id]
            if yon['sonraki_hop'] is not None:
                # Komşu sensöre bağlantı
                komsu = next((s for s in sensorler if s.id == yon['sonraki_hop']), None)
                if komsu:
                    ax.plot([sensor.konum[0], komsu.konum[0]], 
                           [sensor.konum[1], komsu.konum[1]], 
                           '-', color='orange', linewidth=0.8, alpha=0.5, zorder=2)
            else:
                # Doğrudan baz istasyonuna
                ax.plot([sensor.konum[0], baz[0]], 
                       [sensor.konum[1], baz[1]], 
                       '-', color='red', linewidth=0.5, alpha=0.3, zorder=2)
    
    # Sensörler
    for sensor in sensorler:
        renk = RENK_SENSOR_AKTIF if sensor.aktif else RENK_SENSOR_OLU
        if sensor.aktif and sensor.enerji_yuzdesi < 30:
            renk = RENK_SENSOR_DUSUK
        
        ax.scatter(sensor.konum[0], sensor.konum[1], c=renk, s=60, 
                   edgecolors='black', linewidth=0.5, zorder=5)
        ax.annotate(f'S{sensor.id}\n{sensor.enerji_yuzdesi:.0f}%', 
                   (sensor.konum[0]+5, sensor.konum[1]+5),
                   fontsize=6, color='gray')
    
    # Baz istasyonu
    ax.scatter(baz[0], baz[1], c=RENK_BAZ_ISTASYONU, marker='s', s=300, 
               zorder=10, edgecolors='black', linewidth=2, label='Baz Istasyonu')
    ax.annotate('BAZ\nISTASYONU', (baz[0]+10, baz[1]+10),
                fontsize=10, fontweight='bold', color=RENK_BAZ_ISTASYONU)
    
    legend_elements = [
        mpatches.Patch(color=RENK_SENSOR_AKTIF, label='Aktif Sensor'),
        mpatches.Patch(color=RENK_SENSOR_DUSUK, label='Dusuk Enerji'),
        mpatches.Patch(color=RENK_SENSOR_OLU, label='Olu Sensor'),
        plt.Line2D([0], [0], color='orange', linewidth=2, label='Multi-hop Baglanti'),
        plt.Line2D([0], [0], color='red', linewidth=2, alpha=0.5, label='Direkt Baglanti'),
        plt.Line2D([0], [0], marker='s', color='w', markerfacecolor=RENK_BAZ_ISTASYONU, 
                   markersize=12, label='Baz Istasyonu'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9)
    
    ax.set_xlim(-20, ALAN_GENISLIK + 20)
    ax.set_ylim(-20, ALAN_YUKSEKLIK + 80)
    ax.set_xlabel('X (metre)', fontsize=11)
    ax.set_ylabel('Y (metre)', fontsize=11)
    ax.set_title('Multi-hop Ag Topolojisi ve Yonlendirme', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    
    plt.tight_layout()
    if kaydet:
        plt.savefig(f'{CIKTI_KLASORU}/7_multihop_topoloji.png', bbox_inches='tight')
    plt.close()
    print(f"  [OK] Grafik 7: Multi-hop Topoloji kaydedildi.")


def tum_grafikleri_olustur(drone_sonuclari: dict, multihop_sonuclari: dict, 
                             enerji_log: list):
    """Tüm grafikleri oluşturur ve kaydeder."""
    print("\n" + "=" * 60)
    print("  GRAFİKLER OLUŞTURULUYOR...")
    print("=" * 60)
    
    grafik1_ag_topolojisi_ve_rota(drone_sonuclari)
    grafik2_enerji_karsilastirma(drone_sonuclari, multihop_sonuclari)
    grafik3_enerji_isi_haritasi(drone_sonuclari, multihop_sonuclari)
    grafik4_zaman_serisi(enerji_log)
    grafik5_drone_rota_detay(drone_sonuclari)
    grafik6_bellek_ve_paket(drone_sonuclari, multihop_sonuclari)
    grafik7_multihop_topoloji(multihop_sonuclari)
    
    print(f"\n  Tüm grafikler '{CIKTI_KLASORU}/' klasörüne kaydedildi.")
    print("=" * 60)
