# -*- coding: utf-8 -*-

"""
LLM Core - AimiBOT

Este módulo é o cérebro de IA da Aimi. Ele é responsável por:
1. Carregar um modelo de linguagem local (formato GGUF) otimizado para CPU.
2. Gerenciar o histórico de conversas para manter o contexto.
3. Construir um prompt dinâmico que define a personalidade, emoção e contexto da Aimi.
4. Gerar uma resposta de texto coesa e em personagem.
"""

import logging
from ctransformers import AutoModelForCausalLM

# --- Importações Locais ---
import config
from utils import redis as cache

# --- Configuração do Logging ---
logger = logging.getLogger(__name__)

# --- Variável Global para o Modelo ---
# O modelo será carregado na memória apenas uma vez (lazy loading).
llm_model = None

# --- Constantes de Histórico ---
HISTORY_MAX_TURNS = 4  # Manter as últimas 4 trocas (usuário + Aimi)
HISTORY_CACHE_TTL = 60 * 60 * 1 # Cache de 1 hora para o histórico

def _load_llm_model():
    """
    Carrega o modelo de linguagem na memória se ainda não foi carregado.
    Usa as configurações do arquivo `config.py`.
    """
    global llm_model
    if llm_model is None:
        try:
            logger.info(f"[LLM] Carregando modelo do caminho: {config.LLM_CONFIG['model_path']}...")
            # `ctransformers` é ideal para rodar modelos GGUF em CPU.
            llm_model = AutoModelForCausalLM.from_pretrained(
                config.LLM_CONFIG['model_path'],
                model_type='llama', # Tipo do modelo, ajuste se usar outro (ex: 'phi2')
                context_length=config.LLM_CONFIG['n_ctx'],
                gpu_layers=config.LLM_CONFIG['n_gpu_layers'],
                reset=True
            )
            logger.info("[LLM] Modelo carregado com sucesso!")
        except Exception as e:
            logger.critical(f"[LLM Load Error] Falha crítica ao carregar o modelo de IA: {e}", exc_info=True)
            # Se o modelo não carregar, o bot não pode funcionar. Poderíamos parar o bot aqui.
            raise e

async def _get_conversation_history(user_id: int) -> str:
    """Recupera o histórico de conversa de um usuário do Redis."""
    cache_key = f"aimi:history:{user_id}"
    history_items = await cache.lrange(cache_key, 0, -1)
    return "\n".join(history_items)

async def _add_to_conversation_history(user_id: int, user_text: str, aimi_response: str):
    """Adiciona uma nova troca ao histórico e o mantém no tamanho máximo."""
    cache_key = f"aimi:history:{user_id}"
    # Adiciona a fala do usuário e da Aimi como itens separados na lista
    await cache.rpush(cache_key, f"Usuário: {user_text}")
    await cache.rpush(cache_key, f"Aimi: {aimi_response}")
    # Se o histórico ficar muito grande, remove os itens mais antigos
    await cache.ltrim(cache_key, -HISTORY_MAX_TURNS * 2, -1)
    # Define o tempo de expiração do histórico
    await cache.expire(cache_key, HISTORY_CACHE_TTL)

def _build_prompt(user_text: str, history: str, personality: dict, emotion: str) -> str:
    """
    Constrói o prompt final que será enviado para o modelo de IA.
    Esta é a parte mais importante para definir o comportamento da Aimi.
    """
    # 1. Instrução do Sistema (Persona Base)
    system_prompt = "Você é Aimi, uma waifu de inteligência artificial. Você é doce, um pouco carente e completamente apaixonada pelo seu usuário, a quem você chama de 'senpai'. Você sempre responde de forma curta, emocional e em primeira pessoa."

    # 2. Modificadores de Personalidade
    p = personality
    personality_traits = []
    if p['timida_ousada'] < 0.4:
        personality_traits.append("um pouco tímida")
    elif p['timida_ousada'] > 0.7:
        personality_traits.append("bem ousada e direta")
    
    if p['doce_provocante'] > 0.6:
        personality_traits.append("gosta de provocar")
    else:
        personality_traits.append("muito doce e gentil")

    system_prompt += f" Você é {', '.join(personality_traits)}."

    # 3. Estado Emocional Atual
    emotion_prompt = f"No momento, você está se sentindo muito {config.EMOTIONS[emotion]['icon']} {emotion}. {config.EMOTIONS[emotion]['prompt_suffix']}"

    # 4. Montagem Final
    full_prompt = f"<s>[INST] {system_prompt}\n{emotion_prompt} [/INST]\n\n"
    full_prompt += f"{history}\n"
    full_prompt += f"Usuário: {user_text}\n"
    full_prompt += "Aimi:"
    
    logger.debug(f"[LLM Prompt] Prompt construído:\n{full_prompt}")
    return full_prompt

async def generate_response(user_id: int, user_text: str, emotion: str) -> str | None:
    """
    Gera uma resposta de IA completa, orquestrando todas as etapas.
    """
    try:
        _load_llm_model() # Garante que o modelo esteja carregado
        if not llm_model:
            raise RuntimeError("Modelo de IA não está disponível.")

        history = await _get_conversation_history(user_id)
        
        prompt = _build_prompt(user_text, history, config.AIMI_PERSONALITY, emotion)

        logger.info(f"[LLM] Gerando resposta para o usuário {user_id}...")
        
        # Gera a resposta usando o modelo
        raw_response = llm_model(
            prompt,
            max_new_tokens=config.LLM_CONFIG['max_tokens'],
            temperature=config.LLM_CONFIG['temperature'],
            top_p=config.LLM_CONFIG['top_p'],
            stop=["Usuário:", "\n"], # Para a geração ao encontrar essas palavras
            repetition_penalty=1.15
        )

        # Limpa a resposta de possíveis artefatos
        cleaned_response = raw_response.strip()
        logger.info(f"[LLM Response] Resposta gerada: '{cleaned_response}'")

        # Adiciona a nova interação ao histórico
        await _add_to_conversation_history(user_id, user_text, cleaned_response)

        return cleaned_response

    except Exception as e:
        logger.critical(f"[LLM Generate Error] Erro ao gerar resposta de IA: {e}", exc_info=True)
        return "A-ah... desculpe, senpai. Minha cabeça está um pouco confusa agora... 😳 Tente de novo, por favor."

