# routes.py
from fastapi import APIRouter, Depends, Request
from starlette.responses import RedirectResponse
from auth import oauth
from database import get_or_create_user, update_user_credits, get_user_by_id
from authlib.integrations.starlette_client import OAuthError
import gradio as gr
from utils.stripe_utils import create_checkout_session, verify_webhook, retrieve_stripe_session
from config import DOMAIN

router = APIRouter()

def get_user(request: Request):
    user_data = request.session.get('user')
    if user_data:
        # Refresh user data from the database
        user = get_user_by_id(user_data['id'])
        request.session['user'] = user  # Update session with fresh data
        return user['name']
    return None

@router.get('/')
def public(request: Request, user = Depends(get_user)):
    root_url = gr.route_utils.get_root_url(request, "/", None)
    print(f'Root URL: {root_url}')
    if user:
        return RedirectResponse(url=f'{root_url}/gradio/')
    else:
        return RedirectResponse(url=f'{root_url}/main/')
    
@router.route('/logout')
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/')

@router.route('/login')
async def login(request: Request):
    root_url = gr.route_utils.get_root_url(request, "/login", None)
    redirect_uri = f"{root_url}/auth"
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.route('/auth')
async def auth(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')
        if user_info:
            google_id = user_info['sub']
            email = user_info['email']
            name = user_info['name']
            given_name = user_info['given_name']
            profile_picture = user_info.get('picture', '')
            
            user = get_or_create_user(google_id, email, name, given_name, profile_picture)
            request.session['user'] = user
            
            return RedirectResponse(url='/gradio')
        else:
            return RedirectResponse(url='/main')
    except OAuthError as e:
        print(f"OAuth Error: {str(e)}")
        return RedirectResponse(url='/main')
    
# Handle Stripe payments
@router.get("/buy_credits")
async def buy_credits(request: Request):
    user = request.session.get('user')
    if not user:
        return {"error": "User not authenticated"}
    session = create_checkout_session(100, 50, user['id'], request)  # $1 for 50 credits
    
    # Store the session ID and user ID in the session
    request.session['stripe_session_id'] = session['id']
    request.session['user_id'] = user['id']
    print(f"Stripe session created: {session['id']} for user {user['id']}")
    
    return RedirectResponse(session['url'])

@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    
    event = verify_webhook(payload, sig_header)
    
    if event is None:
        return {"error": "Invalid payload or signature"}
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session.get('client_reference_id')
        
        if user_id:
            # Fetch the user from the database
            user = get_user_by_id(user_id)  # You'll need to implement this function
            if user:
                # Update user's credits
                new_credits = user['generation_credits'] + 50  # Assuming 50 credits were purchased
                update_user_credits(user['id'], new_credits, user['train_credits'])
                print(f"Credits updated for user {user['id']}")
            else:
                print(f"User not found for ID: {user_id}")
        else:
            print("No client_reference_id found in the session")
    
    return {"status": "success"}
    
# @router.get("/success")
# async def payment_success(request: Request):
#     print("Payment successful")
#     user = request.session.get('user')
#     print(user)
#     if user:
#         updated_user = get_user_by_id(user['id'])
#         if updated_user:
#             request.session['user'] = updated_user
#             return RedirectResponse(url='/gradio', status_code=303)
#     return RedirectResponse(url='/login', status_code=303)
    
@router.get("/cancel")
async def payment_cancel(request: Request):
    print("Payment cancelled")
    user = request.session.get('user')
    print(user)
    if user:
        return RedirectResponse(url='/gradio', status_code=303)
    return RedirectResponse(url='/login', status_code=303)

@router.get('/success')
async def payment_success(request: Request):
    print('Payment Sucess')
    stripe_session_id = request.session.get('stripe_session_id')
    user_id = request.session.get('user_id')
    print(user_id)
    if stripe_session_id and user_id:
        # Retrieve the Stripe session
        stripe_session = retrieve_stripe_session(stripe_session_id)

        if stripe_session.get('payment_status') == 'paid':
            user = get_user_by_id(user_id)
            if user:
                # Update the session with the latest user data
                request.session['user'] = user
                print(f"\nUser session updated: {user}\n")

                # Clear the stripe_session_id and user_id from the session
                request.session.pop('stripe_session_id', None)
                request.session.pop('user_id', None)

                root_url = DOMAIN
                return RedirectResponse(url=f'{root_url}/gradio/', status_code=303)
            else:
                print(f"User not found for ID: {user_id}")
        else:
            print(f"Payment not completed for session: {stripe_session_id}")
    else:
        print("No Stripe session ID or user ID found in the session")

    return RedirectResponse(url='/login', status_code=303)