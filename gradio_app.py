import gradio as gr
from pathlib import Path

from utils.file_utils import load_css, load_html
from utils.credit_utils import load_greet_and_credits, display_credits
from components.generation_tab import create_generation_tab
from components.training_tab import create_training_tab
from components.login import create_login_demo

# Load CSS and HTML files
login_css = load_css('static/css/login.css')
main_css = load_css('static/css/main.css')
landing_page = load_html('static/html/landing.html')
main_header = load_html('static/html/main_header.html')

# Create login demo
login_demo = create_login_demo(login_css, landing_page)

# Create main demo
with gr.Blocks(theme=gr.themes.Soft(), css=main_css) as main_demo:
    gr.HTML(main_header)
    
    with gr.Column(elem_id="logout-btn-container"):
        gr.Button("Salir", link="/logout", elem_id="logout_btn")
    
    greetings = gr.Markdown("Loading user information...")
    
    with gr.Row():
        generation_credits_display = gr.Number(label="Generation Credits", precision=0, interactive=False)
        train_credits_display = gr.Number(label="Training Credits", precision=0, interactive=False)
        gr.Button("Comprar Creditos 💳", link="/buy_credits")

    with gr.Tabs():
        create_generation_tab()
        create_training_tab()
        
    main_demo.load(load_greet_and_credits, None, [greetings, generation_credits_display, train_credits_display])

# Launch the app
if __name__ == "__main__":
    gr.TabbedInterface([login_demo, main_demo], ["Login", "Main"]).launch()