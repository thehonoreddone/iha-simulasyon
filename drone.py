"""
=============================================================================
 Tarım 5.0: Drone / İHA Modeli (Mobil Baz İstasyonu - Data Mule)
 
 Drone:
   - Optimize edilmiş rotada uçar
   - Sensörlerin iletişim menzili içine girdiğinde durur
   - Veri toplar ve baz istasyonuna getirir
   - 3D konum takibi (x, y, yükseklik)
=============================================================================
"""

import numpy as np
from config import (
    DRONE_HIZ, DRONE_YUKSEKLIK, DRONE_ILETISIM_MENZIL,
    DRONE_BASLANGIC_NOKTASI, DRONE_BEKLEME_SURESI
)
from energy_model import mesafe_hesapla


class Drone:
    """
    Mobil Baz İstasyonu (Drone / İHA) sınıfı.
    
    Attributes
    ----------
    konum : np.ndarray
        Mevcut [x, y] koordinatları
    yukseklik : float
        Uçuş yüksekliği (metre)
    hiz : float
        Uçuş hızı (m/s)
    menzil : float
        İletişim menzili (metre)
    """
    
    def __init__(self, baslangic: np.ndarray = None):
        self.konum = baslangic.copy() if baslangic is not None else DRONE_BASLANGIC_NOKTASI.copy()
        self.baslangic_konum = self.konum.copy()
        self.yukseklik = DRONE_YUKSEKLIK
        self.hiz = DRONE_HIZ
        self.menzil = DRONE_ILETISIM_MENZIL
        self.bekleme_suresi = DRONE_BEKLEME_SURESI
        
        # Rota bilgisi
        self.rota = []              # Ziyaret edilecek noktalar listesi
        self.rota_indeks = 0        # Rotadaki mevcut nokta indeksi
        self.rota_tamamlandi = False
        
        # Toplama istatistikleri
        self.toplanan_paketler = []
        self.toplam_ucus_mesafesi = 0.0
        self.toplam_ucus_suresi = 0.0
        self.toplam_bekleme_suresi = 0.0
        self.tur_sayisi = 0
        
        # Pozisyon geçmişi (görselleştirme için)
        self.pozisyon_gecmisi = []
        self.toplama_noktalari = []  # (zaman, konum, paket_sayisi)
    
    def rota_belirle(self, rota_noktalari: list):
        """
        Drone'un izleyeceği rotayı belirler.
        
        Parameters
        ----------
        rota_noktalari : list
            np.ndarray koordinat listesi [x, y]
        """
        self.rota = rota_noktalari
        self.rota_indeks = 0
        self.rota_tamamlandi = False
    
    def sonraki_hedef(self) -> np.ndarray:
        """
        Rotadaki bir sonraki hedef noktasını döndürür.
        
        Returns
        -------
        np.ndarray or None
            Hedef koordinat veya None (rota tamamlandıysa)
        """
        if self.rota_indeks < len(self.rota):
            return self.rota[self.rota_indeks]
        return None
    
    def hedefe_git(self, hedef: np.ndarray) -> float:
        """
        Hedefe hareket eder. Süreyi döndürür.
        
        Parameters
        ----------
        hedef : np.ndarray
            Hedef [x, y] koordinatları
        
        Returns
        -------
        float
            Uçuş süresi (saniye)
        """
        mesafe = np.linalg.norm(hedef - self.konum)
        sure = mesafe / self.hiz
        
        # Pozisyon geçmişine kaydet
        self.pozisyon_gecmisi.append(self.konum.copy())
        
        # Güncelle
        self.konum = hedef.copy()
        self.toplam_ucus_mesafesi += mesafe
        self.toplam_ucus_suresi += sure
        
        return sure
    
    def menzilde_mi(self, sensor_konum: np.ndarray) -> bool:
        """
        Sensörün iletişim menzilinde olup olmadığını kontrol eder.
        3D mesafe kullanır (yükseklik dahil).
        
        Parameters
        ----------
        sensor_konum : np.ndarray
            Sensör [x, y] koordinatları
        
        Returns
        -------
        bool
            Menzilde mi
        """
        mesafe_3d = mesafe_hesapla(self.konum, sensor_konum, self.yukseklik)
        return mesafe_3d <= self.menzil
    
    def veri_topla(self, sensor, zaman: float) -> int:
        """
        Menzildeki sensörden veri toplar.
        
        Parameters
        ----------
        sensor : SensorDugum
            Veri toplanacak sensör
        zaman : float
            Simülasyon zamanı
        
        Returns
        -------
        int
            Toplanan paket sayısı
        """
        if not self.menzilde_mi(sensor.konum):
            return 0
        
        paketler = sensor.veri_ilet(self.konum, zaman)
        self.toplanan_paketler.extend(paketler)
        
        if paketler:
            self.toplama_noktalari.append((zaman, self.konum.copy(), len(paketler)))
        
        return len(paketler)
    
    def tura_basla(self):
        """Yeni tur başlatır."""
        self.rota_indeks = 0
        self.rota_tamamlandi = False
        self.tur_sayisi += 1
    
    def tur_tamamla(self) -> float:
        """
        Başlangıç noktasına geri dön.
        
        Returns
        -------
        float
            Dönüş süresi (saniye)
        """
        sure = self.hedefe_git(self.baslangic_konum)
        self.pozisyon_gecmisi.append(self.konum.copy())
        self.rota_tamamlandi = True
        return sure
    
    def istatistik_raporu(self):
        """Drone istatistik raporu yazdırır."""
        print(f"\n{'='*50}")
        print(f"  DRONE İSTATİSTİK RAPORU")
        print(f"{'='*50}")
        print(f"  Toplam Tur Sayısı    : {self.tur_sayisi}")
        print(f"  Toplam Uçuş Mesafesi : {self.toplam_ucus_mesafesi:.1f} m")
        print(f"  Toplam Uçuş Süresi   : {self.toplam_ucus_suresi:.1f} s")
        print(f"  Toplam Bekleme Süresi : {self.toplam_bekleme_suresi:.1f} s")
        print(f"  Toplanan Paket Sayısı : {len(self.toplanan_paketler)}")
        if self.tur_sayisi > 0:
            print(f"  Ort. Tur Mesafesi    : {self.toplam_ucus_mesafesi/self.tur_sayisi:.1f} m")
            print(f"  Ort. Tur Süresi      : {(self.toplam_ucus_suresi+self.toplam_bekleme_suresi)/self.tur_sayisi:.1f} s")
    
    def __repr__(self):
        return (f"Drone @ ({self.konum[0]:.1f}, {self.konum[1]:.1f}, {self.yukseklik:.0f}m) "
                f"| Toplanan: {len(self.toplanan_paketler)} paket "
                f"| Mesafe: {self.toplam_ucus_mesafesi:.0f}m")
