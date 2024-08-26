import gradio as gr
from database import get_user_credits

def display_credits(request: gr.Request):
    user = request.session.get('user')
    if user:
        generation_credits, train_credits = get_user_credits(user['id'])
        return generation_credits, train_credits
    return 0, 0

def load_greet_and_credits(request: gr.Request):
    greeting = greet(request)
    generation_credits, train_credits = display_credits(request)
    return greeting, generation_credits, train_credits

def greet(request: gr.Request):
    user = request.session.get('user')
    if user:
        return f"Hola 👋 {user['given_name']}!\n"
    return "OBTU AI. Please log in."