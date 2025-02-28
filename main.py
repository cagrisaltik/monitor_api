from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from passlib.context import CryptContext
from jose import JWTError, jwt
import socket
import ping3
from pysnmp.hlapi import *
from discord_webhook import DiscordWebhook
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

# Database Configuration
DATABASE_URL = "postgresql://user:password@localhost/monitoring_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Security & Authentication
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Webhook Notification System
WEBHOOK_URL = ""

def send_webhook_message(message: str):
    webhook = DiscordWebhook(url=WEBHOOK_URL, content=message)
    webhook.execute()

# Pydantic Models
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class ServerCreate(BaseModel):
    name: str
    ip_address: str
    snmp_community: str

class ServerUpdate(ServerCreate):
    is_active: bool

class MaintenanceCreate(BaseModel):
    server_id: int
    description: str

# Database Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)

class Server(Base):
    __tablename__ = "servers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    ip_address = Column(String, unique=True, nullable=False)
    snmp_community = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

class Maintenance(Base):
    __tablename__ = "maintenance"
    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id"))
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    description = Column(String, nullable=False)
    server = relationship("Server")

Base.metadata.create_all(bind=engine)

# Password Hashing
def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# JWT Token Creation
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Authentication Endpoints
@app.post("/auth/register/")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    new_user = User(username=user.username, hashed_password=get_password_hash(user.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully"}

@app.post("/auth/login/")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    return {"access_token": create_access_token({"sub": db_user.username}), "token_type": "bearer"}

# Server Endpoints
@app.post("/servers/")
def create_server(server: ServerCreate, db: Session = Depends(get_db)):
    existing_server = db.query(Server).filter(Server.ip_address == server.ip_address).first()
    if existing_server:
        raise HTTPException(status_code=400, detail="IP address already exists")
    db_server = Server(**server.dict())
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    return db_server

@app.get("/servers/")
def list_servers(db: Session = Depends(get_db)):
    return db.query(Server).all()

@app.put("/servers/{server_id}")
def update_server(server_id: int, server: ServerUpdate, db: Session = Depends(get_db)):
    db_server = db.query(Server).filter(Server.id == server_id).first()
    if not db_server:
        raise HTTPException(status_code=404, detail="Server not found")
    for key, value in server.dict().items():
        setattr(db_server, key, value)
    db.commit()
    return db_server

@app.delete("/servers/{server_id}")
def delete_server(server_id: int, db: Session = Depends(get_db)):

    #önce Sunucuya ait bakım kayıtlarını sil 
    db.query(Maintenance).filter(Maintenance.server_id == server_id).delete()
    db.commit()

    # Sonra sunucuyu sil
    
    db_server = db.query(Server).filter(Server.id == server_id).first()
    if not db_server:
        raise HTTPException(status_code=404, detail="Server not found")
    db.delete(db_server)
    db.commit()
    return {"message": "Server deleted"}

# Maintenance Endpoints
@app.post("/maintenance/")
def create_maintenance(maintenance: dict, db: Session = Depends(get_db)):
    new_maintenance = Maintenance(server_id=maintenance["server_id"], description=maintenance["description"])
    db.add(new_maintenance)
    db.commit()
    db.refresh(new_maintenance)
    send_webhook_message(f"🛠 Sunucu {new_maintenance.server_id} bakım moduna alındı: {new_maintenance.description}")
    return new_maintenance

@app.get("/maintenance/")
def list_maintenance(db: Session = Depends(get_db)):
    return db.query(Maintenance).all()

@app.patch("/maintenance/{maintenance_id}")
def end_maintenance(maintenance_id: int, db: Session = Depends(get_db)):
    maintenance = db.query(Maintenance).filter(Maintenance.id == maintenance_id).first()
    if not maintenance:
        raise HTTPException(status_code=404, detail="Maintenance not found")
    maintenance.end_time = datetime.utcnow()
    db.commit()
    send_webhook_message(f"✅ Sunucu {maintenance.server_id} bakım modundan çıkarıldı.")
    return maintenance


# Ping Test
@app.get("/ping/{ip_address}")
def ping_server(ip_address: str):
    response_time = ping3.ping(ip_address)
    if response_time is None:
        send_webhook_message(f"🚨 Sunucu DOWN: {ip_address}")
        return {"ip": ip_address, "status": "Down"}
    else:
        send_webhook_message(f"✅ Sunucu UP: {ip_address} - {response_time}ms")
        return {"ip": ip_address, "status": "UP", "response_time": response_time}

# Port Check
@app.get("/port-check/{ip_address}/{port}")
def check_port(ip_address: str, port: int):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex((ip_address, port))
    sock.close()
    
    if result == 0:
        send_webhook_message(f"✅ Port {port} açık: {ip_address}")
        return {"ip": ip_address, "port": port, "status": "Open"}
    else:
        send_webhook_message(f"🚨 Port {port} kapalı: {ip_address}")
        return {"ip": ip_address, "port": port, "status": "Closed"}


# Maintenance Management
@app.post("/maintenance/")
def create_maintenance(server_id: int, description: str, db: Session = Depends(get_db)):
    maintenance = Maintenance(server_id=server_id, description=description)
    db.add(maintenance)
    db.commit()
    db.refresh(maintenance)
    return maintenance

@app.get("/maintenance/")
def list_maintenance(db: Session = Depends(get_db)):
    return db.query(Maintenance).all()

@app.patch("/maintenance/{maintenance_id}")
def end_maintenance(maintenance_id: int, db: Session = Depends(get_db)):
    maintenance = db.query(Maintenance).filter(Maintenance.id == maintenance_id).first()
    if not maintenance:
        raise HTTPException(status_code=404, detail="Maintenance not found")
    maintenance.end_time = datetime.utcnow()
    db.commit()
    return maintenance
