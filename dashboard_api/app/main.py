# Backend da Dashboard AimiAI - app/main.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import socketio

# --- Importações dos Routers ---
# from .routers import stripe_webhook, bot_commands

# --- Configuração do Socket.IO ---
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

# --- Aplicação FastAPI ---
app = FastAPI(title="AimiAI Dashboard API")

# Monta o servidor Socket.IO com a aplicação FastAPI
app.mount("/ws", socketio.ASGIApp(sio))

# --- Middlewares ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://dash.aimiai.com"], # Adicione a URL do seu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Eventos do WebSocket ---
@sio.event
async def connect(sid, environ):
    print(f"[Socket.IO] Cliente conectado: {sid}")

@sio.event
async def disconnect(sid):
    print(f"[Socket.IO] Cliente desconectado: {sid}")

# Exemplo de como emitir um evento (será chamado pelo webhook do Stripe)
async def notify_sale(data):
    await sio.emit('sale_created', data)
    print(f"[Socket.IO] Evento 'sale_created' emitido com dados: {data}")

# --- Rotas da API ---
@app.get("/")
async def read_root():
    return {"message": "AimiAI Dashboard API está online."}

# Exemplo de rota que pode ser chamada pelo webhook do Stripe
@app.post("/stripe-webhook-placeholder")
async def stripe_webhook_placeholder():
    # Lógica do webhook aqui...
    sale_data = {"product": "Aimi Premium", "amount": "R$ 29,90", "user": "Usuário Exemplo"}
    await notify_sale(sale_data)
    return {"status": "webhook received"}

# Inclui os outros routers da aplicação
# app.include_router(stripe_webhook.router)
# app.include_router(bot_commands.router)
