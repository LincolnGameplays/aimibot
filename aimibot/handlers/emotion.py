# -*- coding: utf-8 -*-

"""
Handler de Emoções - AimiBOT

Este módulo é responsável por dar vida à Aimi, gerenciando seu estado
emocional em resposta às interações do usuário.

- Detecta a emoção do usuário através de palavras-chave e emojis.
- Armazena e recupera o estado emocional atual da Aimi (por usuário) no Redis.
- Modifica a emoção da Aimi com base na conversa.
"""

import logging
import re
import random
from telegram import Update
from telegram.ext import ContextTypes

# --- Importações Locais ---
import config
from utils import redis as cache

# --- Configuração do Logging ---
logger = logging.getLogger(__name__)

# --- MAPA DE GATILHOS EMOCIONAIS ---
# Mapeia emoções a padrões (regex) de palavras e emojis.
# A ordem é importante. A primeira emoção a atingir uma pontuação mínima vence.
EMOTION_TRIGGERS = {
    "provocante": {
        "keywords": [r"gostosa", r"safada", r"danada", r"atrevida"],
        "emojis": ["😏", "😈", "🔥"],
        "score": 2
    },
    "carinhosa": {
        "keywords": [r"amo você", r"te amo", r"gosto de você", r"minha linda", r"perfeita", r"abraço", r"beijo"],
        "emojis": ["❤️", "🥰", "😍", "😘"],
        "score": 1
    },
    "fofa": {
        "keywords": [r"fofa", r"own", r"que amor", r"bonitinha", r"querida"],
        "emojis": ["😊", "✨", "💕"],
        "score": 1
    },
    "envergonhada": {
        "keywords": [r"você corou", r"tímida", r"vergonha"],
        "emojis": ["😳", "👉👈"],
        "score": 2
    },
    "triste": {
        "keywords": [r"chata", r"idiota", r"odeio você", r"estou triste", r"sozinho"],
        "emojis": ["😢", "😭", "😞", "💔"],
        "score": 3 # Precisa de um gatilho mais forte para ficar triste
    }
}

# Tempo que a emoção de um usuário fica no cache (em segundos). 2 horas.
EMOTION_CACHE_TTL = 60 * 60 * 2

async def get_current_emotion(user_id: int) -> str:
    """
    Recupera a emoção atual da Aimi para um usuário específico do cache Redis.
    Retorna a emoção padrão se nenhuma for encontrada.
    """
    cache_key = f"aimi:emotion:{user_id}"
    cached_emotion = await cache.get(cache_key)
    if cached_emotion:
        logger.debug(f"[Emotion] Emoção encontrada no cache para {user_id}: {cached_emotion}")
        return cached_emotion
    
    logger.debug(f"[Emotion] Nenhuma emoção no cache para {user_id}. Usando padrão.")
    return config.EMOTION_DEFAULT

async def update_emotion(user_id: int, user_text: str, aimi_response: str) -> str:
    """
    Analisa o texto do usuário, determina a nova emoção e a salva no cache.
    """
    detected_emotion = config.EMOTION_DEFAULT # Começa com a emoção padrão
    highest_score = 0

    # Normaliza o texto para facilitar a detecção
    normalized_text = user_text.lower()

    for emotion, triggers in EMOTION_TRIGGERS.items():
        current_score = 0
        # Procura por palavras-chave
        for keyword in triggers["keywords"]:
            if re.search(keyword, normalized_text):
                current_score += triggers["score"]
        
        # Procura por emojis
        for emoji in triggers["emojis"]:
            if emoji in normalized_text:
                current_score += triggers["score"]

        if current_score > highest_score:
            highest_score = current_score
            detected_emotion = emotion

    # Se uma nova emoção foi detectada, atualiza no cache
    if highest_score > 0:
        logger.info(f"[Emotion Update] Emoção de {user_id} alterada para: {detected_emotion} (Score: {highest_score})")
        cache_key = f"aimi:emotion:{user_id}"
        await cache.setex(cache_key, EMOTION_CACHE_TTL, detected_emotion)
        return detected_emotion

    # Se nada foi detectado, retorna a emoção que já estava no cache
    return await get_current_emotion(user_id)

async def handle_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler para reações não-textuais, como stickers.
    (Funcionalidade a ser expandida no futuro)
    """
    user = update.effective_user
    sticker = update.message.sticker

    if sticker:
        logger.info(f"[Reaction] Usuário {user.first_name} enviou um sticker. Emoji: {sticker.emoji}, File ID: {sticker.file_id}")
        
        # Lógica futura: Aimi pode reagir a certos emojis de stickers
        # Por exemplo, se sticker.emoji == '❤️', Aimi pode mandar uma mensagem de volta.
        await update.message.reply_text("Que figurinha fofa! 🥰")

