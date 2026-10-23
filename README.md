# Eye of Creation

Bir gözün içine dalıp evrenin doğuşuna giden, ardından kara deliğin içinden tekrar o göze dönen ASCII sinematik döngü. Python + pygame ile gerçek zamanlı çalışıyor; aynı döngü macOS ekran koruyucusu olarak da kurulabiliyor.

**EYE → CREATION → BIG BANG → GALAXY → BLACK HOLE → EYE**

![önizleme](docs/preview.png)

## Çalıştırma

```bash
python3 -m venv eye-env
source eye-env/bin/activate
pip install -r requirements.txt
python eye_of_creation.py
```

| Tuş | İşlev |
| --- | --- |
| `SPACE` | duraklat / devam |
| `1`–`5` | sahneye atla |
| `←` / `→` | hız |
| `C` | renk modu (COLOR / MATRIX / MONO) |
| `ESC` | çıkış |

> Python 3.14 kullanıyorsan orijinal `pygame` paketinin font modülü çalışmıyor; `requirements.txt` bu yüzden birebir uyumlu olan `pygame-ce`'yi kuruyor.

## macOS ekran koruyucu

**Kaynaktan kur** (Xcode Command Line Tools yeterli):

```bash
./install.sh
```

Script `.saver` paketini derleyip `~/Library/Screen Savers` içine kopyalar ve Ekran Koruyucu ayarlarını açar. Listeden **Eye of Creation**'ı seçmen yeterli.

**Hazır paket:** [Releases](../../releases) sayfasındaki `EyeOfCreation.saver.zip` dosyasını indir, aç ve çift tıkla. Paket imzasız olduğu için macOS ilk seferde engelleyebilir. Engellerse şunu çalıştır:

```bash
xattr -dr com.apple.quarantine ~/Library/Screen\ Savers/EyeOfCreation.saver
```

## Videoyu yeniden üretmek

Ekran koruyucu, döngünün önceden render edilmiş bir videosunu oynatıyor. Kodda bir şey değiştirirsen videoyu yeniden üret (ffmpeg gerekir):

```bash
EOC_W=1920 EOC_H=1200 EOC_SAVER=1 python tools/record.py screensaver/EyeOfCreation.mp4
```

## Notlar

- CREATION sahnesindeki eller Michelangelo'nun *Adem'in Yaratılışı* freskinden (Sistina Şapeli, kamu malı) alındı. Görsel kodun içine gömülü.
- [@erfanxasadi](https://www.instagram.com/erfanxasadi/)'nin "Eye of Creation" reel'inden ilham alındı.
