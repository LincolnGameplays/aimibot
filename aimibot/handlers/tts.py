# -*- coding: utf-8 -*-

"""
Handler de TTS (Text-to-Speech) - AimiBOT

Responsável por converter texto em áudio com a voz da Aimi.
Funcionalidades:
1. Usa gTTS para gerar o áudio base.
2. Usa FFmpeg para aplicar efeitos de pitch (tom) e speed (velocidade).
3. Implementa um sistema de cache em Redis e no sistema de arquivos para
   evitar gerar o mesmo áudio múltiplas vezes.
4. Opera de forma assíncrona para não bloquear o bot.
"""

import logging
import os
import hashlib
import asyncio
from gtts import gTTS

# --- Importações Locais ---
import config
from utils import redis as cache

# --- Configuração do Logging ---
logger = logging.getLogger(__name__)

# --- Configuração do Cache de Áudio ---
# Define o diretório onde os arquivos de áudio finais serão salvos.
CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache', 'audio')
# Garante que o diretório de cache exista.
os.makedirs(CACHE_DIR, exist_ok=True)

# Tempo que o áudio fica no cache do Redis (em segundos). 1 semana.
REDIS_CACHE_TTL = 60 * 60 * 24 * 7

async def generate_voice(text: str, user_id: int, emotion: str) -> str | None:
    """
    Gera um arquivo de voz a partir de um texto, aplicando efeitos e usando cache.

    Args:
        text (str): O texto a ser convertido em voz.
        user_id (int): O ID do usuário (para futuras personalizações de idioma).
        emotion (str): A emoção atual da Aimi, para modular a voz.

    Returns:
        str | None: O caminho absoluto para o arquivo de áudio gerado (.ogg) ou None se ocorrer um erro.
    """
    try:
        # --- ETAPA 1: Determinar Idioma e Parâmetros da Voz ---
        # Por enquanto, usamos o padrão. No futuro, podemos detectar o idioma do usuário.
        lang_code = config.VOICE_CONFIG.get("default_lang", "pt-br")
        voice_params = config.VOICE_CONFIG["languages"].get(lang_code)
        
        if not voice_params:
            logger.error(f"[TTS] Configurações de voz não encontradas para o idioma: {lang_code}")
            return None

        # --- ETAPA 2: Criar Chave de Cache e Verificar Redis ---
        # A chave é um hash do conteúdo, garantindo que o mesmo texto/emoção/idioma
        # sempre resulte no mesmo arquivo.
        cache_key_hash = hashlib.md5(f"{text}-{lang_code}-{emotion}-{voice_params['pitch']}-{voice_params['speed']}".encode()).hexdigest()
        cache_key = f"aimi:voice:{cache_key_hash}"
        
        cached_file_path = await cache.get(cache_key)
        if cached_file_path and os.path.exists(cached_file_path):
            logger.info(f"[TTS Cache] Áudio encontrado no cache Redis para a chave: {cache_key}")
            return cached_file_path

        # --- ETAPA 3: Gerar Áudio Base com gTTS ---
        # Define os nomes dos arquivos temporário (input) e final (output).
        base_audio_path = os.path.join(CACHE_DIR, f"{cache_key_hash}_base.mp3")
        final_audio_path = os.path.join(CACHE_DIR, f"{cache_key_hash}.ogg")

        logger.info(f"[TTS] Gerando áudio base para: '{text[:30]}...'")
        tts_obj = gTTS(text=text, lang=lang_code, tld=voice_params['tld'], slow=False)
        tts_obj.save(base_audio_path)

        # --- ETAPA 4: Processar Áudio com FFmpeg ---
        # Constrói o comando do FFmpeg para alterar pitch e velocidade.
        # Usamos o codec 'libopus' que é ótimo para voz no Telegram.
        ffmpeg_command = [
            'ffmpeg',
            '-i', base_audio_path,
            '-y',  # Sobrescrever arquivo de saída se existir
            '-filter:a',
            f"asetrate={44100 * voice_params['pitch']},atempo={voice_params['speed']}",
            '-c:a', 'libopus',
            '-b:a', '48k', # Bitrate de 48kbps, bom para voz
            final_audio_path
        ]

        logger.info(f"[FFmpeg] Processando áudio com pitch={voice_params['pitch']} e speed={voice_params['speed']}")
        
        # Executa o comando FFmpeg de forma assíncrona.
        process = await asyncio.create_subprocess_exec(
            *ffmpeg_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error(f"[FFmpeg Error] Falha ao processar o áudio. Código: {process.returncode}")
            logger.error(f"[FFmpeg Stderr] {stderr.decode()}")
            return None

        # --- ETAPA 5: Limpeza e Cache ---
        os.remove(base_audio_path)  # Remove o arquivo base, pois não é mais necessário.
        await cache.setex(cache_key, REDIS_CACHE_TTL, final_audio_path) # Salva no Redis
        logger.info(f"[TTS] Áudio gerado e salvo em: {final_audio_path}")

        return final_audio_path

    except Exception as e:
        logger.critical(f"[TTS Handler Error] Erro inesperado ao gerar voz: {e}", exc_info=True)
        # Limpa arquivos temporários em caso de erro
        if 'base_audio_path' in locals() and os.path.exists(base_audio_path):
            os.remove(base_audio_path)
        return None

