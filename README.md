# Ön Muhasebe Yönetim Sistemi

Bu proje, Django ile geliştirilmiş bir ön muhasebe yönetim sistemidir. Kullanıcılar sisteme kayıt olabilir, giriş yapabilir, şirketlerini ekleyebilir ve her şirket için gelir-gider kayıtlarını yönetebilir.

Projede manuel muhasebe kaydı ekleme, fiş/fatura yükleyerek Gemini API ile veri işleme, günlük ve aylık rapor görüntüleme gibi özellikler bulunmaktadır.

---

## Özellikler

- Kullanıcı kayıt ve giriş sistemi
- Şirket ekleme ve şirket bazlı panel yönetimi
- Aynı sayfa içinde şirket paneli değiştirme
- Gelir kaydı ekleme
- Gider kaydı ekleme
- Geçici kayıt sistemi
- Kaydet butonu ile veritabanına aktarma
- Panel tablosunu temizleme
- Günlük rapor görüntüleme
- Aylık rapor görüntüleme
- Günlük Rapor kayıtlarını silme
- Gemini API ile fiş/fatura üzerinden veri çıkarma
- MySQL veritabanı desteği

---

## Kullanılan Teknolojiler

- Python
- Django
- MySQL
- HTML
- CSS
- JavaScript
- Gemini API

---

## Proje Mantığı

Sistemde her kullanıcı kendi şirketlerini oluşturabilir. Her şirket için ayrı gelir ve gider kayıtları tutulur.

Muhasebe kaydı ekleme işlemi iki aşamalıdır:

1. Kullanıcı gelir veya gider bilgisini tabloya geçici olarak ekler.
2. Kaydet butonuna basıldığında geçici kayıtlar veritabanına aktarılır.

Bu yapı sayesinde kullanıcı, veritabanına kaydetmeden önce kayıtlarını kontrol edebilir.

---

## Gemini API Kullanımı

Projede fiş veya fatura dosyası yüklendiğinde dosya sunucuya kaydedilmez. Dosya sadece `request.FILES` üzerinden okunur ve Gemini API’ye gönderilir.

Gemini API’den şu bilgiler alınmaya çalışılır:

- Tarih
- Tutar
- Açıklama

Örnek çıktı:

```json
{
  "date": "2024-05-11",
  "amount": "94.00",
  "description": "Kedi Maması"
}
