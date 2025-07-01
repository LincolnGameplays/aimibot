# -*- coding: utf-8 -*-

# --- TOKENS E CHAVES ---
# Adicione seus tokens e chaves aqui. NUNCA os exponha publicamente.
TELEGRAM_TOKEN = "SEU_TOKEN_AQUI"  # Token do Bot do Telegram
STRIPE_API_KEY = "SUA_CHAVE_SECRETA_AQUI"  # Chave secreta do Stripe
STRIPE_WEBHOOK_SECRET = "SEU_WEBHOOK_SECRET_AQUI" # Secret do Webhook para verificação

# --- CONFIGURAÇÕES DO BANCO DE DADOS (PostgreSQL via Supabase) ---
DB_USER = "postgres"
DB_PASSWORD = "SUA_SENHA_DO_BANCO_AQUI"
DB_HOST = "db.xxxxxxxxxxxxxxxxxxxx.supabase.co" # Host do Supabase
DB_PORT = "5432"
DB_NAME = "postgres"
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# --- CONFIGURAÇÕES DE VOZ (gTTS + FFmpeg) ---
VOICE_CONFIG = {
    "default_lang": "pt-br",
    "languages": {
        "pt-br": {"pitch": 1.2, "speed": 0.9, "tld": "com.br"},
        "en": {"pitch": 1.5, "speed": 1.1, "tld": "com"},
        "es": {"pitch": 1.1, "speed": 1.0, "tld": "es"},
        "ja": {"pitch": 1.8, "speed": 1.2, "tld": "co.jp"}
    }
}

# --- CONFIGURAÇÕES DE EMOÇÃO ---
EMOTION_DEFAULT = "carinhosa"
EMOTIONS = {
    "carinhosa": {"icon": "❤️", "prompt_suffix": "com um tom carinhoso e doce."},
    "provocante": {"icon": "😏", "prompt_suffix": "com um tom provocante e um pouco atrevido."},
    "triste": {"icon": "😢", "prompt_suffix": "com um tom triste e vulnerável."},
    "fofa": {"icon": "🥰", "prompt_suffix": "com um tom extremamente fofo e inocente."},
    "envergonhada": {"icon": "😳", "prompt_suffix": "com um tom envergonhado e tímido."}
}

# --- PERSONALIDADE DA AIMI (AimiTrainer) ---
# Valores de 0.0 a 1.0 que influenciam o prompt do LLM
AIMI_PERSONALITY = {
    "timida_ousada": 0.3,      # 0.0 = Tímida, 1.0 = Ousada
    "doce_provocante": 0.2,   # 0.0 = Doce, 1.0 = Provocante
    "seria_carinhosa": 0.8,   # 0.0 = Séria, 1.0 = Carinhosa
    "gírias_pt-br": True,     # Usar gírias locais?
    "gírias_en": False
}

# --- CONFIGURAÇÕES DO LLM (Modelo de Linguagem Local) ---
LLM_CONFIG = {
    "model_path": "caminho/para/seu/modelo_local", # Ex: ./models/TinyLlama-1.1B-Chat-v1.0.Q4_K_M.gguf
    "n_ctx": 2048,  # Contexto máximo do modelo
    "n_gpu_layers": 0, # 0 para rodar 100% na CPU
    "max_tokens": 150, # Máximo de tokens na resposta
    "temperature": 0.8,
    "top_p": 0.95
}


# --- MODOS DE OPERAÇÃO ---
# Ative ou desative funcionalidades globais do bot
OPERATION_MODES = {
    "modo_trial_ativo": True,
    "trial_duration_minutes": 5, # Duração do trial em minutos
    "modo_nsfw_global": True, # Permite a ativação de planos NSFW+
    "modo_debug": False, # Ativa logs detalhados no console
}

# --- PLANOS E PRODUTOS (Stripe) ---
# IDs dos produtos criados no seu painel Stripe
STRIPE_PRODUCTS = {
    "premium": "prod_XXXXXXXXXXXXXX",
    "nsfw_plus": "prod_XXXXXXXXXXXXXX",
    "tokens_100": "price_XXXXXXXXXXXXXX", # Exemplo de preço para produto único
}

print("config.py carregado com sucesso!")
