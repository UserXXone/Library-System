# 📚 Kütüphane Yönetim Sistemi (Pro Mod)

Gelişmiş Excel/CSV entegrasyonuna sahip, hafif, modern ve güvenli bir Kütüphane Yönetim Sistemi. Python ve Tkinter ile geliştirilmiş olup, özellikle büyük veri listelerinin (barkod/QR) içeri aktarılmasında yüksek doğruluk ve hız sunar.

## 🚀 Öne Çıkan Özellikler

*   **Akıllı Excel & CSV Aktarımı:** Sütun isimlerini (QR, Barkod, ISBN, Kitap Adı vb.) format fark etmeksizin otomatik tanır ve önceliklendirir. Hatalı Excel hücre formatlarındaki (örn: `.0` uzantısı) verileri temizler, tireli (`-1`, `-2`) özel takip barkodlarını bozmadan içeri alır.
*   **Gelişmiş Veritabanı (SQLite):** Kitaplar, öğrenciler ve ödünç/iade işlemleri güvenli bir şekilde saklanır. Mükerrer barkod kayıtlarında program çökmez, sistemde var olan kitabın sadece raf bilgisini günceller.
*   **Modern ve Dinamik Arayüz:** Kullanıcı dostu Tkinter arayüzü, canlı arama (klavyeden yazarken anında filtreleme) ve dahili tema desteği (Modern Koyu, Gece Modu, Okyanus).
*   **Gecikme Takibi:** Geciken veya bugün teslim edilmesi gereken ödünç kitapları renkli etiketlerle (uyarı formatında) listeler.
*   **Gizli Geliştirici Modları (Root Access):**
    *   `Alt + 2`: Sistem arka plan işlemlerini ve süreç hatalarını izlemek için canlı **Debug Konsolu**.
    *   `Ctrl + 2`: Doğrudan ham SQL komutları çalıştırabileceğiniz, tüm kitapları zorla iade alabileceğiniz veya veritabanını sıfırlayabileceğiniz **Hack Mode (SQL Injector)**.
*   **Sistem Koruması:** Windows `.exe` derlemelerinde sıklıkla karşılaşılan "Fork Bomb" (programın kendi kendini sonsuz döngüde açması) sorununa karşı `multiprocessing.freeze_support()` koruması aktiftir.

## 🛠️ Kurulum ve Geliştirme

Projenin çalışması için sisteminizde Python 3.x yüklü olmalıdır.

**1. Depoyu klonlayın:**
```bash
git clone [https://github.com/kullaniciadi/proje-adi.git](https://github.com/kullaniciadi/proje-adi.git)
cd proje-adi


mehmetozkal12@gmail.com
