Proje Hakkında
Bu proje, insansız hava araçlarının (İHA) belirlenmiş bir hedef platforma otonom ve
hassas bir şekilde iniş yapmasını sağlamak amacıyla geliştirilmiştir. Görüntü işleme
birimi olarak YOLOv8 kullanılırken, karar mekanizması olarak Bulanık Mantık (Fuzzy
Logic) algoritması tercih edilmiştir.
Temel Özellikler

Gerçek Zamanlı Nesne Tespiti: YOLOv8 ve MobileNetV3 mimarileri ile yüksek
doğruluklu iniş platformu tespiti.
Akıllı Karar Mekanizması: Hedef ile İHA arasındaki merkez kaymasını minimize
eden Bulanık Mantık kontrolcüsü.
Güvenlik Motoru (Safety Engine): İniş sırasında karşılaşılan riskleri minimize
eden güvenlik algoritmaları.
Donanım Entegrasyonu: Raspberry Pi 5 üzerinde optimize edilmiş çalışma
performansı.

Teknoloji Yığını
Dil: Python
Görüntü İşleme: OpenCV, YOLOv8
Yapay Zeka: MobileNetV3 (Hafif ve hızlı çıkarım için)
Kontrol: Fuzzy Logic (Bulanık Mantık)
Donanım: Raspberry Pi 5, Kamera Modülü
•

•

•

•

•
•
•
•
•

Kurulum

git clone https://github.com/kullaniciadi/otonom-iha-inis.git
cd otonom-iha-inis
pip install -r requirements.txt

Kullanım

Sistemi başlatmak için ana betiği çalıştırın:

python main.py --model yolov8n.pt --source 0

Sistem Mimarisi

Sistem, kameradan gelen görüntüyü işleyerek hedefin merkez koordinatlarını belirler.
Bulanık mantık kontrolcüsü, bu koordinatları kullanarak İHA'nın motor sürücülerine
gidecek olan yönelme komutlarını üretir.
