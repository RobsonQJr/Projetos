# Ateliê Roberta Severo — Loja de Crochê

## Como rodar

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

---

## Como testar o webhook localmente (ngrok)

O Mercado Pago precisa de uma URL pública para enviar a notificação de pagamento.
Em desenvolvimento, use o **ngrok** para criar um túnel temporário:

### 1. Instalar o ngrok
Baixe em: https://ngrok.com/download  
Ou via npm: `npm install -g ngrok`

### 2. Abrir o túnel (em outro terminal, com o uvicorn já rodando)
```bash
ngrok http 8000
```
O ngrok vai mostrar uma URL do tipo:
```
Forwarding  https://abc123.ngrok-free.app -> http://127.0.0.1:8000
```

### 3. Copiar essa URL para o .env
```
WEBHOOK_URL=https://abc123.ngrok-free.app
```

### 4. Reiniciar o uvicorn
```
CTRL+C  →  uvicorn main:app --reload
```

Pronto! Na próxima compra aprovada, o MP vai chamar:
`POST https://abc123.ngrok-free.app/webhook/mp`
e o email será enviado automaticamente para a artesã.

---

## Estrutura dos arquivos

| Arquivo | Função |
|---|---|
| `main.py` | Loja FastAPI + webhook + email |
| `admin.py` | Painel Streamlit (cadastro de produtos) |
| `models.py` | Modelos do banco (Produto, Pedido) |
| `database.py` | Conexão PostgreSQL via SQLAlchemy |
| `templates/` | HTML com Tailwind CSS |
| `.env` | Variáveis de configuração |

---

## Observações

- O **Gmail** precisa de **App Password** (não a senha normal).  
  Gere em: myaccount.google.com → Segurança → Senhas de app
- Em produção, troque `BASE_URL` e `WEBHOOK_URL` pelo domínio real
- O token `TEST-` é para testes (sandbox). Em produção use o `APP_USR-`
