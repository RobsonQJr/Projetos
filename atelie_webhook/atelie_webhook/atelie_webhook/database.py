import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# Pegamos a URL e limpamos espaços ou aspas acidentais
raw_url = os.getenv("DATABASE_URL")
if raw_url:
    # Remove aspas simples, duplas e espaços em branco que podem vir do .env
    db_url = raw_url.replace('"', '').replace("'", "").strip()
else:
    raise ValueError("DATABASE_URL não definida no arquivo .env")

# Criamos o engine
engine = create_engine(
    db_url,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()  # CORRIGIDO: importado de sqlalchemy.orm (não depreciado)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
