# Tarım 5.0: Mobil Baz İstasyonu (Drone/İHA) Yoluyla Veri Toplama

## Proje Açıklaması

Bu proje, **Kablosuz Algılayıcı Ağlarda (WSN)** mobil bir baz istasyonu (Drone/İHA) kullanarak tarım alanlarından enerji-verimli veri toplama simülasyonunu gerçekleştirir.

### Temel Konsept
Sabit baz istasyonu yerine, belirli aralıklarla ağın üzerinde uçan ve verileri toplayan bir **mobil düğüm (Data Mule)** simülasyonu yapılmaktadır.

**Farkı:** Düğümler veriyi çok uzaklara (multi-hop) göndermek yerine, Drone yakınına gelene kadar belleğinde saklar. Bu, uç noktalardaki düğümlerin pil ömrünü **10 kata kadar** artırabilir.

---

## Mimari

```
tarim_iha/
├── main.py              # Ana çalıştırma betiği
├── config.py            # Konfigürasyon parametreleri
├── sensor.py            # Sensör düğüm modeli
├── drone.py             # Drone/İHA (Data Mule) modeli
├── energy_model.py      # Enerji tüketim modeli (First Order Radio)
├── trajectory.py        # Rota optimizasyonu (NN + 2-Opt)
├── simulation.py        # SimPy tabanlı ayrık olay simülasyonu
├── visualization.py     # Matplotlib görselleştirme (7 grafik)
├── requirements.txt     # Python bağımlılıkları
├── README.md            # Bu dosya
└── sonuclar/            # Çıktı grafikleri (otomatik oluşturulur)
```

## Simüle Edilen Senaryolar

### Senaryo 1: Mobil Baz İstasyonu (Drone)
- Sensörler periyodik olarak veri üretir (sıcaklık, nem, toprak nemi)
- Veriler sensör belleğinde saklanır
- Drone optimize edilmiş rotada uçarak veri toplar
- **Düşük enerji tüketimi** (kısa mesafe iletim)

### Senaryo 2: Sabit Baz İstasyonu (Multi-hop)
- Aynı sensör ağı ve veri üretimi
- Sensörler veriyi multi-hop yönlendirme ile baz istasyonuna iletir
- **Yüksek enerji tüketimi** (uzun mesafe, çok hop iletim)

## Kullanılan Modeller

| Bileşen | Model |
|---------|-------|
| Enerji | First Order Radio Model (Heinzelman et al.) |
| Rota Optimizasyonu | Nearest Neighbor + 2-Opt (TSP benzeri) |
| Simülasyon | SimPy ayrık olay simülasyonu |
| Veri Üretimi | Periyodik algılama (sıcaklık, nem, toprak nemi) |

## Kurulum

```bash
pip install -r requirements.txt
```

## Çalıştırma

```bash
cd tarim_iha
python main.py
```

## Çıktılar

Simülasyon tamamlandığında `sonuclar/` klasöründe 7 grafik oluşturulur:

1. **Ağ Topolojisi ve Drone Rotası** - Sensör konumları + optimize edilmiş drone rotası
2. **Enerji Karşılaştırması** - Drone vs Multi-hop sensör bazında enerji karşılaştırması
3. **Enerji Isı Haritası** - Alandaki enerji dağılımı görselleştirmesi
4. **Zaman Serisi** - Zamanla enerji tüketimi ve aktif sensör değişimi
5. **Drone Rota Detayı** - Zamanlı rota ve kümülatif veri toplama
6. **Bellek ve Paket Analizi** - Üretilen, iletilen, kaybedilen paket istatistikleri
7. **Multi-hop Topoloji** - Yönlendirme bağlantıları ve baz istasyonu

## Parametreler

Tüm parametreler `config.py` dosyasından ayarlanabilir:

| Parametre | Varsayılan | Açıklama |
|-----------|-----------|----------|
| SENSOR_SAYISI | 30 | Toplam sensör düğüm sayısı |
| ALAN_GENISLIK/YUKSEKLIK | 500m | Tarım alanı boyutu |
| DRONE_HIZ | 10 m/s | İHA uçuş hızı |
| DRONE_YUKSEKLIK | 50m | Uçuş yüksekliği |
| DRONE_ILETISIM_MENZIL | 60m | İletişim menzili |
| SIMULASYON_SURESI | 3600s | Simülasyon süresi (1 saat) |
| VERI_URETIM_ARALIGI | 10s | Sensör veri üretim periyodu |

## Araçlar

- **SimPy**: Ayrık olay simülasyonu
- **NumPy**: Koordinat hesaplamaları ve matematiksel işlemler
- **Matplotlib**: Görselleştirme ve grafik oluşturma
