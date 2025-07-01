# -*- coding: utf-8 -*-

"""
Módulo Principal - AimiBOT

Este é o ponto de entrada do AimiBOT. Ele é responsável por:
1. Carregar as configurações do `config.py`.
2. Inicializar a aplicação do bot usando a biblioteca `python-telegram-bot`.
3. Configurar o sistema de logging para monitoramento e depuração.
4. Registrar todos os "handlers", que são as funções que respondem a comandos
   (ex: /start), mensagens de texto, pagamentos e outras interações.
5. Iniciar o bot para que ele comece a ouvir as mensagens dos usuários.
"""

import logging
import asyncio

from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    PreCheckoutQueryHandler,
    SuccessfulPaymentHandler,
    CallbackQueryHandler
)

# --- Importações Locais ---
# Importa as configurações e os módulos de handlers que criaramos a seguir.
import config
from handlers import commands, chat, emotion, stripe, tts

# --- Configuração do Logging ---
# Define um sistema de log para sabermos o que o bot está fazendo e identificar erros.
# Se o modo_debug estiver ativo no config.py, os logs serão mais detalhados.
log_level = logging.DEBUG if config.OPERATION_MODES.get("modo_debug") else logging.INFO
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=log_level
)
# Define um logger específico para este arquivo.
logger = logging.getLogger(__name__)


async def error_handler(update, context):
    """
    Handler de Erro Global.

    Captura todas as exceções não tratadas e as registra para que possamos
    diagnosticar problemas sem que o bot pare de funcionar.
    """
    logger.error("Exceção ao processar uma atualização:", exc_info=context.error)


async def main():
    """
    Função principal que configura e inicia o bot.
    """
    logger.info("Iniciando o AimiBOT...")
    
    # Cria a aplicação do bot usando o token do Telegram.
    application = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()

    # --- Registro dos Handlers ---
    # Cada handler é associado a um tipo de evento (comando, texto, etc.)
    
    # 1. Handlers de Comandos Essenciais
    application.add_handler(CommandHandler("start", commands.start))
    application.add_handler(CommandHandler("ajuda", commands.ajuda))
    application.add_handler(CommandHandler("status", commands.status))
    application.add_handler(CommandHandler("planos", stripe.show_plans))
    
    # 2. Handler de Conversa Principal (Roleplay)
    # Responde a mensagens de texto que NÃO são comandos.
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat.handle_message))

    # 3. Handler de Emoções (Reações a emojis específicos)
    # O filtro pode ser ajustado para emojis específicos. Ex: filters.Sticker.EMOJI
    application.add_handler(MessageHandler(filters.Sticker.ALL, emotion.handle_reaction))

    # 4. Handlers de Pagamento (Stripe)
    # Lida com o processo de checkout do Telegram.
    application.add_handler(PreCheckoutQueryHandler(stripe.pre_checkout_callback))
    application.add_handler(SuccessfulPaymentHandler(stripe.successful_payment_callback))

    # 5. Handler para botões (CallbackQueryHandler)
    # Usado para interações com botões em mensagens, como os do /start.
    application.add_handler(CallbackQueryHandler(commands.button_callback))

    # --- Handler de Erro ---
    # Registra o handler global de erros.
    application.add_error_handler(error_handler)

    # --- Inicia o Bot ---
    # O bot começa a "ouvir" as mensagens do Telegram.
    # `run_polling` é ideal para desenvolvimento. Para produção, `run_webhook` é recomendado.
    logger.info("AimiBOT está online e ouvindo...")
    await application.run_polling()


if __name__ == "__main__":
    try:
        # Executa a função principal de forma assíncrona.
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("AimiBOT foi desligado.")
    except Exception as e:
        logger.critical(f"Erro crítico ao iniciar o bot: {e}", exc_info=True)

