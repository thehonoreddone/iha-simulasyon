"""
=============================================================================
 Tarım 5.0: SimPy Tabanlı Ayrık Olay Simülasyonu
 
 Simülasyon Bileşenleri:
   1. Sensör Veri Üretim Süreci
   2. Drone Tur Süreci (Mobil Baz İstasyonu)
   3. Multi-hop Karşılaştırma Süreci
   4. Enerji İzleme Süreci
=============================================================================
"""

import simpy
import numpy as np
from typing import List, Dict, Tuple

from config import (
    SENSOR_SAYISI, ALAN_GENISLIK, ALAN_YUKSEKLIK,
    VERI_URETIM_ARALIGI, DRONE_TUR_ARALIGI,
    DRONE_BASLANGIC_NOKTASI, DRONE_BEKLEME_SURESI,
    SIMULASYON_SURESI, RASTGELE_TOHUM,
    BAZ_ISTASYONU_KONUM, MULTI_HOP_MENZIL
)
from sensor import SensorDugum, sensor_agi_olustur
from drone import Drone
from trajectory import rota_optimize_et
from energy_model import mesafe_hesapla


class TarimSimulasyonu:
    """
    Ana simülasyon sınıfı - SimPy tabanlı ayrık olay simülasyonu.
    
    İki senaryo simüle eder:
    1. Mobil Baz İstasyonu (Drone ile veri toplama)
    2. Statik Baz İstasyonu (Multi-hop ile veri iletimi)
    """
    
    def __init__(self, simulasyon_suresi: int = SIMULASYON_SURESI,
                 sensor_sayisi: int = SENSOR_SAYISI,
                 rastgele_tohum: int = RASTGELE_TOHUM):
        
        self.simulasyon_suresi = simulasyon_suresi
        self.sensor_sayisi = sensor_sayisi
        self.rastgele_tohum = rastgele_tohum
        
        # Sonuçlar
        self.drone_sonuclari = {}
        self.multihop_sonuclari = {}
        self.enerji_log = []
        
    def _sensor_veri_uretimi(self, env: simpy.Environment,
                              sensorler: List[SensorDugum]):
        """
        Sensör veri üretim süreci.
        Her VERI_URETIM_ARALIGI saniyede bir tüm sensörler veri üretir.
        """
        while True:
            yield env.timeout(VERI_URETIM_ARALIGI)
            
            aktif_sayisi = 0
            for sensor in sensorler:
                if sensor.veri_uret(env.now):
                    aktif_sayisi += 1
            
            # Enerji kaydı
            for sensor in sensorler:
                sensor.enerji_kaydet(env.now)
    
    def _drone_tur_sureci(self, env: simpy.Environment,
                           drone: Drone,
                           sensorler: List[SensorDugum]):
        """
        Drone tur süreci.
        Belirli aralıklarla optimize edilmiş rotada uçar ve veri toplar.
        """
        while True:
            # Tur aralığı bekle (ilk turda az bekle)
            if drone.tur_sayisi > 0:
                yield env.timeout(DRONE_TUR_ARALIGI)
            else:
                yield env.timeout(30)  # İlk tur 30 sn sonra
            
            if env.now >= self.simulasyon_suresi:
                break
            
            # Aktif sensör konumlarını al
            aktif_sensorler = [s for s in sensorler if s.aktif]
            if not aktif_sensorler:
                print(f"  [t={env.now:.0f}s] Tüm sensörler öldü! Drone durduruluyor.")
                break
            
            # Veri olan sensörleri öncelikle ziyaret et
            ziyaret_listesi = [s for s in aktif_sensorler if len(s.bellek) > 0]
            if not ziyaret_listesi:
                ziyaret_listesi = aktif_sensorler
            
            sensor_konumlari = [s.konum for s in ziyaret_listesi]
            
            # Rota optimize et
            rota, _ = rota_optimize_et(
                sensor_konumlari, 
                drone.baslangic_konum, 
                yontem="2-opt"
            )
            
            drone.rota_belirle(rota[1:])  # İlk nokta başlangıç
            drone.tura_basla()
            
            tur_baslangic = env.now
            tur_paket = 0
            
            print(f"\n  [t={env.now:.0f}s] === DRONE TUR #{drone.tur_sayisi} BAŞLADI ===")
            print(f"  Ziyaret edilecek sensör: {len(ziyaret_listesi)}")
            
            # Rotadaki her noktayı ziyaret et
            for hedef in rota[1:]:
                if env.now >= self.simulasyon_suresi:
                    break
                
                # Hedefe uç
                ucus_suresi = drone.hedefe_git(hedef)
                yield env.timeout(ucus_suresi)
                
                # Menzildeki sensörlerden veri topla
                for sensor in sensorler:
                    if sensor.aktif and drone.menzilde_mi(sensor.konum):
                        paket_sayisi = drone.veri_topla(sensor, env.now)
                        tur_paket += paket_sayisi
                
                # Bekleme süresi
                yield env.timeout(DRONE_BEKLEME_SURESI)
                drone.toplam_bekleme_suresi += DRONE_BEKLEME_SURESI
            
            tur_suresi = env.now - tur_baslangic
            print(f"  [t={env.now:.0f}s] === TUR #{drone.tur_sayisi} TAMAMLANDI ===")
            print(f"  Süre: {tur_suresi:.0f}s | Toplanan paket: {tur_paket}")
            print(f"  Aktif sensör: {sum(1 for s in sensorler if s.aktif)}/{len(sensorler)}")
    
    def _enerji_izleme(self, env: simpy.Environment,
                        sensorler: List[SensorDugum],
                        etiket: str):
        """
        Periyodik enerji izleme süreci.
        """
        kayit_araligi = 60  # Her 60 saniyede bir kayıt
        
        while True:
            yield env.timeout(kayit_araligi)
            
            aktif = sum(1 for s in sensorler if s.aktif)
            ort_enerji = np.mean([s.enerji_yuzdesi for s in sensorler])
            min_enerji = min(s.enerji_yuzdesi for s in sensorler)
            
            self.enerji_log.append({
                'zaman': env.now,
                'senaryo': etiket,
                'aktif_sensor': aktif,
                'ortalama_enerji': ort_enerji,
                'minimum_enerji': min_enerji
            })
    
    def drone_simulasyonu_calistir(self) -> Dict:
        """
        Mobil Baz İstasyonu (Drone) simülasyonunu çalıştırır.
        
        Returns
        -------
        dict
            Simülasyon sonuçları
        """
        print("\n" + "=" * 60)
        print("  SENARYO 1: MOBİL BAZ İSTASYONU (DRONE)")
        print("=" * 60)
        
        np.random.seed(self.rastgele_tohum)
        
        # Sensör ağını oluştur
        sensorler = sensor_agi_olustur(
            self.sensor_sayisi, ALAN_GENISLIK, ALAN_YUKSEKLIK,
            self.rastgele_tohum
        )
        
        # Drone oluştur
        drone = Drone(DRONE_BASLANGIC_NOKTASI)
        
        # SimPy ortamı
        env = simpy.Environment()
        
        # Süreçleri başlat
        env.process(self._sensor_veri_uretimi(env, sensorler))
        env.process(self._drone_tur_sureci(env, drone, sensorler))
        env.process(self._enerji_izleme(env, sensorler, "Drone"))
        
        # Simülasyonu çalıştır
        print(f"\n  Simülasyon başlatılıyor ({self.simulasyon_suresi}s)...")
        env.run(until=self.simulasyon_suresi)
        
        # Sonuçları topla
        drone.istatistik_raporu()
        
        self.drone_sonuclari = {
            'sensorler': sensorler,
            'drone': drone,
            'toplam_paket': len(drone.toplanan_paketler),
            'aktif_sensor_sayisi': sum(1 for s in sensorler if s.aktif),
            'ortalama_enerji': np.mean([s.enerji_yuzdesi for s in sensorler]),
            'minimum_enerji': min(s.enerji_yuzdesi for s in sensorler),
            'enerji_dagilimi': [s.enerji_yuzdesi for s in sensorler],
            'olum_zamanlari': [],
            'sensor_konumlari': [s.konum.copy() for s in sensorler],
            'sensor_enerjileri': [s.enerji for s in sensorler],
        }
        
        # Detaylı rapor
        print(f"\n  --- SENSÖR AĞI DURUMU ---")
        print(f"  Aktif Sensör: {self.drone_sonuclari['aktif_sensor_sayisi']}/{self.sensor_sayisi}")
        print(f"  Ort. Kalan Enerji: %{self.drone_sonuclari['ortalama_enerji']:.1f}")
        print(f"  Min. Kalan Enerji: %{self.drone_sonuclari['minimum_enerji']:.1f}")
        
        return self.drone_sonuclari
    
    def multihop_simulasyonu_calistir(self) -> Dict:
        """
        Statik Baz İstasyonu (Multi-hop) simülasyonunu çalıştırır.
        Karşılaştırma için aynı sensör konumlarını kullanır.
        
        Returns
        -------
        dict
            Simülasyon sonuçları
        """
        print("\n" + "=" * 60)
        print("  SENARYO 2: SABİT BAZ İSTASYONU (MULTI-HOP)")
        print("=" * 60)
        
        np.random.seed(self.rastgele_tohum)
        
        # Aynı sensör ağını oluştur
        sensorler = sensor_agi_olustur(
            self.sensor_sayisi, ALAN_GENISLIK, ALAN_YUKSEKLIK,
            self.rastgele_tohum
        )
        
        # Yönlendirme tablosu oluştur (en kısa yol - greedy)
        yonlendirme = self._yonlendirme_tablosu_olustur(sensorler)
        
        # SimPy ortamı
        env = simpy.Environment()
        env.process(self._sensor_veri_uretimi(env, sensorler))
        env.process(self._multihop_iletim_sureci(env, sensorler, yonlendirme))
        env.process(self._enerji_izleme(env, sensorler, "Multi-hop"))
        
        print(f"\n  Simülasyon başlatılıyor ({self.simulasyon_suresi}s)...")
        env.run(until=self.simulasyon_suresi)
        
        # Sonuçları topla
        toplam_iletilen = sum(s.toplam_iletilen_paket for s in sensorler)
        
        self.multihop_sonuclari = {
            'sensorler': sensorler,
            'toplam_paket': toplam_iletilen,
            'aktif_sensor_sayisi': sum(1 for s in sensorler if s.aktif),
            'ortalama_enerji': np.mean([s.enerji_yuzdesi for s in sensorler]),
            'minimum_enerji': min(s.enerji_yuzdesi for s in sensorler),
            'enerji_dagilimi': [s.enerji_yuzdesi for s in sensorler],
            'sensor_konumlari': [s.konum.copy() for s in sensorler],
            'sensor_enerjileri': [s.enerji for s in sensorler],
            'yonlendirme': yonlendirme,
            'baz_istasyonu': BAZ_ISTASYONU_KONUM,
        }
        
        print(f"\n  --- SONUÇLAR ---")
        print(f"  Aktif Sensör: {self.multihop_sonuclari['aktif_sensor_sayisi']}/{self.sensor_sayisi}")
        print(f"  Toplam İletilen Paket: {toplam_iletilen}")
        print(f"  Ort. Kalan Enerji: %{self.multihop_sonuclari['ortalama_enerji']:.1f}")
        print(f"  Min. Kalan Enerji: %{self.multihop_sonuclari['minimum_enerji']:.1f}")
        
        return self.multihop_sonuclari
    
    def _yonlendirme_tablosu_olustur(
        self, sensorler: List[SensorDugum]
    ) -> Dict:
        """
        Greedy multi-hop yönlendirme tablosu.
        Her sensör, baz istasyonuna en yakın komşusu üzerinden veri gönderir.
        """
        yonlendirme = {}
        baz = BAZ_ISTASYONU_KONUM
        
        for sensor in sensorler:
            # Baz istasyonuna doğrudan mesafe
            direkt_mesafe = np.linalg.norm(sensor.konum - baz)
            
            if direkt_mesafe <= MULTI_HOP_MENZIL:
                # Doğrudan baz istasyonuna gönder
                yonlendirme[sensor.id] = {
                    'sonraki_hop': None,  # Doğrudan baz istasyonu
                    'mesafe': direkt_mesafe,
                    'hop_sayisi': 1
                }
            else:
                # En yakın komşuyu bul (baz istasyonuna daha yakın olan)
                en_yakin = None
                en_kisa = float('inf')
                
                for diger in sensorler:
                    if diger.id == sensor.id:
                        continue
                    
                    komsu_mesafe = np.linalg.norm(sensor.konum - diger.konum)
                    komsu_baz_mesafe = np.linalg.norm(diger.konum - baz)
                    
                    # Menzil içinde ve baz istasyonuna daha yakın olmalı
                    if (komsu_mesafe <= MULTI_HOP_MENZIL and 
                        komsu_baz_mesafe < direkt_mesafe and
                        komsu_mesafe < en_kisa):
                        en_yakin = diger.id
                        en_kisa = komsu_mesafe
                
                if en_yakin is not None:
                    yonlendirme[sensor.id] = {
                        'sonraki_hop': en_yakin,
                        'mesafe': en_kisa,
                        'hop_sayisi': 2  # Basitleştirme
                    }
                else:
                    # Ulaşılamayan düğüm - en yakın komşuya gönder
                    en_yakin_genel = None
                    en_kisa_genel = float('inf')
                    for diger in sensorler:
                        if diger.id == sensor.id:
                            continue
                        komsu_mesafe = np.linalg.norm(sensor.konum - diger.konum)
                        komsu_baz_mesafe = np.linalg.norm(diger.konum - baz)
                        if komsu_baz_mesafe < direkt_mesafe and komsu_mesafe < en_kisa_genel:
                            en_yakin_genel = diger.id
                            en_kisa_genel = komsu_mesafe
                    
                    if en_yakin_genel is not None:
                        yonlendirme[sensor.id] = {
                            'sonraki_hop': en_yakin_genel,
                            'mesafe': en_kisa_genel,
                            'hop_sayisi': 3
                        }
                    else:
                        # Hiçbir komşu bulunamadı - doğrudan gönder
                        yonlendirme[sensor.id] = {
                            'sonraki_hop': None,
                            'mesafe': direkt_mesafe,
                            'hop_sayisi': 1
                        }
        
        return yonlendirme
    
    def _multihop_iletim_sureci(self, env: simpy.Environment,
                                  sensorler: List[SensorDugum],
                                  yonlendirme: Dict):
        """
        Multi-hop iletim süreci.
        Her veri üretim aralığında tüm sensörler veriyi baz istasyonuna iletir.
        """
        while True:
            yield env.timeout(VERI_URETIM_ARALIGI + 1)  # Üretimden hemen sonra
            
            for sensor in sensorler:
                if not sensor.aktif or len(sensor.bellek) == 0:
                    continue
                
                if sensor.id in yonlendirme:
                    mesafe = yonlendirme[sensor.id]['mesafe']
                    sensor.multi_hop_ilet(mesafe, env.now)
    
    def karsilastirma_raporu(self):
        """Drone vs Multi-hop karşılaştırma raporu."""
        if not self.drone_sonuclari or not self.multihop_sonuclari:
            print("Her iki simülasyon da çalıştırılmalıdır!")
            return
        
        d = self.drone_sonuclari
        m = self.multihop_sonuclari
        
        print("\n" + "=" * 70)
        print("  KARŞILAŞTIRMA RAPORU: DRONE vs MULTI-HOP")
        print("=" * 70)
        print(f"{'Metrik':<35} {'Drone':>15} {'Multi-hop':>15}")
        print("-" * 70)
        print(f"{'Toplam İletilen Paket':<35} {d['toplam_paket']:>15} {m['toplam_paket']:>15}")
        print(f"{'Aktif Sensör (sonda)':<35} {d['aktif_sensor_sayisi']:>15} {m['aktif_sensor_sayisi']:>15}")
        print(f"{'Ort. Kalan Enerji (%)':<35} {d['ortalama_enerji']:>14.1f}% {m['ortalama_enerji']:>14.1f}%")
        print(f"{'Min. Kalan Enerji (%)':<35} {d['minimum_enerji']:>14.1f}% {m['minimum_enerji']:>14.1f}%")
        
        # Enerji tasarrufu hesapla
        d_ort_harcanan = 100 - d['ortalama_enerji']
        m_ort_harcanan = 100 - m['ortalama_enerji']
        
        if m_ort_harcanan > 0:
            tasarruf = ((m_ort_harcanan - d_ort_harcanan) / m_ort_harcanan) * 100
            print(f"\n  >>> Drone ile enerji tasarrufu: %{tasarruf:.1f}")
            
            if d_ort_harcanan > 0:
                omur_orani = m_ort_harcanan / d_ort_harcanan
                print(f"  >>> Tahmini ağ ömrü artışı: {omur_orani:.1f}x")
        
        print("=" * 70)
        
        return {
            'drone': d,
            'multihop': m,
            'enerji_log': self.enerji_log
        }


if __name__ == "__main__":
    sim = TarimSimulasyonu(simulasyon_suresi=1800)
    sim.drone_simulasyonu_calistir()
    sim.multihop_simulasyonu_calistir()
    sim.karsilastirma_raporu()
