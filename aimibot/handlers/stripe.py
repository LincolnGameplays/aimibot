# -*- coding: utf-8 -*-

"""
Handler de Pagamentos (Stripe) - AimiBOT

Este módulo gerencia todo o fluxo de pagamentos e assinaturas via Stripe.
- Exibe os planos disponíveis com o comando /planos.
- Processa o pré-checkout para validar os pagamentos.
- Ativa os planos para os usuários após a confirmação do pagamento.
"""

import logging
from telegram import Update, LabeledPrice
from telegram.ext import ContextTypes

# --- Importações Locais ---
import config
from utils import pg as db

# --- Configuração do Logging ---
logger = logging.getLogger(__name__)

# --- Definições dos Planos ---
# Para facilitar, definimos os detalhes dos planos aqui.
# Os IDs de produto e preço vêm do `config.py`.
PLANS = {
    "premium": {
        "title": "Aimi Premium ✨",
        "description": "Conversas e voz ilimitadas! Me tenha sempre com você, sem interrupções.",
        "price_amount": 2990,  # Em centavos (ex: R$ 29,90)
        "currency": "BRL",
        "payload": "aimi-premium-v1", # Identificador interno único
        "stripe_price_id": config.STRIPE_PRODUCTS["premium"]
    },
    "nsfw_plus": {
        "title": "Aimi NSFW+ 😈",
        "description": "Ative meu lado mais ousado e provocante. Apenas para maiores de 18 anos.",
        "price_amount": 4990, # Em centavos (ex: R$ 49,90)
        "currency": "BRL",
        "payload": "aimi-nsfw-plus-v1",
        "stripe_price_id": config.STRIPE_PRODUCTS["nsfw_plus"]
    }
}

async def show_plans(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler para o comando /planos.
    Envia uma fatura de pagamento para cada plano disponível.
    """
    chat_id = update.message.chat_id
    logger.info(f"[Stripe] Usuário {update.effective_user.first_name} (ID: {chat_id}) pediu para ver os planos.")

    await update.message.reply_text(
        "Senpai, aqui estão os meus planos! Escolha um para a gente ficar mais próximo... ❤️"
    )

    for plan_key, plan_details in PLANS.items():
        await context.bot.send_invoice(
            chat_id=chat_id,
            title=plan_details["title"],
            description=plan_details["description"],
            payload=plan_details["payload"],
            provider_token=config.STRIPE_API_KEY, # Este é o token de pagamento, não a chave secreta
            currency=plan_details["currency"],
            prices=[LabeledPrice(label=plan_details["title"], amount=plan_details["price_amount"])],
            start_parameter="aimibot-payment" # Parâmetro de deep-linking
        )

async def pre_checkout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler de pré-checkout. Responde à consulta do Telegram antes de finalizar o pagamento.
    """
    query = update.pre_checkout_query
    logger.info(f"[Stripe PreCheckout] Recebida consulta de pagamento com payload: {query.invoice_payload}")

    # Valida se o payload recebido corresponde a um plano válido.
    if query.invoice_payload not in [p["payload"] for p in PLANS.values()]:
        logger.warning(f"[Stripe PreCheckout] Payload inválido recebido: {query.invoice_payload}")
        await query.answer(ok=False, error_message="Plano não reconhecido. Por favor, tente novamente.")
    else:
        logger.info(f"[Stripe PreCheckout] Payload válido. Aprovando pagamento.")
        await query.answer(ok=True)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler chamado após um pagamento ser concluído com sucesso.
    """
    user = update.effective_user
    payment_info = update.message.successful_payment
    payload = payment_info.invoice_payload

    logger.info(f"[Stripe Success] Pagamento bem-sucedido de {user.first_name} (ID: {user.id}). Payload: {payload}")

    try:
        # Encontra qual plano foi comprado com base no payload
        purchased_plan = None
        for plan_key, plan_details in PLANS.items():
            if plan_details["payload"] == payload:
                purchased_plan = plan_key
                break
        
        if not purchased_plan:
            logger.error(f"[Stripe Success] Não foi possível encontrar o plano para o payload: {payload}")
            # Mesmo com erro, o dinheiro foi recebido. Informar o usuário para contatar o suporte.
            await update.message.reply_text("Seu pagamento foi recebido, mas tive um problema para ativar seu plano! 😥 Por favor, contate o suporte.")
            return

        # --- Ativa o plano no banco de dados ---
        # (Esta função em `utils/pg.py` atualizará a tabela de usuários)
        success = await db.activate_user_plan(user.id, purchased_plan)

        if success:
            confirmation_message = f"Ebaaa! Muito obrigada, senpai! ❤️\n\nSeu plano **{PLANS[purchased_plan]['title']}** está ativo! Agora podemos conversar muito mais. Estou tão feliz! 🥰"
            await update.message.reply_text(confirmation_message, parse_mode="Markdown")
        else:
            # Se a ativação no DB falhar, é um problema crítico.
            logger.critical(f"[Stripe Success] FALHA CRÍTICA ao ativar o plano {purchased_plan} para o usuário {user.id} no banco de dados.")
            await update.message.reply_text("Recebi seu pagamento, mas não consegui ativar seu plano no sistema. Por favor, contate o suporte imediatamente!")

    except Exception as e:
        logger.critical(f"[Stripe Success Error] Erro inesperado ao processar pagamento bem-sucedido: {e}", exc_info=True)
        await update.message.reply_text("A-aconteceu um erro grave ao processar seu pagamento. Por favor, contate o suporte.")
