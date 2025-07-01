# Exemplo de um arquivo de rota - app/routers/stripe_webhook.py

from fastapi import APIRouter, Request, Header
import stripe

# from .. import config # Supondo que você tenha um config.py na API
# from ..main import notify_sale # Importa a função de notificação

router = APIRouter(
    prefix="/webhooks",
    tags=["Stripe"]
)

@router.post("/stripe")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    data = await request.body()
    
    # try:
    #     event = stripe.Webhook.construct_event(
    #         payload=data,
    #         sig_header=stripe_signature,
    #         secret=config.STRIPE_WEBHOOK_SECRET
    #     )
    # except Exception as e:
    #     return {"error": str(e)}

    # # Exemplo de lógica
    # if event['type'] == 'checkout.session.completed':
    #     session = event['data']['object']
    #     # Lógica para buscar o usuário e o produto
    #     sale_data = {"product": session['display_items'][0]['custom']['name'], "amount": f"{session['amount_total']/100} {session['currency'].upper()}"}
    #     await notify_sale(sale_data)
        
    return {"status": "success"}
