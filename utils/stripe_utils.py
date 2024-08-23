import stripe
from config import STRIPE_API_KEY, STRIPE_WEBHOOK_SECRET

stripe.api_key = STRIPE_API_KEY


def create_checkout_session(amount, quantity, user_id):
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'unit_amount': amount,
                'product_data': {
                    'name': f'Buy {quantity} credits',
                },
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url='http://localhost:8000/success?session_id={CHECKOUT_SESSION_ID}&user_id=' + str(user_id),
        cancel_url='http://localhost:8000/cancel?user_id=' + str(user_id),

        client_reference_id=str(user_id),  # Add this line
    )
    return session

def verify_webhook(payload, signature):
    try:
        event = stripe.Webhook.construct_event(
            payload, signature, STRIPE_WEBHOOK_SECRET
        )
        return event
    except ValueError as e:
        return None
    except stripe.error.SignatureVerificationError as e:
        return None

def retrieve_stripe_session(session_id):
    try:
        return stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError as e:
        print(f"Error retrieving Stripe session: {str(e)}")
        return None