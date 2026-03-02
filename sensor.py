"""
=============================================================================
 Tarım 5.0: Sensör Düğüm Modeli
 Her sensör düğüm:
   - Periyodik veri üretir (sıcaklık, nem, toprak nemi)
   - Veriyi belleğinde saklar (buffer)
   - Drone yaklaştığında veriyi iletir
   - Enerji tüketimini izler
=============================================================================
"""

import numpy as np
from energy_model import (
    iletim_enerjisi, algilama_enerjisi, mesafe_hesapla
)
from config import (
    SENSOR_BASLANGIC_ENERJI, SENSOR_BELLEK_KAPASITESI,
    VERI_PAKET_BOYUTU, VERI_URETIM_ARALIGI, DRONE_YUKSEKLIK
)


class SensorDugum:
    """
    Kablosuz sensör düğüm sınıfı.
    
    Attributes
    ----------
    id : int
        Düğüm kimliği
    konum : np.ndarray
        [x, y] koordinatları (metre)
    enerji : float
        Kalan enerji (Joule)
    bellek : list
        Veri tamponu (saklanmış paketler)
    aktif : bool
        Düğüm aktif mi (enerji > 0)
    """
    
    def __init__(self, dugum_id: int, x: float, y: float,
                 baslangic_enerji: float = SENSOR_BASLANGIC_ENERJI):
        self.id = dugum_id
        self.konum = np.array([x, y])
        self.baslangic_enerji = baslangic_enerji
        self.enerji = baslangic_enerji
        self.bellek = []
        self.bellek_kapasitesi = SENSOR_BELLEK_KAPASITESI
        self.aktif = True
        
        # İstatistikler
        self.toplam_uretilen_paket = 0
        self.toplam_iletilen_paket = 0
        self.toplam_kaybedilen_paket = 0  # Bellek taşması
        self.toplam_harcanan_enerji = 0.0
        self.enerji_gecmisi = []  # (zaman, enerji) listesi
        self.iletim_gecmisi = []  # (zaman, paket_sayisi) listesi
        
    def veri_uret(self, zaman: float) -> bool:
        """
        Yeni bir sensör verisi üretir ve belleğe ekler.
        
        Parameters
        ----------
        zaman : float
            Simülasyon zamanı (saniye)
        
        Returns
        -------
        bool
            Başarılı mı
        """
        if not self.aktif:
            return False
        
        # Algılama enerjisi harca
        e_sense = algilama_enerjisi(VERI_PAKET_BOYUTU)
        if self.enerji < e_sense:
            self.aktif = False
            return False
        
        self.enerji -= e_sense
        self.toplam_harcanan_enerji += e_sense
        
        # Veri paketi oluştur
        paket = {
            'sensor_id': self.id,
            'zaman': zaman,
            'boyut': VERI_PAKET_BOYUTU,
            'veri': {
                'sicaklik': np.random.uniform(15, 40),     # °C
                'nem': np.random.uniform(30, 90),           # %
                'toprak_nemi': np.random.uniform(10, 80),   # %
            }
        }
        
        self.toplam_uretilen_paket += 1
        
        # Bellek kontrolü
        if len(self.bellek) >= self.bellek_kapasitesi:
            # En eski veriyi sil (FIFO)
            self.bellek.pop(0)
            self.toplam_kaybedilen_paket += 1
        
        self.bellek.append(paket)
        return True
    
    def veri_ilet(self, hedef_konum: np.ndarray, zaman: float) -> list:
        """
        Bellekteki tüm verileri hedefe (drone) iletir.
        
        Parameters
        ----------
        hedef_konum : np.ndarray
            Hedef [x, y] koordinatları
        zaman : float
            Simülasyon zamanı
        
        Returns
        -------
        list
            İletilen paketler listesi
        """
        if not self.aktif or len(self.bellek) == 0:
            return []
        
        # 3D mesafe (drone havada)
        mesafe = mesafe_hesapla(self.konum, hedef_konum, DRONE_YUKSEKLIK)
        
        # Toplam iletim enerjisi (tüm paketler için)
        paket_sayisi = len(self.bellek)
        toplam_boyut = paket_sayisi * VERI_PAKET_BOYUTU
        e_tx = iletim_enerjisi(toplam_boyut, mesafe)
        
        if self.enerji < e_tx:
            # Yeterli enerji yok - gönderebileceği kadar gönder
            kalan_enerji = self.enerji
            gonderilebilir = 0
            for i in range(paket_sayisi):
                e_tek = iletim_enerjisi(VERI_PAKET_BOYUTU, mesafe)
                if kalan_enerji >= e_tek:
                    kalan_enerji -= e_tek
                    gonderilebilir += 1
                else:
                    break
            
            if gonderilebilir == 0:
                return []
            
            iletilen = self.bellek[:gonderilebilir]
            self.bellek = self.bellek[gonderilebilir:]
            e_tx = self.enerji - kalan_enerji
        else:
            iletilen = self.bellek.copy()
            self.bellek = []
        
        # Enerji güncelle
        self.enerji -= e_tx
        self.toplam_harcanan_enerji += e_tx
        self.toplam_iletilen_paket += len(iletilen)
        
        # İstatistik kaydet
        self.iletim_gecmisi.append((zaman, len(iletilen)))
        
        # Enerji kontrolü
        if self.enerji <= 0:
            self.enerji = 0
            self.aktif = False
        
        return iletilen
    
    def multi_hop_ilet(self, mesafe: float, zaman: float) -> list:
        """
        Multi-hop senaryosu için - belirli mesafeye iletim yapar.
        Her veri üretildiğinde hemen gönderilir.
        
        Parameters
        ----------
        mesafe : float
            Bir sonraki hop'a mesafe
        zaman : float
            Simülasyon zamanı
        
        Returns
        -------
        list
            İletilen paketler
        """
        if not self.aktif or len(self.bellek) == 0:
            return []
        
        iletilen = []
        while self.bellek:
            paket = self.bellek[0]
            e_tx = iletim_enerjisi(VERI_PAKET_BOYUTU, mesafe)
            
            if self.enerji < e_tx:
                self.aktif = False
                break
            
            self.enerji -= e_tx
            self.toplam_harcanan_enerji += e_tx
            self.toplam_iletilen_paket += 1
            iletilen.append(self.bellek.pop(0))
        
        if self.enerji <= 0:
            self.enerji = 0
            self.aktif = False
        
        return iletilen
    
    def enerji_kaydet(self, zaman: float):
        """Enerji geçmişini kaydeder."""
        self.enerji_gecmisi.append((zaman, self.enerji))
    
    @property
    def enerji_yuzdesi(self) -> float:
        """Kalan enerji yüzdesi."""
        return (self.enerji / self.baslangic_enerji) * 100
    
    @property
    def bellek_doluluk(self) -> float:
        """Bellek doluluk oranı (%)."""
        return (len(self.bellek) / self.bellek_kapasitesi) * 100
    
    def __repr__(self):
        durum = "AKTİF" if self.aktif else "ÖLÜM"
        return (f"Sensör-{self.id:02d} [{durum}] "
                f"Konum=({self.konum[0]:.0f},{self.konum[1]:.0f}) "
                f"Enerji={self.enerji_yuzdesi:.1f}% "
                f"Bellek={len(self.bellek)}/{self.bellek_kapasitesi}")


def sensor_agi_olustur(
    sensor_sayisi: int, 
    alan_genislik: float, 
    alan_yukseklik: float,
    rastgele_tohum: int = 42
) -> list:
    """
    Rastgele konumlandırılmış sensör ağı oluşturur.
    
    Parameters
    ----------
    sensor_sayisi : int
        Toplam sensör sayısı
    alan_genislik : float
        Alan genişliği (metre)
    alan_yukseklik : float
        Alan yüksekliği (metre)
    rastgele_tohum : int
        Rastgele sayı üreteci tohumu
    
    Returns
    -------
    list
        SensorDugum nesneleri listesi
    """
    np.random.seed(rastgele_tohum)
    
    sensorler = []
    for i in range(sensor_sayisi):
        x = np.random.uniform(20, alan_genislik - 20)
        y = np.random.uniform(20, alan_yukseklik - 20)
        sensor = SensorDugum(dugum_id=i, x=x, y=y)
        sensorler.append(sensor)
    
    return sensorler


if __name__ == "__main__":
    from config import SENSOR_SAYISI, ALAN_GENISLIK, ALAN_YUKSEKLIK
    
    print("=" * 60)
    print("SENSÖR AĞI TESTİ")
    print("=" * 60)
    
    sensorler = sensor_agi_olustur(
        SENSOR_SAYISI, ALAN_GENISLIK, ALAN_YUKSEKLIK
    )
    
    for s in sensorler[:5]:
        print(s)
        s.veri_uret(0)
        print(f"  -> Veri üretildi. Bellek: {len(s.bellek)} paket")
