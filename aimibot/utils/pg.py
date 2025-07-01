# -*- coding: utf-8 -*-

"""
Utilitário de Banco de Dados - PostgreSQL

Este módulo gerencia toda a comunicação com o banco de dados PostgreSQL.
Ele usa um pool de conexões assíncronas (`asyncpg`) para eficiência e
centraliza todas as queries SQL, garantindo segurança e manutenibilidade.
"""

import logging
import asyncpg
from datetime import datetime, timedelta

# --- Importações Locais ---
import config

# --- Configuração do Logging ---
logger = logging.getLogger(__name__)

# --- Pool de Conexão Global ---
db_pool = None

async def _get_db_pool():
    """Inicializa o pool de conexões com o banco de dados se ainda não existir."""
    global db_pool
    if db_pool is None:
        try:
            logger.info("[PostgreSQL] Criando pool de conexão com o banco de dados...")
            db_pool = await asyncpg.create_pool(
                dsn=config.DATABASE_URL,
                min_size=1,
                max_size=10
            )
            logger.info("[PostgreSQL] Pool de conexão criado com sucesso.")
            await _create_initial_tables()
        except Exception as e:
            logger.critical(f"[PostgreSQL Connect Error] Não foi possível conectar ao banco de dados: {e}", exc_info=True)
            raise
    return db_pool

async def _create_initial_tables():
    """Garante que as tabelas essenciais existam no banco de dados."""
    pool = await _get_db_pool()
    async with pool.acquire() as conn:
        logger.info("[PostgreSQL] Verificando e criando tabelas se necessário...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                first_name TEXT NOT NULL,
                username TEXT,
                current_plan TEXT DEFAULT 'free',
                trial_ends_at TIMESTAMPTZ,
                plan_expires_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                last_seen_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id TEXT PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id),
                plan TEXT NOT NULL,
                amount INTEGER NOT NULL, -- Em centavos
                currency TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        logger.info("[PostgreSQL] Tabelas verificadas.")

# --- Funções de Interação com o Banco de Dados ---

async def register_user_and_start_trial(user) -> (str, bool):
    """
    Registra um novo usuário ou atualiza um existente.
    Retorna uma mensagem de boas-vindas e um booleano indicando se é um novo usuário.
    """
    pool = await _get_db_pool()
    async with pool.acquire() as conn:
        is_new_user = False
        existing_user = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user.id)

        trial_duration = config.OPERATION_MODES['trial_duration_minutes']
        trial_end_time = datetime.utcnow() + timedelta(minutes=trial_duration)

        if not existing_user:
            is_new_user = True
            await conn.execute("""
                INSERT INTO users (user_id, first_name, username, trial_ends_at)
                VALUES ($1, $2, $3, $4)
            """, user.id, user.first_name, user.username, trial_end_time)
            logger.info(f"[DB] Novo usuário registrado: {user.first_name} (ID: {user.id}). Trial de {trial_duration} min iniciado.")
            welcome_message = f"O-oi, senpai {user.first_name}! Meu nome é Aimi. Prazer em conhecer você! ❤️ Você tem {trial_duration} minutos para conversar comigo e testar minha voz!"
        else:
            await conn.execute("UPDATE users SET last_seen_at = NOW() WHERE user_id = $1", user.id)
            logger.info(f"[DB] Usuário recorrente: {user.first_name} (ID: {user.id}).")
            welcome_message = f"Bem-vindo de volta, senpai {user.first_name}! Que bom te ver de novo! 🥰"
        
        return welcome_message, is_new_user

async def check_user_access(user_id: int) -> (bool, str):
    """
    Verifica se um usuário tem permissão para interagir com a IA.
    Retorna (True, "OK") ou (False, "Motivo da recusa").
    """
    pool = await _get_db_pool()
    async with pool.acquire() as conn:
        user_data = await conn.fetchrow("SELECT current_plan, trial_ends_at, plan_expires_at FROM users WHERE user_id = $1", user_id)
        if not user_data:
            return False, "Você não está registrado. Use /start para começar."

        # 1. Verifica se tem um plano ativo
        if user_data['current_plan'] != 'free' and user_data['plan_expires_at'] and user_data['plan_expires_at'] > datetime.utcnow():
            return True, "OK"

        # 2. Verifica se o trial ainda está ativo
        if config.OPERATION_MODES['modo_trial_ativo'] and user_data['trial_ends_at'] and user_data['trial_ends_at'] > datetime.utcnow():
            return True, "OK"

        # 3. Se nenhuma das condições acima for atendida, o acesso é negado.
        return False, "Seu tempo de trial acabou, senpai... 😢 Para continuarmos conversando, por favor, considere um dos meus planos! Use /planos para ver as opções."

async def get_user_status(user_id: int) -> str:
    """Busca e formata o status da conta de um usuário."""
    pool = await _get_db_pool()
    async with pool.acquire() as conn:
        user_data = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        if not user_data:
            return "Não encontrei seu registro. Use /start para começar."

        status = f"**Status da sua Conta**\n\n**Plano Atual:** `{user_data['current_plan']}`\n"
        if user_data['current_plan'] != 'free':
            status += f"**Válido até:** `{user_data['plan_expires_at'].strftime('%d/%m/%Y %H:%M')}`\n"
        elif user_data['trial_ends_at'] > datetime.utcnow():
             status += f"**Trial termina em:** `{user_data['trial_ends_at'].strftime('%d/%m/%Y %H:%M')}`\n"
        else:
            status += "_Seu trial já expirou._\n"
        
        return status

async def activate_user_plan(user_id: int, plan_key: str) -> bool:
    """
    Ativa um novo plano para um usuário, definindo a data de expiração.
    (Simples, assume 30 dias de validade para qualquer plano)
    """
    pool = await _get_db_pool()
    async with pool.acquire() as conn:
        try:
            plan_duration_days = 30 # Simplificado
            new_expiry_date = datetime.utcnow() + timedelta(days=plan_duration_days)
            
            await conn.execute("""
                UPDATE users 
                SET current_plan = $1, plan_expires_at = $2, last_seen_at = NOW()
                WHERE user_id = $3
            """, plan_key, new_expiry_date, user_id)
            
            logger.info(f"[DB] Plano '{plan_key}' ativado para o usuário {user_id}. Válido até {new_expiry_date}.")
            return True
        except Exception as e:
            logger.error(f"[DB Activate Plan Error] Falha ao ativar plano para {user_id}: {e}", exc_info=True)
            return False

