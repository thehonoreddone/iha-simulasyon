# 🚁 Tarım 5.0 — Drone/İHA Mobil Baz İstasyonu Simülasyonu

> **Kablosuz Sensör Ağlarında Drone Destekli Veri Toplama ve Multi-Hop Karşılaştırma Simülasyonu**

---

## 📖 Proje Hakkında

Bu proje, **Tarım 5.0** konsepti çerçevesinde bir tarım alanındaki kablosuz sensör ağından veri toplamanın iki farklı yöntemi arasındaki enerji verimliliğini karşılaştıran gerçek zamanlı bir animasyon simülasyonudur.

Simülasyon iki senaryoyu **eş zamanlı** olarak çalıştırır ve karşılaştırır:

| Senaryo | Açıklama |
|---|---|
| 🚁 **Drone (Mobil Baz İstasyonu)** | Bir İHA/drone, sensörleri optimize edilmiş bir rota ile gezerek yakın mesafeden veri toplar |
| 📡 **Multi-Hop (Sabit Baz İstasyonu)** | Sensörler, verilerini sabit bir baz istasyonuna çok atlamalı yönlendirme ile iletir |

---

## ✨ Temel Özellikler

- 🗺️ **Gerçek Zamanlı Animasyon** — Matplotlib TkAgg ile 30 FPS canlı görselleştirme
- 🛣️ **Akıllı Rota Planlama** — Nearest-Neighbour + 2-Opt optimizasyonu (TSP benzeri)
- ⚡ **First-Order Radio Enerji Modeli** — Fiziksel tabanlı enerji hesaplama (E_FS, E_MP)
- 📊 **Karşılaştırmalı Enerji Grafiği** — Drone vs Multi-Hop ortalama enerji tüketimi
- 🔴 **Sensör Durum Görselleştirmesi** — Canlı renk kodlaması ile anlık sensör durumları
- 📦 **Bellek Yönetimi** — Sensör buffer doluluk takibi ve paket kayıp tespiti
- ⚡ **Lazer Veri Toplama Efekti** — Drone veri toplarken görsel animasyon
- 📈 **İstatistik Paneli** — Tur sayısı, toplanan paket, mesafe, enerji tasarrufu oranı

---

## 🎯 Simülasyon Parametreleri

### Alan & Sensör Ayarları
| Parametre | Değer | Açıklama |
|---|---|---|
| `ALAN_W` / `ALAN_H` | 500 × 500 m | Tarım alanı boyutları |
| `SENSOR_N` | 30 | Toplam sensör sayısı |
| `SENSOR_ENERJI` | 0.5 J | Başlangıç enerji kapasitesi |
| `SENSOR_BELLEK_MAX` | 100 paket | Maksimum buffer boyutu |
| `VERI_URETIM_DT` | 10 sn | Veri üretim periyodu |
| `PAKET_BIT` | 4000 bit | Paket boyutu |

### Drone Ayarları
| Parametre | Değer | Açıklama |
|---|---|---|
| `DRONE_HIZ` | 10 m/s | Drone uçuş hızı |
| `DRONE_H` | 50 m | Uçuş yüksekliği |
| `DRONE_MENZIL` | 60 m | İletişim menzili |
| `DRONE_BEKLEME` | 2 sn | Durak bekleme süresi |
| `DRONE_TUR_ARASI` | 120 sn | Turlar arası bekleme süresi |

### Enerji Modeli (First-Order Radio)
```
d < D0 (87m)  →  E_tx = E_elec × k + E_fs × k × d²
d ≥ D0        →  E_tx = E_elec × k + E_mp × k × d⁴

E_elec = 50 nJ/bit
E_fs   = 10 pJ/bit/m²
E_mp   = 0.0013 pJ/bit/m⁴
```

---

## 🗂️ Proje Yapısı

```
iha-simulasyon/
├── simulate.py          # Ana simülasyon ve animasyon dosyası
├── requirements.txt     # Python bağımlılıkları
├── sonuclar/            # Simülasyon çıktıları (grafikler, loglar)
└── README.md
```

---

## 🛠️ Kurulum

### Gereksinimler
- Python 3.8+
- Tkinter (genellikle Python ile birlikte gelir)

### Adımlar

```bash
# Repoyu klonla
git clone https://github.com/thehonoreddone/iha-simulasyon.git
cd iha-simulasyon

# Bağımlılıkları yükle
pip install -r requirements.txt
```

---

## 🚀 Kullanım

```bash
python simulate.py
```

Simülasyon başladığında bir pencere açılır. **Pencereyi kapatarak durdurun.**

---

## 📺 Arayüz

```
┌─────────────────────────────────┬──────────────────────┐
│                                 │  Enerji Grafiği      │
│   500m × 500m Tarım Haritası    │  (Drone vs Multi-hop)│
│                                 ├──────────────────────┤
│   🟢 Aktif Sensör               │  İstatistik Paneli   │
│   🟠 Bellek Dolu Sensör         │  - Drone durumu      │
│   🟡 Düşük Enerjili Sensör      │  - Toplanan paketler │
│   🔴 Ölü Sensör                 │  - Enerji tasarrufu  │
│   🔺 Drone (İHA)                │  - Ömür oranı        │
│   🟣 Multi-hop Baz İstasyonu    │                      │
└─────────────────────────────────┴──────────────────────┘
```

---

## 🔬 Algoritma Detayları

### Rota Planlama (TSP Optimizasyonu)
1. **Nearest-Neighbour Heuristic** → Başlangıç rotası oluşturur
2. **2-Opt Local Search** → Rotayı iteratif olarak iyileştirir (çapraz geçişleri düzeltir)
3. Her turdan önce yeniden hesaplanır (ölü sensörler rotadan çıkarılır)

### Multi-Hop Yönlendirme
- Her sensör, baza olan mesafesine göre en yakın "relay" düğümünü seçer
- Baz menzilindeki sensörler doğrudan iletim yapar
- Greedy forwarding: Mesafeyi azaltan en yakın komşu seçilir

### Sensör Renk Kodlaması
| Renk | Anlam |
|---|---|
| 🟢 Yeşil (`#2ed573`) | Aktif ve sağlıklı |
| 🟠 Turuncu (`#ffa502`) | Buffer doluluk > %70 |
| 🟡 Sarı (`#eccc68`) | Enerji < %30 |
| 🔴 Kırmızı (`#ff4757`) | Ölü (enerji tükenmiş) |
| ✨ Parlak Yeşil | Drone veri toplarken (flash animasyonu) |

---

## 📦 Bağımlılıklar

```
numpy>=1.21
matplotlib>=3.5
simpy>=4.0
```

---

## 💡 Motivasyon

Geleneksel kablosuz sensör ağlarında sensörler, verilerini çok atlamalı yönlendirme (multi-hop) ile sabit bir baz istasyonuna iletir. Bu yaklaşım:
- **Röle düğümlere** orantısız enerji yükü bindirir
- **Enerji tükenmesi** ile ağ topolojisi bozulur

Drone tabanlı mobil baz istasyonu yaklaşımında ise drone sensörlere yaklaşarak iletim mesafesini minimuma indirir ve enerji yükünü dengeli biçimde dağıtır.

Bu simülasyon bu iki yaklaşımı **aynı sensör ağı üzerinde** karşılaştırarak drone destekli veri toplamanın enerji verimliliğine katkısını görselleştirir.

---

## 📄 Lisans

Bu proje akademik ve eğitim amaçlıdır.

---

*Tarım 5.0 — Akıllı Tarım için İHA Destekli Kablosuz Sensör Ağı Simülasyonu*
