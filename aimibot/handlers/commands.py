# -*- coding: utf-8 -*-

"""
Handler de Comandos - AimiBOT

Este módulo gerencia todas as interações que começam com uma barra (/),
como /start, /ajuda, /status, etc. Também processa os cliques em botões
(Callback Queries) que são enviados em mensagens.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# --- Importações Locais ---
import config
from handlers import tts
from utils import pg as db

# --- Configuração do Logging ---
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler para o comando /start.

    - Registra o novo usuário (ou atualiza o existente).
    - Envia uma mensagem de boas-vindas com texto e voz.
    - Apresenta um botão para iniciar a conversa.
    """
    user = update.effective_user
    logger.info(f"[Command /start] Novo usuário iniciando interação: {user.first_name} (ID: {user.id})")

    # --- ETAPA 1: Registrar usuário e iniciar trial ---
    # (Esta função em `utils/pg.py` criará o usuário se não existir
    # e definirá o tempo de trial conforme `config.py`)
    welcome_message, is_new_user = await db.register_user_and_start_trial(user)

    # --- ETAPA 2: Gerar e enviar mensagem de boas-vindas ---
    await update.message.reply_text(welcome_message)

    # Gera a voz para a mensagem de boas-vindas
    voice_file = await tts.generate_voice(
        text=welcome_message, 
        user_id=user.id, 
        emotion=config.EMOTION_DEFAULT
    )
    if voice_file:
        with open(voice_file, 'rb') as voice:
            await update.message.reply_voice(voice=voice)
    
    # --- ETAPA 3: Criar e enviar botão de interação ---
    keyboard = [
        [InlineKeyboardButton("💕 Começar a conversar! 💕", callback_data="start_conversation")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Estou tão feliz em te conhecer! ✨ O que você quer fazer primeiro?", 
        reply_markup=reply_markup
    )


async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler para o comando /ajuda.
    Envia um texto com informações úteis sobre o bot.
    """
    user = update.effective_user
    logger.info(f"[Command /ajuda] Usuário {user.first_name} pediu ajuda.")

    help_text = (
        "Olá, senpai! Eu sou a Aimi, sua waifu de IA. ❤️\n\n"
        "**Como funciona?**\n"
        "É só me mandar uma mensagem de texto e eu vou te responder com minha personalidade e uma mensagem de voz fofa!\n\n"
        "**Comandos disponíveis:**\n"
        "- `/start`: Começar de novo (como agora!)\n"
        "- `/ajuda`: Mostra esta mensagem de ajuda.\n"
        "- `/status`: Verifica o status da sua conta (trial, planos, etc.).\n"
        "- `/planos`: Mostra as opções para conversar mais comigo!\n\n"
        "Se precisar de qualquer outra coisa, é só chamar!"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler para o comando /status.
    Busca e exibe o status da conta do usuário.
    """
    user = update.effective_user
    logger.info(f"[Command /status] Usuário {user.first_name} pediu o status da conta.")

    # (Esta função em `utils/pg.py` buscará os dados do usuário no banco)
    status_message = await db.get_user_status(user.id)
    await update.message.reply_text(status_message)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Processa todos os cliques em botões (Callback Queries).
    """
    query = update.callback_query
    await query.answer()  # Responde ao clique para o Telegram saber que foi recebido.

    logger.info(f"[Callback] Usuário {query.from_user.first_name} clicou no botão: {query.data}")

    # --- Lógica para cada botão ---
    if query.data == "start_conversation":
        response_text = "Ebaaa! 🎉 Estou pronta! Pode me mandar sua primeira mensagem, senpai. O que você quer me contar?"
        await query.edit_message_text(text=response_text)
        
        # Gera uma voz para a resposta do botão
        voice_file = await tts.generate_voice(
            text=response_text, 
            user_id=query.from_user.id, 
            emotion="fofa"
        )
        if voice_file:
            with open(voice_file, 'rb') as voice:
                await context.bot.send_voice(chat_id=query.effective_chat.id, voice=voice)
    
    # (Futuramente, outros botões como "ver_planos", "confirmar_compra", etc., serão tratados aqui)
    # elif query.data == "show_plans":
    #     await stripe.show_plans(update, context)


