from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime
from datetime import datetime, timezone
from database import Base, engine

class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text)
    preco = Column(Float, nullable=False)
    estoque = Column(Integer, default=0)
    imagem_url = Column(String(500))
    categoria = Column(String(50))

class Pedido(Base):
    __tablename__ = "pedidos"
    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"))
    nome_cliente = Column(String(100))
    email_cliente = Column(String(100))
    telefone = Column(String(20))
    endereco_completo = Column(String(500))
    valor_produto = Column(Float)
    valor_frete = Column(Float)
    valor_total = Column(Float)
    status = Column(String(20), default="pendente")
    # CORRIGIDO: datetime.utcnow depreciado no Python 3.11+ → usar timezone-aware
    data_criacao = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# Cria as tabelas no banco de dados se não existirem
Base.metadata.create_all(bind=engine)
