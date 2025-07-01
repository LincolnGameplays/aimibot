# -*- coding: utf-8 -*-

"""
Handler de Chat - AimiBOT

Este módulo é o coração da interação de roleplay. Ele orquestra:
1. A recepção da mensagem do usuário.
2. A verificação de permissões (trial, premium).
3. A chamada ao módulo de IA (`llm.py`) para gerar uma resposta textual.
4. A chamada ao módulo de TTS (`tts.py`) para converter o texto em voz.
5. O envio das respostas (texto e voz) de volta ao usuário.
6. A atualização do estado emocional da Aimi.
"""

import logging
from telegram import Update, ChatAction
from telegram.ext import ContextTypes

# --- Importações Locais ---
# Importamos os módulos que serão usados. Mesmo que ainda não existam,
# o Python só os carregará quando a função for chamada.
import config
from ai_core import llm
from handlers import tts, emotion
from utils import pg as db, redis as cache # Usando aliases para clareza

# --- Configuração do Logging ---
logger = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Processa todas as mensagens de texto recebidas que não são comandos.
    """
    user = update.effective_user
    message_text = update.message.text

    logger.info(f"[Chat] Mensagem recebida de {user.first_name} (ID: {user.id}): '{message_text}'")

    try:
        # --- ETAPA 1: Verificar permissão do usuário ---
        # (Esta função será implementada em `utils/pg.py`)
        has_access, reason = await db.check_user_access(user.id)
        
        if not has_access:
            # Se o usuário não tem acesso (ex: trial expirado), envia uma mensagem de upsell e para.
            await update.message.reply_text(reason)
            logger.warning(f"[Access Denied] Usuário {user.id} sem acesso. Motivo: {reason}")
            return

        # --- ETAPA 2: Feedback visual para o usuário ---
        # Informa ao usuário que o bot está "pensando".
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

        # --- ETAPA 3: Gerar a resposta da IA ---
        # (Esta função será implementada em `ai_core/llm.py`)
        # Ela considerará a personalidade da Aimi, o histórico e a emoção atual.
        current_emotion = await emotion.get_current_emotion(user.id)
        ai_response_text = await llm.generate_response(
            user_id=user.id,
            user_text=message_text,
            emotion=current_emotion
        )

        if not ai_response_text:
            logger.error("[LLM Error] A IA não retornou uma resposta.")
            await update.message.reply_text("Desculpe, senpai... não consigo pensar em nada agora. 😥")
            return

        # Envia a resposta em texto imediatamente.
        await update.message.reply_text(ai_response_text)

        # --- ETAPA 4: Gerar e enviar a voz ---
        # Informa que o bot está "gravando áudio".
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.RECORD_VOICE)

        # (Esta função será implementada em `handlers/tts.py`)
        # Ela gera o áudio, aplica efeitos e o salva em cache.
        voice_file = await tts.generate_voice(
            text=ai_response_text, 
            user_id=user.id, 
            emotion=current_emotion
        )

        if voice_file:
            with open(voice_file, 'rb') as voice:
                await update.message.reply_voice(voice=voice)
            # (Opcional: remover o arquivo de áudio local após o envio se não for mais necessário)
            # os.remove(voice_file)
        else:
            logger.error(f"[TTS Error] Não foi possível gerar o áudio para o texto: '{ai_response_text}'")

        # --- ETAPA 5: Atualizar a emoção da Aimi ---
        # A emoção da Aimi muda com base na conversa.
        # (Esta função será implementada em `handlers/emotion.py`)
        await emotion.update_emotion(
            user_id=user.id, 
            user_text=message_text, 
            aimi_response=ai_response_text
        )

    except Exception as e:
        logger.critical(f"[Chat Handler Error] Erro inesperado ao processar mensagem de {user.id}: {e}", exc_info=True)
        await update.message.reply_text("A-ah... aconteceu um erro aqui dentro, senpai. Tente de novo, por favor! 😳")

