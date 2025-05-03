# Telegram LOG
cheatglobal.com | cheatglobal.com/members/twixx.64436/

Bu bot, belirtilen Telegram kanallarından .txt dosyalarını otomatik olarak indirmenizi sağlayan bir tooldur.

## Kurulum

1. Python 3.10 veya daha yüksek bir sürümü yükleyin.
2. Gerekli paketleri yükleyin:
```
pip install -r requirements.txt
```

## Ayarlar

Bot'u kullanmaya başlamadan önce, `twix_bot.py` dosyasında aşağıdaki bilgileri doldurmanız gerekmektedir:

```python
API_ID = '' # API ID buraya
API_HASH = '' # API HASH buraya
PHONE_NUMBER = '' # Telefon numaranızı buraya yazın (+905554443322 gibi)
```

## API ID ve API HASH Nasıl Alınır

1. https://my.telegram.org/ adresine gidin.
2. Telefon numaranızla giriş yapın.
3. "API Development Tools" bölümüne tıklayın.
4. Bir uygulama oluşturun (uygulama adı ve açıklaması önemli değil, herhangi bir şey olabilir).
5. Oluşturma işlemi tamamlandıktan sonra, API ID ve API HASH bilgileriniz görüntülenecektir.
6. Bu bilgileri `twix_bot.py` dosyasındaki ilgili yerleri doldurun.

## Kanal Listesi

İndirme yapılacak kanal ID'lerini `CHANNEL_IDS` listesine ekleyin:

```python
CHANNEL_IDS = [
    -1002410689650,
    -1002192829947,
    # Daha fazla kanal ekleyebilirsiniz
]

Kanallara katılmak zorundasınız!
```

## Kullanım

Bot'u başlatmak için:

```
python twix_bot.py
```

Bot, belirtilen kanallardan belirli bir tarihten sonraki tüm mesajları tarayacak ve .txt dosyalarını indirecektir.

## Tarih Filtresi

Hangi tarihten sonraki mesajların taranacağını ayarlamak için şu satırı düzenleyin:

```python
FILTER_DATE = datetime(2025, 1, 28)  # Yıl, Ay, Gün formatında
```
