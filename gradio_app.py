import os
import zipfile
from pathlib import Path

import gradio as gr

from database import (
    get_user_credits,
    update_user_credits,
    get_lora_models_info,
    get_user_lora_models
)

from services.image_generation import generate_image
from services.train_lora import lora_pipeline
from utils.image_utils import url_to_pil_image
from utils.file_utils import load_file_content

LORA_MODELS = get_lora_models_info()
if not isinstance(LORA_MODELS, list):
    raise ValueError("Expected loras_models to be a list of dictionaries.")

BASE_DIR = Path(__file__).parent
LOGIN_CSS_PATH = BASE_DIR / 'static/css/login.css'
MAIN_CSS_PATH = BASE_DIR / 'static/css/main.css'
LANDING_HTML_PATH = BASE_DIR / 'static/html/landing.html'
MAIN_HEADER_PATH = BASE_DIR / 'static/html/main_header.html'

LOGIN_CSS = load_file_content(LOGIN_CSS_PATH)
MAIN_CSS = load_file_content(MAIN_CSS_PATH)
LANDING_PAGE = load_file_content(LANDING_HTML_PATH)
MAIN_HEADER = load_file_content(MAIN_HEADER_PATH)

def load_user_models(request: gr.Request):
    user = request.session.get('user')
    print(user)
    if user:
        user_models = get_user_lora_models(user['id'])
        if user_models:
            return [(item.get("image_url", "assets/logo.jpg"), item["lora_name"]) for item in user_models]
    return []

def update_selection(evt: gr.SelectData, gallery_type: str, width, height):
    if gallery_type == "user":
        selected_lora = {"lora_name": "custom", "trigger_word": "custom"}
    else:
        selected_lora = LORA_MODELS[evt.index]
    new_placeholder = f"Enter a prompt for {selected_lora['lora_name']}"
    trigger_word = selected_lora["trigger_word"]
    updated_text = f"#### Trigger Word: {trigger_word} ✨"
    
    if "aspect" in selected_lora:
        if selected_lora["aspect"] == "portrait":
            width, height = 768, 1024
        elif selected_lora["aspect"] == "landscape":
            width, height = 1024, 768

    return gr.update(placeholder=new_placeholder), updated_text, evt.index, width, height, gallery_type

def compress_and_train(request: gr.Request, files, model_name, trigger_word, train_steps, lora_rank, batch_size, learning_rate):
    if not files:
        return "No Images. Please, upload some images to start training"
    
    user = request.session.get('user')
    
    _, training_credits = get_user_credits(user['id'])
    
    if training_credits <= 0:
        raise gr.Error("You ran out of credtis. Please buy more to continue")
    
    if not user:
        raise gr.Error("User not authenticated. Please log in.")

    user_id = user['id']
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
    result = lora_pipeline(user_id,
                            zip_path, 
                            model_name, 
                            trigger_word=trigger_word, 
                            steps=train_steps, 
                            lora_rank=lora_rank, 
                            batch_size=batch_size, 
                            autocaption=True, 
                            learning_rate=learning_rate)
    
    new_training_credits = training_credits - 1
    update_user_credits(user['id'], user['generation_credits'], new_training_credits)
    
    # Update session data
    user['training_credits'] = new_training_credits
    request.session['user'] = user
    
    return gr.Info("Your model is training. In about 20 minutes, it will be ready for you to test in 'Generation"), new_training_credits
            
def run_lora(request: gr.Request, prompt, cfg_scale, steps, selected_index, selected_gallery, width, height, lora_scale, progress=gr.Progress(track_tqdm=True)):
    user = request.session.get('user')
    if not user:
        raise gr.Error("User not authenticated. Please log in.")
    lora_models = get_user_lora_models(user['id'])
    print(f'Selected gallery: {selected_gallery}')
    if selected_gallery == "user":
        lora_models = get_user_lora_models(user['id'])
        print('Using user models')
    else:  # public
        lora_models = get_lora_models_info()
        print('Using public models')
    print(f'Selected index: {selected_index}')
    if selected_index is None:
        selected_lora = None
    else:
        selected_lora = lora_models[selected_index]

    generation_credits, _ = get_user_credits(user['id'])
    if selected_lora:
        print(f"Selected Lora: {selected_lora['lora_name']}")
        model_name = selected_lora['lora_name']
        use_default = False
    else:
        model_name = "black-forest-labs/flux-pro"
        print(f"Using default Lora: {model_name}")
        use_default = True
    if generation_credits <= 0:
        raise gr.Error("Ya no tienes creditos disponibles. Compra para continuar.")
    
    image_url = generate_image(model_name, prompt, steps, cfg_scale, width, height, lora_scale, progress, use_default)
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

with gr.Blocks(theme=gr.themes.Soft(), css=LOGIN_CSS) as login_demo:
    with gr.Column(elem_id="google-btn-container", elem_classes="google-btn-container svelte-vt1mxs gap"):
        btn = gr.Button("Sign In with Google", elem_classes="login-with-google-btn")
    _js_redirect = """
    () => {
        url = '/login' + window.location.search;
        window.open(url, '_blank');
    }
    """
    btn.click(None, js=_js_redirect)
    gr.HTML(LANDING_PAGE)
        

header = '<script src="https://cdn.lordicon.com/lordicon.js"></script>'

with gr.Blocks(theme=gr.themes.Soft(), head=header, css=MAIN_CSS) as main_demo:
    title = gr.HTML(MAIN_HEADER)
    
    with gr.Column(elem_id="logout-btn-container"):
        gr.Button("Logout", link="/logout", elem_id="logout_btn")

    
    greetings = gr.Markdown("Loading user information...")
    
    selected_index = gr.State(None)
    
    with gr.Row():
        with gr.Column():
            generation_credits_display = gr.Number(label="Generation Credits", precision=0, interactive=False)
        with gr.Column():
            train_credits_display = gr.Number(label="Training Credits", precision=0, interactive=False)
        with gr.Column():
            gr.Button("Buy Credits 💳", link="/buy_credits")
    

    with gr.Tabs():
        with gr.TabItem('Create'):
            with gr.Row():
                with gr.Column(scale=3):
                    prompt = gr.Textbox(label="Prompt", 
                                        lines=1, 
                                        placeholder="Enter Your Prompt to start creating 📷", 
                                        info='Some public models may experience longer processing times due to server availability and queue management.')
                with gr.Column(scale=1, elem_id="gen_column"):
                    generate_button = gr.Button("Generate", variant="primary", elem_id="gen_btn")
            
            with gr.Row():
                with gr.Column(scale=4):
                    result = gr.Image(label="Imagen Generada")
                
                with gr.Column(scale=3):
                    with gr.Accordion("Public Models"):
                        selected_info = gr.Markdown("")
                        gallery = gr.Gallery(
                            [(item["image_url"], item["model_name"]) for item in LORA_MODELS],
                            label="Public Models",
                            allow_preview=False,
                            columns=3,
                            elem_id="gallery"
                        )
                        
                    with gr.Accordion("Your Models"):
                        user_model_gallery = gr.Gallery(
                            label="Galeria de Modelos",
                            allow_preview=False,
                            columns=3,
                            elem_id="galley"
                        )
                        
            gallery_type = gr.State("Public")

            with gr.Accordion("Advanced Settings", open=False):
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
                inputs=[gr.State("public"), width, height],
                outputs=[prompt, selected_info, selected_index, width, height, gallery_type]
            )
            
            user_model_gallery.select(
                update_selection,
                inputs=[gr.State("user"), width, height],
                outputs=[prompt, selected_info, selected_index, width, height, gallery_type]
            )
            gr.on(
                triggers=[generate_button.click, prompt.submit],
                fn=run_lora,
                inputs=[prompt, cfg_scale, steps, selected_index, gallery_type, width, height, lora_scale],
                outputs=[result, generation_credits_display]
            )

        with gr.TabItem("Train"):
            gr.Markdown("# Train your own model 🧠")
            gr.Markdown("In this section, you can train your own model using your images.")
            with gr.Row():
                with gr.Column():
                    train_dataset = gr.Gallery(columns=4, interactive=True, label="Tus Imagenes")
                    model_name = gr.Textbox(label="Model Name",)
                    trigger_word = gr.Textbox(label="Trigger Word", 
                                              info="This will be a keyword to later instruct the model when to use these new capabilities we're going to teach it", 
                                              )
                    train_button = gr.Button("Start Training")
            with gr.Accordion("Advanced Settings", open=False):
                train_steps = gr.Slider(label="Training Steps", minimum=100, maximum=10000, step=100, value=1000)
                lora_rank = gr.Number(label='lora_rank', value=16)
                batch_size = gr.Number(label='batch_size', value=1)
                learning_rate = gr.Number(label='learning_rate', value=0.0004)
                training_status = gr.Textbox(label="Training Status")
                
            train_button.click(
                compress_and_train,
                inputs=[train_dataset, model_name, trigger_word, train_steps, lora_rank, batch_size, learning_rate],
                outputs=[training_status,train_credits_display]
            )
                
        main_demo.load(load_user_models, None, user_model_gallery)
        main_demo.load(load_greet_and_credits, None, [greetings, generation_credits_display, train_credits_display])