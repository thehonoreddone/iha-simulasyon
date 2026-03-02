"""
=============================================================================
 Tarım 5.0: Drone Rota Optimizasyonu (Trajectory Optimization)
 
 Yöntemler:
   1. En Yakın Komşu (Nearest Neighbor) - Başlangıç çözümü
   2. 2-Opt İyileştirme - Yerel arama ile rota iyileştirme
   3. Kümeleme Tabanlı Rota - K-means ile bölge bazlı optimizasyon
   
 Amaç: Tüm sensörlerden minimum mesafe ile veri toplamak
        (Gezgin Satıcı Problemi - TSP benzeri)
=============================================================================
"""

import numpy as np
from typing import List, Tuple


def mesafe_matrisi_olustur(
    noktalar: List[np.ndarray], 
    baslangic: np.ndarray
) -> np.ndarray:
    """
    Tüm noktalar arası mesafe matrisini oluşturur.
    İlk nokta (indeks 0) başlangıç/bitiş noktasıdır.
    
    Parameters
    ----------
    noktalar : list
        Sensör konumları [np.ndarray]
    baslangic : np.ndarray
        Drone başlangıç noktası
    
    Returns
    -------
    np.ndarray
        Mesafe matrisi (n+1 x n+1)
    """
    tum_noktalar = [baslangic] + noktalar
    n = len(tum_noktalar)
    matris = np.zeros((n, n))
    
    for i in range(n):
        for j in range(i + 1, n):
            d = np.linalg.norm(tum_noktalar[i] - tum_noktalar[j])
            matris[i][j] = d
            matris[j][i] = d
    
    return matris


def rota_mesafesi(rota: List[int], mesafe_mat: np.ndarray) -> float:
    """
    Rotanın toplam mesafesini hesaplar.
    
    Parameters
    ----------
    rota : list
        Düğüm indeksleri sırası
    mesafe_mat : np.ndarray
        Mesafe matrisi
    
    Returns
    -------
    float
        Toplam mesafe
    """
    toplam = 0.0
    for i in range(len(rota) - 1):
        toplam += mesafe_mat[rota[i]][rota[i + 1]]
    return toplam


def en_yakin_komsu(mesafe_mat: np.ndarray) -> List[int]:
    """
    En Yakın Komşu (Nearest Neighbor) algoritması.
    Greedy yaklaşımla başlangıç çözümü üretir.
    
    Parameters
    ----------
    mesafe_mat : np.ndarray
        Mesafe matrisi (0. indeks = başlangıç)
    
    Returns
    -------
    list
        Rota (düğüm indeksleri)
    """
    n = mesafe_mat.shape[0]
    ziyaret_edildi = [False] * n
    rota = [0]  # Başlangıçtan başla
    ziyaret_edildi[0] = True
    
    for _ in range(n - 1):
        mevcut = rota[-1]
        en_yakin = -1
        en_kisa = float('inf')
        
        for j in range(n):
            if not ziyaret_edildi[j] and mesafe_mat[mevcut][j] < en_kisa:
                en_kisa = mesafe_mat[mevcut][j]
                en_yakin = j
        
        if en_yakin != -1:
            rota.append(en_yakin)
            ziyaret_edildi[en_yakin] = True
    
    rota.append(0)  # Başlangıca dön
    return rota


def iki_opt_iyilestirme(
    rota: List[int], 
    mesafe_mat: np.ndarray,
    max_iterasyon: int = 1000
) -> Tuple[List[int], float]:
    """
    2-Opt yerel arama ile rota iyileştirme.
    İki kenarı değiştirerek kısaltma arar.
    
    Parameters
    ----------
    rota : list
        Başlangıç rotası
    mesafe_mat : np.ndarray
        Mesafe matrisi
    max_iterasyon : int
        Maksimum iterasyon sayısı
    
    Returns
    -------
    tuple
        (İyileştirilmiş rota, toplam mesafe)
    """
    en_iyi_rota = rota.copy()
    en_iyi_mesafe = rota_mesafesi(en_iyi_rota, mesafe_mat)
    iyilesti = True
    iterasyon = 0
    
    while iyilesti and iterasyon < max_iterasyon:
        iyilesti = False
        iterasyon += 1
        
        for i in range(1, len(en_iyi_rota) - 2):
            for j in range(i + 1, len(en_iyi_rota) - 1):
                # 2-opt swap: i ile j arasını ters çevir
                yeni_rota = (
                    en_iyi_rota[:i] + 
                    en_iyi_rota[i:j+1][::-1] + 
                    en_iyi_rota[j+1:]
                )
                yeni_mesafe = rota_mesafesi(yeni_rota, mesafe_mat)
                
                if yeni_mesafe < en_iyi_mesafe:
                    en_iyi_rota = yeni_rota
                    en_iyi_mesafe = yeni_mesafe
                    iyilesti = True
    
    return en_iyi_rota, en_iyi_mesafe


def kumeleme_rotasi(
    sensor_konumlari: List[np.ndarray],
    baslangic: np.ndarray,
    kume_sayisi: int = 5
) -> List[np.ndarray]:
    """
    K-means kümeleme ile bölge bazlı rota optimizasyonu.
    Sensörleri kümelere ayırır, her kümenin merkezini ziyaret rotasına ekler,
    sonra 2-opt ile optimize eder.
    
    Parameters
    ----------
    sensor_konumlari : list
        Sensör konumları
    baslangic : np.ndarray
        Başlangıç noktası
    kume_sayisi : int
        Küme sayısı
    
    Returns
    -------
    list
        Optimize edilmiş rota (koordinat listesi)
    """
    from scipy.cluster.vq import kmeans2
    
    konumlar = np.array(sensor_konumlari)
    merkezler, etiketler = kmeans2(konumlar, kume_sayisi, minit='points')
    
    # Her kümedeki sensörleri düzenle
    kumeler = {}
    for i, etiket in enumerate(etiketler):
        if etiket not in kumeler:
            kumeler[etiket] = []
        kumeler[etiket].append(sensor_konumlari[i])
    
    # Küme merkezlerini ziyaret rotası olarak kullan
    merkez_listesi = [merkezler[i] for i in range(len(merkezler))]
    
    # Mesafe matrisi ve 2-opt optimize
    mesafe_mat = mesafe_matrisi_olustur(merkez_listesi, baslangic)
    ilk_rota = en_yakin_komsu(mesafe_mat)
    optimized_rota, _ = iki_opt_iyilestirme(ilk_rota, mesafe_mat)
    
    # Küme merkezleri rotasını koordinatlara çevir
    tum_noktalar = [baslangic] + merkez_listesi
    sonuc_rota = [tum_noktalar[i] for i in optimized_rota]
    
    return sonuc_rota


def rota_optimize_et(
    sensor_konumlari: List[np.ndarray],
    baslangic: np.ndarray,
    yontem: str = "2-opt"
) -> Tuple[List[np.ndarray], float]:
    """
    Ana rota optimizasyon fonksiyonu.
    
    Parameters
    ----------
    sensor_konumlari : list
        Sensör [x, y] konumları listesi
    baslangic : np.ndarray
        Drone başlangıç noktası
    yontem : str
        Optimizasyon yöntemi: "nearest", "2-opt", "cluster"
    
    Returns
    -------
    tuple
        (Rota koordinat listesi, toplam mesafe)
    """
    print(f"\n  Rota optimizasyonu başlatılıyor... (Yöntem: {yontem})")
    print(f"  Sensör sayısı: {len(sensor_konumlari)}")
    
    # Mesafe matrisi oluştur
    mesafe_mat = mesafe_matrisi_olustur(sensor_konumlari, baslangic)
    
    if yontem == "nearest":
        rota_indeks = en_yakin_komsu(mesafe_mat)
        toplam_mesafe = rota_mesafesi(rota_indeks, mesafe_mat)
        
    elif yontem == "2-opt":
        ilk_rota = en_yakin_komsu(mesafe_mat)
        ilk_mesafe = rota_mesafesi(ilk_rota, mesafe_mat)
        rota_indeks, toplam_mesafe = iki_opt_iyilestirme(ilk_rota, mesafe_mat)
        iyilesme = (1 - toplam_mesafe / ilk_mesafe) * 100
        print(f"  2-Opt İyileşme: %{iyilesme:.1f} ({ilk_mesafe:.0f}m -> {toplam_mesafe:.0f}m)")
        
    elif yontem == "cluster":
        koordinat_rota = kumeleme_rotasi(sensor_konumlari, baslangic)
        toplam_mesafe = sum(
            np.linalg.norm(koordinat_rota[i+1] - koordinat_rota[i]) 
            for i in range(len(koordinat_rota) - 1)
        )
        print(f"  Kümeleme Rota Mesafesi: {toplam_mesafe:.0f} m")
        return koordinat_rota, toplam_mesafe
    else:
        raise ValueError(f"Bilinmeyen yöntem: {yontem}")
    
    # İndeksleri koordinatlara çevir
    tum_noktalar = [baslangic] + sensor_konumlari
    rota_koordinat = [tum_noktalar[i] for i in rota_indeks]
    
    print(f"  Optimize edilmiş rota mesafesi: {toplam_mesafe:.0f} m")
    
    return rota_koordinat, toplam_mesafe


if __name__ == "__main__":
    # Test
    np.random.seed(42)
    
    baslangic = np.array([0.0, 0.0])
    sensorler = [np.random.uniform(20, 480, size=2) for _ in range(20)]
    
    for yontem in ["nearest", "2-opt"]:
        rota, mesafe = rota_optimize_et(sensorler, baslangic, yontem)
        print(f"  {yontem}: {mesafe:.0f} m, {len(rota)} nokta\n")
