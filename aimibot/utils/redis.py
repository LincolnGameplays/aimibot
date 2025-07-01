# -*- coding: utf-8 -*-

"""
Utilitário de Cache - Redis

Este módulo centraliza a conexão e a interação com o servidor Redis.
Ele fornece funções assíncronas para operações comuns de cache, como
GET, SET, e manipulação de listas, usadas em várias partes do bot.
"""

import logging
import redis.asyncio as redis

# --- Importações Locais ---
import config

# --- Configuração do Logging ---
logger = logging.getLogger(__name__)

# --- Pool de Conexão ---
# Criar um pool de conexão é mais eficiente do que criar uma nova conexão a cada vez.
redis_pool = None

def _get_redis_pool():
    """Inicializa o pool de conexão Redis se ainda não existir."""
    global redis_pool
    if redis_pool is None:
        try:
            logger.info("[Redis] Criando pool de conexão com o Redis...")
            # Idealmente, as configurações de host e porta viriam do config.py
            redis_pool = redis.ConnectionPool.from_url(
                "redis://localhost:6379/0", # Altere para o URL do seu Redis Cloud se necessário
                decode_responses=True # Decodifica respostas de bytes para string automaticamente
            )
            logger.info("[Redis] Pool de conexão criado com sucesso.")
        except Exception as e:
            logger.critical(f"[Redis Connect Error] Não foi possível conectar ao Redis: {e}", exc_info=True)
            raise
    return redis_pool

async def get_client():
    """Retorna um cliente Redis do pool de conexão."""
    return redis.Redis(connection_pool=_get_redis_pool())

# --- Funções de Wrapper para Comandos Comuns ---

async def get(key: str) -> str | None:
    """Busca um valor no cache Redis pela chave."""
    try:
        r = await get_client()
        return await r.get(key)
    except Exception as e:
        logger.error(f"[Redis GET Error] Falha ao buscar a chave '{key}': {e}")
        return None

async def setex(key: str, ttl_seconds: int, value: str) -> bool:
    """Define um valor no cache Redis com um tempo de expiração (TTL)."""
    try:
        r = await get_client()
        await r.setex(key, ttl_seconds, value)
        return True
    except Exception as e:
        logger.error(f"[Redis SETEX Error] Falha ao definir a chave '{key}': {e}")
        return False

async def rpush(key: str, value: str) -> int:
    """Adiciona um valor ao final de uma lista no Redis."""
    try:
        r = await get_client()
        return await r.rpush(key, value)
    except Exception as e:
        logger.error(f"[Redis RPUSH Error] Falha ao adicionar na lista '{key}': {e}")
        return 0

async def lrange(key: str, start: int, end: int) -> list:
    """Retorna um range de itens de uma lista do Redis."""
    try:
        r = await get_client()
        return await r.lrange(key, start, end)
    except Exception as e:
        logger.error(f"[Redis LRANGE Error] Falha ao buscar a lista '{key}': {e}")
        return []

async def ltrim(key: str, start: int, end: int) -> bool:
    """Corta uma lista do Redis, mantendo apenas os itens entre start e end."""
    try:
        r = await get_client()
        await r.ltrim(key, start, end)
        return True
    except Exception as e:
        logger.error(f"[Redis LTRIM Error] Falha ao cortar a lista '{key}': {e}")
        return False

async def expire(key: str, ttl_seconds: int) -> bool:
    """Define um tempo de expiração para uma chave existente."""
    try:
        r = await get_client()
        await r.expire(key, ttl_seconds)
        return True
    except Exception as e:
        logger.error(f"[Redis EXPIRE Error] Falha ao definir TTL para a chave '{key}': {e}")
        return False

logger.info("Módulo de utilidades Redis carregado.")

