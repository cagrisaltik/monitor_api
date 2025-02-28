# Monitoring API

This project is a server monitoring and maintenance management API developed using FastAPI. The API tracks server statuses via ping and port checks and manages maintenance modes. Additionally, it can send notifications using Discord Webhook integration.

## 🚀 Installation

### 1️⃣ Install Required Dependencies

First, install all dependencies by running:
```bash
pip install -r requirements.txt
```

### 2️⃣ Create the Database

For PostreSQL database, first log in to the database
```bash
sudo -u postgres psql
```
 After logging in to the database, create a table and database user user 
```
CREATE DATABASE monitoring_db;
CREATE USER user WITH ENCRYPTED PASSWORD ‘password’;
GRANT ALL PRIVILEGES ON DATABASE monitoring_db TO user;
```


After creating the user, update it in `main.py`:
```python
DATABASE_URL = ‘postgresql://user:password@localhost/monitoring_db’
```

Translated with DeepL.com (free version)

### 3️⃣ Start the API
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📌 API Endpoints and Usage

### 🟢 User Registration
**Endpoint:** `POST /auth/register/`
```json
{
  "username": "testuser",
  "password": "TestPassword123"
}
```

### 🔑 User Login (Token Retrieval)
**Endpoint:** `POST /auth/login/`
```json
{
  "username": "testuser",
  "password": "TestPassword123"
}
```
📌 **Response:**
```json
{
  "access_token": "your_jwt_token_here",
  "token_type": "bearer"
}
```
📌 **Copy the `access_token` and use it in other API requests with `Authorization: Bearer {TOKEN}`.**

### 🚀 Add Server
**Endpoint:** `POST /servers/`
```json
{
  "name": "Test Server",
  "ip_address": "192.168.1.100",
  "snmp_community": "public"
}
```

### 📡 Ping Test
**Endpoint:** `GET /ping/{ip_address}`
```bash
curl -X GET "http://localhost:8000/ping/192.168.1.100"
```
📌 **Response:**
```json
{
  "ip": "192.168.1.100",
  "status": "UP",
  "response_time": 10.5
}
```

### 🔍 Port Check
**Endpoint:** `GET /port-check/{ip_address}/{port}`
```bash
curl -X GET "http://localhost:8000/port-check/192.168.1.100/22"
```

### 🛠 Start Maintenance
**Endpoint:** `POST /maintenance/`
```json
{
  "server_id": 1,
  "description": "Updating OS"
}
```

### 📋 List Maintenance
**Endpoint:** `GET /maintenance/`
```bash
curl -X GET "http://localhost:8000/maintenance/"
```

### ✅ End Maintenance
**Endpoint:** `PATCH /maintenance/{maintenance_id}`
```bash
curl -X PATCH "http://localhost:8000/maintenance/1"
```

## 🛠 Development and Contribution

1. Fork the project.
2. Create a branch for new features.
3. Develop and test your code.
4. Submit a Pull Request (PR) to contribute.

## 📜 License
This project is licensed under the MIT License.
