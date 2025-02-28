# Monitoring API

Bu proje, FastAPI kullanılarak geliştirilmiş bir sunucu izleme ve bakım yönetim API'sidir. API, sunucu durumlarını ping ve port kontrolü ile takip eder ve bakım modlarını yönetir. Ayrıca, Discord Webhook entegrasyonu sayesinde bildirim gönderebilir.

## 🚀 Kurulum

### 1️⃣ Gerekli Bağımlılıkları Yükleyin

Öncelikle, tüm bağımlılıkları yüklemek için aşağıdaki komutu çalıştırın:
```bash
pip install -r requirements.txt
```

### 2️⃣ Veritabanını Oluşturun

PostreSQL veritabanı için öncelikle veritabanına giriş yapın
sudo -u postgres psql

## Veritabanına giriş yaptıktan sonra tablo ve veritabanı kullanıcısı oluşturun kullanıcı 
CREATE DATABASE monitoring_db;
CREATE USER user WITH ENCRYPTED PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE monitoring_db TO user;


Kullanıcıyı oluşturduktan sonra  `main.py` içinde güncelleyin:
```python
DATABASE_URL = "postgresql://user:password@localhost/monitoring_db"
```

### 3️⃣ API'yi Çalıştırın
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📌 API Endpointleri ve Kullanımı

### 🟢 Kullanıcı Kayıt
**Endpoint:** `POST /auth/register/`
```json
{
  "username": "testuser",
  "password": "TestPassword123"
}
```

### 🔑 Kullanıcı Girişi (Token Alma)
**Endpoint:** `POST /auth/login/`
```json
{
  "username": "testuser",
  "password": "TestPassword123"
}
```
📌 **Yanıt:**
```json
{
  "access_token": "your_jwt_token_here",
  "token_type": "bearer"
}
```
📌 **Bu `access_token` değerini kopyalayıp diğer API isteklerinde `Authorization: Bearer {TOKEN}` olarak ekleyin.**

### 🚀 Sunucu Ekleme
**Endpoint:** `POST /servers/`
```json
{
  "name": "Test Server",
  "ip_address": "192.168.1.100",
  "snmp_community": "public"
}
```

### 📡 Ping Testi
**Endpoint:** `GET /ping/{ip_address}`
```bash
curl -X GET "http://localhost:8000/ping/192.168.1.100"
```
📌 **Yanıt:**
```json
{
  "ip": "192.168.1.100",
  "status": "UP",
  "response_time": 10.5
}
```

### 🔍 Port Kontrolü
**Endpoint:** `GET /port-check/{ip_address}/{port}`
```bash
curl -X GET "http://localhost:8000/port-check/192.168.1.100/22"
```

### 🛠 Bakım Başlatma
**Endpoint:** `POST /maintenance/`
```json
{
  "server_id": 1,
  "description": "Updating OS"
}
```

### 📋 Bakım Listeleme
**Endpoint:** `GET /maintenance/`
```bash
curl -X GET "http://localhost:8000/maintenance/"
```

### ✅ Bakımı Sonlandırma
**Endpoint:** `PATCH /maintenance/{maintenance_id}`
```bash
curl -X PATCH "http://localhost:8000/maintenance/1"
```

## 🛠 Geliştirme ve Katkı Sağlama

1. Projeyi forklayın.
2. Yeni bir özellik eklemek için branch oluşturun.
3. Kodunuzu geliştirin ve test edin.
4. PR (Pull Request) açarak katkı sağlayın.

## 📜 Lisans
Bu proje MIT lisansı ile lisanslanmıştır.
