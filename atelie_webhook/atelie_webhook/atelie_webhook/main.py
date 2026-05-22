import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import quote

from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import mercadopago
from dotenv import load_dotenv

import models
import database
from database import get_db

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")


def is_localhost(url: str) -> bool:
    return "127.0.0.1" in url or "localhost" in url


# ─────────────────────────────────────────
#  LOJA
# ─────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    produtos = db.query(models.Produto).all()
    return templates.TemplateResponse(
        request=request,
        name="loja.html",
        context={"produtos": produtos, "whatsapp_num": os.getenv("WHATSAPP_NUM", "")}
    )


@app.get("/checkout/{produto_id}", response_class=HTMLResponse)
async def exibir_checkout(request: Request, produto_id: int, db: Session = Depends(get_db)):
    produto = db.query(models.Produto).filter(models.Produto.id == produto_id).first()
    if not produto:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="checkout.html",
        context={"produto": produto}
    )


@app.post("/processar_pedido/{produto_id}")
async def processar_pedido(
    produto_id: int,
    nome: str = Form(...),
    email: str = Form(...),
    telefone: str = Form(...),
    cep: str = Form(...),
    endereco: str = Form(...),
    db: Session = Depends(get_db)
):
    produto = db.query(models.Produto).filter(models.Produto.id == produto_id).first()
    if not produto:
        return RedirectResponse(url="/", status_code=303)

    valor_frete = 25.00 if cep.startswith("0") else 45.00
    valor_total = produto.preco + valor_frete

    novo_pedido = models.Pedido(
        produto_id=produto.id,
        nome_cliente=nome,
        email_cliente=email,
        telefone=telefone,
        endereco_completo=f"{endereco}, CEP: {cep}",
        valor_produto=produto.preco,
        valor_frete=valor_frete,
        valor_total=valor_total,
        status="pendente"
    )
    db.add(novo_pedido)
    db.commit()
    db.refresh(novo_pedido)

    # URL do webhook — deve ser pública (ngrok em dev, domínio em produção)
    webhook_url = os.getenv("WEBHOOK_URL", "").strip()

    preference_data = {
        "items": [
            {
                "id": str(produto.id),
                "title": produto.nome[:250],
                "quantity": 1,
                "unit_price": float(produto.preco),
                "currency_id": "BRL"
            },
            {
                "id": "frete",
                "title": "Frete",
                "quantity": 1,
                "unit_price": float(valor_frete),
                "currency_id": "BRL"
            }
        ],
        "payer": {
            "email": email,
            "name": nome,
            "phone": {"number": telefone}
        },
        "external_reference": str(novo_pedido.id),
        "back_urls": {
            "success": f"{BASE_URL}/confirmacao/{novo_pedido.id}",
            "failure": f"{BASE_URL}/",
            "pending": f"{BASE_URL}/"
        },
    }

    # auto_return só funciona com domínio público
    if not is_localhost(BASE_URL):
        preference_data["auto_return"] = "approved"

    # Webhook: só adiciona se houver URL configurada e acessível publicamente
    if webhook_url and not is_localhost(webhook_url):
        preference_data["notification_url"] = f"{webhook_url}/webhook/mp"

    preference_response = sdk.preference().create(preference_data)

    if preference_response["status"] != 201:
        erro = preference_response.get("response", {})
        return HTMLResponse(
            content=f"<h2>Erro ao criar pagamento.</h2><pre>{erro}</pre><a href='/'>← Voltar</a>",
            status_code=500
        )

    resposta = preference_response["response"]
    url_pagamento = (
        resposta.get("sandbox_init_point", resposta.get("init_point"))
        if is_localhost(BASE_URL)
        else resposta["init_point"]
    )

    return RedirectResponse(url_pagamento, status_code=303)


# ─────────────────────────────────────────
#  WEBHOOK — recebe notificação do MP
# ─────────────────────────────────────────

@app.post("/webhook/mp")
async def webhook_mercadopago(request: Request, db: Session = Depends(get_db)):
    """
    O Mercado Pago chama este endpoint automaticamente quando o status
    de um pagamento muda. O MP só manda o ID — buscamos os detalhes
    completos na API deles e então enviamos o email se aprovado.
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "erro": "body inválido"}, status_code=400)

    print(f"[WEBHOOK] Recebido: {body}")

    # O MP envia: {"type": "payment", "data": {"id": "123456789"}, ...}
    tipo = body.get("type") or body.get("topic", "")
    payment_id = (
        body.get("data", {}).get("id")
        or request.query_params.get("id")
        or request.query_params.get("data.id")
    )

    if tipo != "payment" or not payment_id:
        # Outros eventos (merchant_order, etc.) — ignoramos e retornamos 200
        return JSONResponse({"ok": True, "msg": "evento ignorado"})

    # Consulta os detalhes reais do pagamento na API do MP
    payment_info = sdk.payment().get(payment_id)
    if payment_info["status"] != 200:
        print(f"[WEBHOOK] Erro ao buscar pagamento {payment_id}: {payment_info}")
        return JSONResponse({"ok": False}, status_code=200)  # 200 p/ MP não retentar

    pagamento = payment_info["response"]
    status_mp = pagamento.get("status")
    external_reference = pagamento.get("external_reference")

    print(f"[WEBHOOK] Pagamento {payment_id} | status={status_mp} | ref={external_reference}")

    # Só processa pagamentos APROVADOS
    if status_mp != "approved":
        return JSONResponse({"ok": True, "msg": f"status {status_mp} ignorado"})

    if not external_reference:
        return JSONResponse({"ok": False, "msg": "sem external_reference"})

    # Busca o pedido no banco pelo ID que passamos como external_reference
    pedido = db.query(models.Pedido).filter(
        models.Pedido.id == int(external_reference)
    ).first()

    if not pedido:
        print(f"[WEBHOOK] Pedido {external_reference} não encontrado no banco")
        return JSONResponse({"ok": False, "msg": "pedido não encontrado"})

    # Evita processar o mesmo pedido duas vezes
    if pedido.status == "pago":
        print(f"[WEBHOOK] Pedido {pedido.id} já estava como pago — ignorando")
        return JSONResponse({"ok": True, "msg": "já processado"})

    # Atualiza status no banco
    pedido.status = "pago"
    db.commit()

    # Busca o produto para incluir no email
    produto = db.query(models.Produto).filter(models.Produto.id == pedido.produto_id).first()

    # Envia o email de notificação para a artesã
    try:
        enviar_email_venda(pedido, produto, pagamento)
        print(f"[WEBHOOK] Email enviado para {os.getenv('EMAIL_ARTESA')} — pedido #{pedido.id}")
    except Exception as e:
        print(f"[WEBHOOK] Falha ao enviar email: {e}")

    return JSONResponse({"ok": True, "msg": f"pedido {pedido.id} processado"})


# ─────────────────────────────────────────
#  PÁGINA DE CONFIRMAÇÃO (fallback visual)
# ─────────────────────────────────────────

@app.get("/confirmacao/{pedido_id}")
async def confirmacao_venda(pedido_id: int, db: Session = Depends(get_db)):
    """
    O cliente cai aqui após o pagamento. O email já foi (ou será)
    disparado pelo webhook. Esta página é só o feedback visual.
    """
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        return RedirectResponse(url="/")

    produto = db.query(models.Produto).filter(models.Produto.id == pedido.produto_id).first()

    msg_zap = (
        f"Novo Pedido!\n\n"
        f"Pedido: #{pedido.id}\n"
        f"Produto: {produto.nome if produto else 'N/A'}\n"
        f"Total: R$ {pedido.valor_total:.2f}\n"
        f"Cliente: {pedido.nome_cliente}\n"
        f"Endereco: {pedido.endereco_completo}"
    )
    whatsapp_url = f"https://wa.me/{os.getenv('WHATSAPP_NUM')}?text={quote(msg_zap)}"

    html_content = f"""
    <html>
        <head><meta charset="UTF-8"></head>
        <body style="text-align:center;font-family:sans-serif;padding-top:50px;">
            <h1 style="color:#059669;">Pagamento Confirmado! 🎉</h1>
            <p>Obrigado, {pedido.nome_cliente}! Seu pedido foi registrado com sucesso.</p>
            <p>Redirecionando para o WhatsApp da artesã em instantes...</p>
            <script>
                setTimeout(function() {{ window.location.href = "{whatsapp_url}"; }}, 4000);
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# ─────────────────────────────────────────
#  EMAIL
# ─────────────────────────────────────────

def enviar_email_venda(pedido, produto, pagamento_mp: dict = None):
    email_artesa = os.getenv("EMAIL_ARTESA")
    senha_email = os.getenv("EMAIL_PASSWORD")

    nome_produto = produto.nome if produto else "Produto removido"

    # Método de pagamento (vem da resposta do MP)
    metodo = "—"
    if pagamento_mp:
        metodo = pagamento_mp.get("payment_type_id", "—")
        metodo_map = {
            "credit_card": "Cartão de Crédito",
            "debit_card": "Cartão de Débito",
            "account_money": "Saldo Mercado Pago",
            "pix": "Pix",
            "ticket": "Boleto",
        }
        metodo = metodo_map.get(metodo, metodo)

    msg = MIMEMultipart("alternative")
    msg["From"] = email_artesa
    msg["To"] = email_artesa
    msg["Subject"] = f"🛍️ NOVA VENDA — Pedido #{pedido.id} | {nome_produto}"

    # Corpo em texto simples (fallback)
    corpo_txt = f"""
Nova venda realizada!

━━━━━━━━━━━━━━━━━━━━━
PRODUTO
━━━━━━━━━━━━━━━━━━━━━
Produto : {nome_produto}
Valor   : R$ {pedido.valor_produto:.2f}
Frete   : R$ {pedido.valor_frete:.2f}
TOTAL   : R$ {pedido.valor_total:.2f}
Pagamento: {metodo}

━━━━━━━━━━━━━━━━━━━━━
DADOS DO CLIENTE
━━━━━━━━━━━━━━━━━━━━━
Nome     : {pedido.nome_cliente}
E-mail   : {pedido.email_cliente}
Telefone : {pedido.telefone}
Endereço : {pedido.endereco_completo}

━━━━━━━━━━━━━━━━━━━━━
Pedido #{pedido.id} — confirmado pelo Mercado Pago
"""

    # Corpo em HTML (bonito)
    corpo_html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f5f5f4;font-family:Georgia,serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:30px 10px;">
      <table width="560" cellpadding="0" cellspacing="0"
             style="background:#fff;border-radius:12px;overflow:hidden;
                    box-shadow:0 2px 8px rgba(0,0,0,.08);">

        <!-- Cabeçalho -->
        <tr>
          <td style="background:#78350f;padding:28px 32px;text-align:center;">
            <h1 style="margin:0;color:#fef3c7;font-size:22px;letter-spacing:1px;">
              🧶 Ateliê Roberta Severo
            </h1>
            <p style="margin:6px 0 0;color:#fde68a;font-size:13px;">
              Nova venda confirmada!
            </p>
          </td>
        </tr>

        <!-- Badge de aprovação -->
        <tr>
          <td style="padding:24px 32px 0;text-align:center;">
            <span style="display:inline-block;background:#d1fae5;color:#065f46;
                         border-radius:999px;padding:8px 20px;font-size:14px;font-weight:bold;">
              ✅ Pagamento Aprovado via {metodo}
            </span>
          </td>
        </tr>

        <!-- Produto -->
        <tr>
          <td style="padding:24px 32px 0;">
            <p style="margin:0 0 8px;font-size:11px;text-transform:uppercase;
                      letter-spacing:1px;color:#a8a29e;">Produto</p>
            <table width="100%" style="background:#fafaf9;border-radius:8px;
                                       border:1px solid #e7e5e4;border-collapse:collapse;">
              <tr>
                <td style="padding:14px 16px;color:#44403c;font-size:15px;font-weight:bold;">
                  {nome_produto}
                </td>
              </tr>
              <tr style="border-top:1px solid #e7e5e4;">
                <td style="padding:12px 16px;">
                  <table width="100%">
                    <tr>
                      <td style="color:#78716c;font-size:13px;">Valor do produto</td>
                      <td align="right" style="color:#44403c;font-size:13px;">
                        R$ {pedido.valor_produto:.2f}
                      </td>
                    </tr>
                    <tr>
                      <td style="color:#78716c;font-size:13px;padding-top:6px;">Frete</td>
                      <td align="right" style="color:#44403c;font-size:13px;padding-top:6px;">
                        R$ {pedido.valor_frete:.2f}
                      </td>
                    </tr>
                    <tr>
                      <td style="color:#292524;font-size:15px;font-weight:bold;
                                 padding-top:10px;border-top:1px solid #e7e5e4;">
                        Total pago
                      </td>
                      <td align="right" style="color:#15803d;font-size:17px;font-weight:bold;
                                               padding-top:10px;border-top:1px solid #e7e5e4;">
                        R$ {pedido.valor_total:.2f}
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Cliente -->
        <tr>
          <td style="padding:20px 32px 0;">
            <p style="margin:0 0 8px;font-size:11px;text-transform:uppercase;
                      letter-spacing:1px;color:#a8a29e;">Dados do cliente</p>
            <table width="100%" style="background:#fafaf9;border-radius:8px;
                                       border:1px solid #e7e5e4;border-collapse:collapse;">
              <tr>
                <td style="padding:12px 16px;">
                  <table width="100%" style="font-size:13px;color:#44403c;border-collapse:collapse;">
                    <tr>
                      <td style="padding:4px 0;color:#78716c;width:90px;">Nome</td>
                      <td style="padding:4px 0;font-weight:bold;">{pedido.nome_cliente}</td>
                    </tr>
                    <tr>
                      <td style="padding:4px 0;color:#78716c;">E-mail</td>
                      <td style="padding:4px 0;">
                        <a href="mailto:{pedido.email_cliente}"
                           style="color:#0369a1;">{pedido.email_cliente}</a>
                      </td>
                    </tr>
                    <tr>
                      <td style="padding:4px 0;color:#78716c;">Telefone</td>
                      <td style="padding:4px 0;">{pedido.telefone}</td>
                    </tr>
                    <tr>
                      <td style="padding:4px 0;color:#78716c;vertical-align:top;">Endereço</td>
                      <td style="padding:4px 0;">{pedido.endereco_completo}</td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Rodapé -->
        <tr>
          <td style="padding:24px 32px 32px;text-align:center;">
            <p style="margin:0;font-size:12px;color:#a8a29e;">
              Pedido #{pedido.id} — confirmado automaticamente pelo Mercado Pago
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>
"""

    msg.attach(MIMEText(corpo_txt, "plain", "utf-8"))
    msg.attach(MIMEText(corpo_html, "html", "utf-8"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(email_artesa, senha_email)
        server.send_message(msg)
