# SQL Server Docker Setup for FastAPI Development

Quick reference guide for setting up SQL Server in Docker on WSL for local development.

---

## Prerequisites

- Windows 10/11 with WSL2 installed
- Ubuntu (or any Linux distro) running in WSL

---

## Step 1: Install Docker in WSL

Open your WSL terminal and run:

```bash
# Update package list
sudo apt update

# Install Docker
sudo apt install -y docker.io

# Start Docker service
sudo service docker start

# Add your user to docker group (avoid using sudo with docker commands)
sudo usermod -aG docker $USER

# Apply group changes (or log out and back in)
newgrp docker

# Verify Docker is working
docker --version
docker ps
```

### Make Docker Start Automatically (Optional)

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# Start Docker automatically
if service docker status 2>&1 | grep -q "is not running"; then
    sudo service docker start > /dev/null 2>&1
fi
```

Then run: `source ~/.bashrc` or `source ~/.zshrc`

---

## Step 2: Run SQL Server Container

### Quick Start (Recommended for Development)

```bash
docker run -e "ACCEPT_EULA=Y" \
  -e "MSSQL_SA_PASSWORD=DevPassword123!" \
  -p 1433:1433 \
  --name sqlserver \
  --hostname sqlserver \
  -v sqlvolume:/var/opt/mssql \
  -d mcr.microsoft.com/mssql/server:2022-latest
```

**What this does:**
- `ACCEPT_EULA=Y` - Accepts SQL Server license
- `MSSQL_SA_PASSWORD` - Sets admin password (change this!)
- `-p 1433:1433` - Maps port 1433 (SQL Server default)
- `--name sqlserver` - Names the container for easy reference
- `-v sqlvolume:/var/opt/mssql` - Persists data (survives container deletion)
- `-d` - Runs in background
- `mcr.microsoft.com/mssql/server:2022-latest` - SQL Server 2022 image

### With Custom Data Directory (Optional)

If you want data stored in a specific folder:

```bash
# Create directory for SQL Server data
mkdir -p ~/sqlserver_data

docker run -e "ACCEPT_EULA=Y" \
  -e "MSSQL_SA_PASSWORD=DevPassword123!" \
  -p 1433:1433 \
  --name sqlserver \
  --hostname sqlserver \
  -v ~/sqlserver_data:/var/opt/mssql/data \
  -d mcr.microsoft.com/mssql/server:2022-latest
```

### Verify Container is Running

```bash
docker ps
```

You should see `sqlserver` in the list.

---

## Step 3: Common Docker Commands

```bash
# Start SQL Server (after machine reboot)
docker start sqlserver

# Stop SQL Server
docker stop sqlserver

# Restart SQL Server
docker restart sqlserver

# View logs (troubleshooting)
docker logs sqlserver

# Check container status
docker ps -a

# Connect to container shell
docker exec -it sqlserver bash

# Remove container (data persists in volume)
docker rm sqlserver

# Remove container AND volume (deletes all data)
docker rm sqlserver
docker volume rm sqlvolume
```

---

## Step 4: Connect with SQL Tools

### Option A: sqlcmd (Command Line)

Install SQL command-line tools in WSL:

```bash
# Download and install the Microsoft signing key
curl https://packages.microsoft.com/keys/microsoft.asc | sudo tee /etc/apt/trusted.gpg.d/microsoft.asc

# Add the SQL Server tools repository
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list

# Update package list and install
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y mssql-tools18 unixodbc-dev

# Add to PATH
echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc
source ~/.bashrc

# Test connection to SQL Server
sqlcmd -S localhost -U sa -P DevPassword123! -C
```

### Option B: VS Code SQL Server Extension

1. Open VS Code
2. Install extension: **SQL Server (mssql)** by Microsoft
3. Click SQL Server icon in sidebar
4. Add Connection:
   - **Server:** `localhost`
   - **Database:** `<default>`
   - **Authentication Type:** `SQL Login`
   - **User:** `sa`
   - **Password:** `DevPassword123!`
   - **Save Password:** Yes
   - **Profile Name:** `Local Docker SQL Server`

### Option C: Azure Data Studio (Windows)

Download from: https://aka.ms/azuredatastudio

Connect with:
- **Server:** `localhost`
- **Authentication:** SQL Login
- **User:** `sa`
- **Password:** `DevPassword123!`

---

## Step 5: Create Your Development Database

```sql
-- Connect with sqlcmd or VS Code, then run:
CREATE DATABASE DevDB;
GO

USE DevDB;
GO

-- Test table
CREATE TABLE users (
    id INT PRIMARY KEY IDENTITY(1,1),
    username NVARCHAR(50) NOT NULL,
    email NVARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT GETDATE()
);
GO

-- Insert test data
INSERT INTO users (username, email) 
VALUES ('testuser', 'test@example.com');
GO

-- Verify
SELECT * FROM users;
GO
```

---

## Step 6: Configure FastAPI with SQLAlchemy

### Install Required Packages

```bash
pip install sqlalchemy pymssql fastapi uvicorn
```

### Database Configuration File

Create `database.py`:

```python
import os
from typing import Annotated
from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

# Database Configuration
DB_SERVER = os.getenv("DB_SERVER", "localhost")
DB_PORT = os.getenv("DB_PORT", "1433")
DB_NAME = os.getenv("DB_NAME", "DevDB")
DB_USER = os.getenv("DB_USER", "sa")
DB_PASSWORD = os.getenv("DB_PASSWORD", "DevPassword123!")

# Connection String
SQLALCHEMY_DATABASE_URL = (
    f"mssql+pymssql://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}:{DB_PORT}/{DB_NAME}"
)

# Create Engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True,  # Set to False in production
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base Class for Models
Base = declarative_base()

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Type hint for dependency injection
db_dependency = Annotated[Session, Depends(get_db)]
```

### Environment Variables (Recommended)

Create `.env` file:

```env
DB_SERVER=localhost
DB_PORT=1433
DB_NAME=DevDB
DB_USER=sa
DB_PASSWORD=DevPassword123!
```

Install python-dotenv:

```bash
pip install python-dotenv
```

Load in your app:

```python
from dotenv import load_dotenv
load_dotenv()
```

### Example Model

Create `models.py`:

```python
from sqlalchemy import Boolean, Column, Integer, String, DateTime
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Example FastAPI App

Create `main.py`:

```python
from fastapi import FastAPI
from database import engine, Base, db_dependency
from models import User

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "SQL Server + FastAPI"}

@app.get("/users")
def get_users(db: db_dependency):
    users = db.query(User).all()
    return users

@app.post("/users")
def create_user(username: str, email: str, db: db_dependency):
    user = User(username=username, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```

Run:

```bash
uvicorn main:app --reload
```

Visit: http://localhost:8000/docs

---

## Key Differences: SQLite vs SQL Server

| Feature | SQLite | SQL Server |
|---------|--------|------------|
| Connection | `sqlite:///path/to/db.db` | `mssql+pymssql://user:pass@host/db` |
| String Length | Optional | **Required**: `String(200)` |
| Boolean | Stored as 0/1 | Native `BIT` type |
| Auto Increment | `autoincrement=True` | `identity=True` or let DB handle |
| Date/Time | `func.now()` | `func.getdate()` |
| Thread Safety | Needs `check_same_thread=False` | Not needed |

**Critical Change for Models:**

```python
# SQLite (old)
title = Column(String)

# SQL Server (new)
title = Column(String(200))  # MUST specify length!
```

---

## Connection String Formats

### pymssql (Recommended - Simpler)

```python
"mssql+pymssql://sa:password@localhost:1433/DevDB"
```

### pyodbc (More Complex - Requires ODBC Driver)

```python
from urllib.parse import quote_plus

connection_string = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=DevDB;"
    "UID=sa;"
    "PWD=password;"
    "TrustServerCertificate=yes;"
)
params = quote_plus(connection_string)
DATABASE_URL = f"mssql+pyodbc:///?odbc_connect={params}"
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs sqlserver

# Common issue: Port already in use
# Solution: Stop Windows SQL Server or change port
docker run ... -p 1434:1433 ...  # Use different host port
```

### Can't Connect from FastAPI

```bash
# Test connection manually
docker exec -it sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P DevPassword123! -C

# Check if container is running
docker ps

# Check firewall (rarely needed in WSL)
sudo ufw status
```

### Password Policy Error

Password must:
- Be at least 8 characters
- Contain 3 of 4: uppercase, lowercase, digits, symbols

### Docker Service Not Running

```bash
# Start Docker
sudo service docker start

# Check status
sudo service docker status
```

### Data Persistence Not Working

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect sqlvolume

# Manually create volume first
docker volume create sqlvolume
```

---

## Quick Reference Card

```bash
# Start SQL Server
docker start sqlserver

# Stop SQL Server
docker stop sqlserver

# Connect with sqlcmd
sqlcmd -S localhost -U sa -P DevPassword123! -C

# Create database
sqlcmd -S localhost -U sa -P DevPassword123! -C -Q "CREATE DATABASE DevDB"

# Backup database
docker exec sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P DevPassword123! -Q "BACKUP DATABASE DevDB TO DISK='/var/opt/mssql/data/DevDB.bak'" -C

# View container logs
docker logs sqlserver -f

# Clean slate (delete everything)
docker rm -f sqlserver && docker volume rm sqlvolume
```

---

## Production Considerations

When connecting to **enterprise SQL Server** at work:

```python
# Production connection
SQLALCHEMY_DATABASE_URL = (
    f"mssql+pymssql://{PROD_USER}:{PROD_PASSWORD}@"
    f"{PROD_SERVER}:{PROD_PORT}/{PROD_DB}"
)

# Use environment variables
# Never hardcode production credentials!
```

### Security Best Practices

1. **Never commit credentials** to Git
   - Use `.env` files (add to `.gitignore`)
   - Use Azure Key Vault / AWS Secrets Manager in production

2. **Different passwords** for dev vs prod

3. **Connection pooling** (already configured with `pool_pre_ping`)

4. **SSL/TLS** for production databases:
   ```python
   engine = create_engine(
       DATABASE_URL,
       connect_args={"ssl": {"ssl": True}}
   )
   ```

---

## Summary

**Development Setup:**
```bash
# 1. Install Docker
sudo apt install -y docker.io && sudo service docker start

# 2. Run SQL Server
docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=DevPassword123!" \
  -p 1433:1433 --name sqlserver -v sqlvolume:/var/opt/mssql \
  -d mcr.microsoft.com/mssql/server:2022-latest

# 3. Install Python packages
pip install sqlalchemy pymssql fastapi uvicorn

# 4. Update connection string
DATABASE_URL = "mssql+pymssql://sa:DevPassword123!@localhost/DevDB"
```

**Daily Usage:**
- Start: `docker start sqlserver`
- Stop: `docker stop sqlserver`
- Connect: VS Code extension or sqlcmd

**Key SQLAlchemy Changes:**
- Add length to strings: `String(200)`
- Remove `check_same_thread` (SQLite only)
- Use `pool_pre_ping=True`

---

Done! 🚀 You now have SQL Server running in Docker for local FastAPI development.
