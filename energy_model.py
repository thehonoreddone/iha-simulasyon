"""
=============================================================================
 Tarım 5.0: Enerji Tüketim Modeli
 First Order Radio Model (Heinzelman et al.)
=============================================================================
 TX Enerjisi: E_tx = E_elec * k + E_amp * k * d^n
 RX Enerjisi: E_rx = E_elec * k
 
 Burada:
   k   = paket boyutu (bit)
   d   = mesafe (metre)
   n   = yol kayıp üssü (2: serbest alan, 4: çok yollu)
=============================================================================
"""

import numpy as np
from config import (
    E_ELEC, E_FS, E_MP, E_DA, D_CROSSOVER, VERI_PAKET_BOYUTU
)


def iletim_enerjisi(paket_boyutu: int, mesafe: float) -> float:
    """
    Veri iletim enerjisini hesaplar (Joule).
    
    Parameters
    ----------
    paket_boyutu : int
        İletilecek veri boyutu (bit)
    mesafe : float
        İletim mesafesi (metre)
    
    Returns
    -------
    float
        Harcanan enerji (Joule)
    """
    if mesafe <= 0:
        return E_ELEC * paket_boyutu
    
    if mesafe < D_CROSSOVER:
        # Serbest alan modeli (d^2)
        enerji = E_ELEC * paket_boyutu + E_FS * paket_boyutu * (mesafe ** 2)
    else:
        # Çok yollu kayıp modeli (d^4)
        enerji = E_ELEC * paket_boyutu + E_MP * paket_boyutu * (mesafe ** 4)
    
    return enerji


def alim_enerjisi(paket_boyutu: int) -> float:
    """
    Veri alma enerjisini hesaplar (Joule).
    
    Parameters
    ----------
    paket_boyutu : int
        Alınan veri boyutu (bit)
    
    Returns
    -------
    float
        Harcanan enerji (Joule)
    """
    return E_ELEC * paket_boyutu


def veri_birlestirme_enerjisi(paket_boyutu: int) -> float:
    """
    Veri birleştirme (data aggregation) enerjisini hesaplar.
    
    Parameters
    ----------
    paket_boyutu : int
        İşlenen veri boyutu (bit)
    
    Returns
    -------
    float
        Harcanan enerji (Joule)
    """
    return E_DA * paket_boyutu


def algilama_enerjisi(paket_boyutu: int) -> float:
    """
    Sensörün veri algılama/ölçüm enerjisi (sensing).
    Genellikle çok küçüktür ama modelde yer alır.
    
    Parameters
    ----------
    paket_boyutu : int
        Algılanan veri boyutu (bit)
    
    Returns
    -------
    float
        Harcanan enerji (Joule)
    """
    return 5e-9 * paket_boyutu  # ~5 nJ/bit


def mesafe_hesapla(konum1: np.ndarray, konum2: np.ndarray, 
                    yukseklik_farki: float = 0.0) -> float:
    """
    İki nokta arasındaki 3D mesafeyi hesaplar.
    
    Parameters
    ----------
    konum1 : np.ndarray
        Birinci nokta [x, y]
    konum2 : np.ndarray
        İkinci nokta [x, y]
    yukseklik_farki : float
        Yükseklik farkı (metre)
    
    Returns
    -------
    float
        3D mesafe (metre)
    """
    yatay_mesafe = np.linalg.norm(konum1 - konum2)
    return np.sqrt(yatay_mesafe**2 + yukseklik_farki**2)


def toplam_iletim_enerjisi_multi_hop(
    paket_boyutu: int, 
    hop_mesafeleri: list
) -> float:
    """
    Multi-hop iletimde toplam enerji tüketimini hesaplar.
    Her hop'ta TX + RX + veri birleştirme enerjisi harcanır.
    
    Parameters
    ----------
    paket_boyutu : int
        Paket boyutu (bit)
    hop_mesafeleri : list
        Her hop'un mesafesi (metre listesi)
    
    Returns
    -------
    float
        Toplam enerji tüketimi (Joule)
    """
    toplam = 0.0
    for mesafe in hop_mesafeleri:
        toplam += iletim_enerjisi(paket_boyutu, mesafe)
        toplam += alim_enerjisi(paket_boyutu)
        toplam += veri_birlestirme_enerjisi(paket_boyutu)
    return toplam


def enerji_raporu(mesafe: float, paket_boyutu: int = VERI_PAKET_BOYUTU):
    """Belirli bir mesafe için enerji tüketim raporu yazdırır."""
    e_tx = iletim_enerjisi(paket_boyutu, mesafe)
    e_rx = alim_enerjisi(paket_boyutu)
    e_sense = algilama_enerjisi(paket_boyutu)
    
    print(f"  Mesafe: {mesafe:.1f} m")
    print(f"  Paket Boyutu: {paket_boyutu} bit")
    print(f"  TX Enerji: {e_tx*1e6:.4f} µJ")
    print(f"  RX Enerji: {e_rx*1e6:.4f} µJ")
    print(f"  Algılama Enerji: {e_sense*1e6:.4f} µJ")
    print(f"  Toplam: {(e_tx + e_rx + e_sense)*1e6:.4f} µJ")


if __name__ == "__main__":
    print("=" * 50)
    print("ENERJİ MODELİ TEST")
    print("=" * 50)
    
    for d in [10, 30, 50, 87, 100, 150]:
        print(f"\n--- Mesafe: {d} m ---")
        enerji_raporu(d)
