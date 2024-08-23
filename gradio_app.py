import gradio as gr

import os
import json
import zipfile
from pathlib import Path

from database import get_user_credits, update_user_credits, get_lora_models_info
from services.image_generation import generate_image
from services.train_lora import lora_pipeline
from utils.image_utils import url_to_pil_image

lora_models = get_lora_models_info()


if not isinstance(lora_models, list):
    raise ValueError("Expected loras_models to be a list of dictionaries.")

login_css_path = Path(__file__).parent / 'static/css/login.css'
main_css_path = Path(__file__).parent / 'static/css/main.css'
landing_html_path = Path(__file__).parent / 'static/html/landing.html'
main_header_path = Path(__file__).parent / 'static/html/main_header.html'

if login_css_path.is_file():  # Check if the file exists
    with login_css_path.open() as file:
       login_css = file.read()

if main_css_path.is_file():  # Check if the file exists
    with main_css_path.open() as file:
        main_css = file.read()
        
if landing_html_path.is_file():
    with landing_html_path.open() as file:
        landin_page = file.read()

if main_header_path.is_file():
    with main_header_path.open() as file:
        main_header = file.read()

def update_selection(evt: gr.SelectData, width, height):
    selected_lora = lora_models[evt.index]
    new_placeholder = f"Ingresa un prompt para tu modelo {selected_lora['lora_name']}"
    trigger_word = selected_lora["trigger_word"]
    updated_text = f"#### Palabra clave: {trigger_word} ✨"
    
    if "aspect" in selected_lora:
        if selected_lora["aspect"] == "portrait":
            width, height = 768, 1024
        elif selected_lora["aspect"] == "landscape":
            width, height = 1024, 768
    
    return gr.update(placeholder=new_placeholder), updated_text, evt.index, width, height

def compress_and_train(files, model_name, trigger_word, train_steps, lora_rank, batch_size, learning_rate):
    if not files:
        return "No images uploaded. Please upload images before training."

    # Create a directory in the user's home folder
    output_dir = os.path.expanduser("~/gradio_training_data")
    os.makedirs(output_dir, exist_ok=True)

    # Create a zip file in the output directory
    zip_path = os.path.join(output_dir, "training_data.zip")
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file_info in files:
            file_path = file_info[0]  # The first element of the tuple is the file path
            file_name = os.path.basename(file_path)
            zipf.write(file_path, file_name)
    
    print(f"Zip file created at: {zip_path}")
        
    print(f'[INFO] Procesando {trigger_word}')
    # Now call the train_lora function with the zip file path
    result = lora_pipeline(zip_path, 
                            model_name, 
                            trigger_word=trigger_word, 
                            steps=train_steps, 
                            lora_rank=lora_rank, 
                            batch_size=batch_size, 
                            autocaption=True, 
                            learning_rate=learning_rate)
    
    return f"{result}\n\nZip file saved at: {zip_path}"
            
def run_lora(request: gr.Request, prompt, cfg_scale, steps, selected_index, randomize_seed, width, height, lora_scale, progress=gr.Progress(track_tqdm=True)):
    user = request.session.get('user')
    if not user:
        raise gr.Error("User not authenticated. Please log in.")
    
    generation_credits, _ = get_user_credits(user['id'])
    
    if generation_credits <= 0:
        raise gr.Error("Ya no tienes creditos disponibles. Compra para continuar.")
    
    image_url = generate_image(prompt, steps, cfg_scale, width, height, lora_scale, progress)
    image = url_to_pil_image(image_url)
    
    # Update user's credits
    new_generation_credits = generation_credits - 1
    update_user_credits(user['id'], new_generation_credits, user['train_credits'])
    
    # Update session data
    user['generation_credits'] = new_generation_credits
    request.session['user'] = user
    
    print(f"Generation credits remaining: {new_generation_credits}")
    
    return image, new_generation_credits

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
        with gr.Column():  
            with gr.Row():
                greeting = f"Hola 👋 {user['given_name']}!"
            return f"{greeting}\n"
    return "OBTU AI. Please log in."

with gr.Blocks(theme=gr.themes.Soft(), css=login_css) as login_demo:
    with gr.Column(elem_id="google-btn-container", elem_classes="google-btn-container svelte-vt1mxs gap"):
        btn = gr.Button("Iniciar Sesion con Google", elem_classes="login-with-google-btn")
    _js_redirect = """
    () => {
        url = '/login' + window.location.search;
        window.open(url, '_blank');
    }
    """
    btn.click(None, js=_js_redirect)
    gr.HTML(landin_page)
        

header = '<script src="https://cdn.lordicon.com/lordicon.js"></script>'

with gr.Blocks(theme=gr.themes.Soft(), head=header, css=main_css) as main_demo:
    title = gr.HTML(main_header)
    
    with gr.Column(elem_id="logout-btn-container"):
        gr.Button("Salir", link="/logout", elem_id="logout_btn")

    
    greetings = gr.Markdown("Loading user information...")
    gr.Button("Comprar Creditos", link="/buy_credits", elem_id="buy_credits_btn")

    selected_index = gr.State(None)
    
    with gr.Row():
        with gr.Column():
            generation_credits_display = gr.Number(label="Generation Credits", precision=0, interactive=False)
        with gr.Column():
            train_credits_display = gr.Number(label="Training Credits", precision=0, interactive=False)
    

    with gr.Tabs():
        with gr.TabItem('Generacion'):
            with gr.Row():
                with gr.Column(scale=3):
                    prompt = gr.Textbox(label="Prompt", lines=1, placeholder="Ingresa un prompt para empezar a crear")
                with gr.Column(scale=1, elem_id="gen_column"):
                    generate_button = gr.Button("Generate", variant="primary", elem_id="gen_btn")
            
            with gr.Row():
                with gr.Column(scale=4):
                    result = gr.Image(label="Imagen Generada")
                
                with gr.Column(scale=3):
                    with gr.Accordion("Tus Modelos"):
                        user_model_gallery = gr.Gallery(
                            label="Galeria de Modelos",
                            allow_preview=False,
                            columns=3,
                            elem_id="galley"
                        )
                        
                    with gr.Accordion("Modelos Publicos", open=False):
                        selected_info = gr.Markdown("")
                        gallery = gr.Gallery(
                            [(item["image_url"], item["lora_name"]) for item in lora_models],
                            label="Galeria de Modelos Publicos",
                            allow_preview=False,
                            columns=3,
                            elem_id="gallery"
                        )
                    

            with gr.Accordion("Configuracion Avanzada", open=False):
                with gr.Row():
                    cfg_scale = gr.Slider(label="CFG Scale", minimum=1, maximum=20, step=0.5, value=3.5)
                    steps = gr.Slider(label="Steps", minimum=1, maximum=50, step=1, value=28)
                with gr.Row():
                    width = gr.Slider(label="Width", minimum=256, maximum=1536, step=64, value=1024)
                    height = gr.Slider(label="Height", minimum=256, maximum=1536, step=64, value=1024)
                with gr.Row():
                    randomize_seed = gr.Checkbox(True, label="Randomize seed")
                    lora_scale = gr.Slider(label="LoRA Scale", minimum=0, maximum=1, step=0.01, value=0.95)

            gallery.select(
                update_selection,
                inputs=[width, height],
                outputs=[prompt, selected_info, selected_index, width, height]
            )

            gr.on(
                triggers=[generate_button.click, prompt.submit],
                fn=run_lora,
                inputs=[prompt, cfg_scale, steps, selected_index, randomize_seed, width, height, lora_scale],
                outputs=[result, generation_credits_display]
            )

        with gr.TabItem("Training"):
            gr.Markdown("# Entrena tu propio modelo 🧠")
            gr.Markdown("En esta seccion podes entrenar tu propio modelo a partir de tus imagenes.")
            with gr.Row():
                with gr.Column():
                    train_dataset = gr.Gallery(columns=4, interactive=True, label="Tus Imagenes")
                    model_name = gr.Textbox(label="Nombre del Modelo",)
                    trigger_word = gr.Textbox(label="Palabra clave", 
                                              info="Esta seria una palabra clave para luego indicar al modelo cuando debe usar estas nuevas capacidad es que le vamos a ensenar", 
                                              )
                    train_button = gr.Button("Comenzar Training")
            with gr.Accordion("Configuracion Avanzada", open=False):
                train_steps = gr.Slider(label="Training Steps", minimum=100, maximum=10000, step=100, value=1000)
                lora_rank = gr.Number(label='lora_rank', value=16)
                batch_size = gr.Number(label='batch_size', value=1)
                learning_rate = gr.Number(label='learning_rate', value=0.0004)
                training_status = gr.Textbox(label="Training Status")



            train_button.click(
                compress_and_train,
                inputs=[train_dataset, model_name, trigger_word, train_steps, lora_rank, batch_size, learning_rate],
                outputs=training_status
            )
                
                
        #main_demo.load(greet, None, title)
        #main_demo.load(greet, None, greetings)
        #main_demo.load((greet, display_credits), None, [greetings, generation_credits_display, train_credits_display])
        main_demo.load(load_greet_and_credits, None, [greetings, generation_credits_display, train_credits_display])



# TODO:
'''
- Galeria Modelos Propios (si existe alguno del user, si no, mostrar un mensaje para entrenar)
- Galeria Modelos Open Source (accordion)
- Training con creditos.
- Stripe(?)
- Mejorar boton de login/logout
- Retoque landing page
'''


