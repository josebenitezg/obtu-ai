import gradio as gr
from database import get_lora_models_info, get_user_lora_models, update_user_credits, get_user_credits
from services.image_generation import generate_image
from utils.image_utils import url_to_pil_image

def create_generation_tab():
    with gr.TabItem('Generacion'):
        with gr.Row():
            with gr.Column(scale=3):
                prompt = gr.Textbox(label="Prompt", 
                                    lines=1, 
                                    placeholder="Ingresa un prompt para empezar a crear", 
                                    info='Algunos modelos publicos pueden demorar un poco más dependiendo de la disponibilidad que tengan en los servidores.')
            with gr.Column(scale=1, elem_id="gen_column"):
                generate_button = gr.Button("Generate", variant="primary", elem_id="gen_btn")
        
        with gr.Row():
            with gr.Column(scale=4):
                result = gr.Image(label="Imagen Generada")
            
            with gr.Column(scale=3):
                with gr.Accordion("Modelos Publicos"):
                    selected_info = gr.Markdown("")
                    lora_models = get_lora_models_info()
                    gallery = gr.Gallery(
                        [(item["image_url"], item["model_name"]) for item in lora_models],
                        label="Galeria de Modelos Publicos",
                        allow_preview=False,
                        columns=3,
                        elem_id="gallery"
                    )
                    
                with gr.Accordion("Tus Modelos"):
                    user_model_gallery = gr.Gallery(
                        label="Galeria de Modelos",
                        allow_preview=False,
                        columns=3,
                        elem_id="galley"
                    )
                    
        gallery_type = gr.State("Public")

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
            inputs=[gr.State("public"), width, height],
            outputs=[prompt, selected_info, gr.State(0), width, height, gallery_type]
        )
        
        user_model_gallery.select(
            update_selection,
            inputs=[gr.State("user"), width, height],
            outputs=[prompt, selected_info, gr.State(0), width, height, gallery_type]
        )
        gr.on(
            triggers=[generate_button.click, prompt.submit],
            fn=run_lora,
            inputs=[prompt, cfg_scale, steps, gr.State(0), gallery_type, width, height, lora_scale],
            outputs=[result, gr.State(0)]
        )

def update_selection(evt: gr.SelectData, gallery_type: str, width, height):
    if gallery_type == "user":
        selected_lora = {"lora_name": "custom", "trigger_word": "custom"}
    else:
        lora_models = get_lora_models_info()
        selected_lora = lora_models[evt.index]
    new_placeholder = f"Ingresa un prompt para tu modelo {selected_lora['lora_name']}"
    trigger_word = selected_lora["trigger_word"]
    updated_text = f"#### Palabra clave: {trigger_word} ✨"
    
    if "aspect" in selected_lora:
        if selected_lora["aspect"] == "portrait":
            width, height = 768, 1024
        elif selected_lora["aspect"] == "landscape":
            width, height = 1024, 768
    
    return new_placeholder, updated_text, evt.index, width, height, gallery_type

def run_lora(request: gr.Request, prompt, cfg_scale, steps, selected_index, selected_gallery, width, height, lora_scale, progress=gr.Progress(track_tqdm=True)):
    user = request.session.get('user')
    if not user:
        raise gr.Error("User not authenticated. Please log in.")
    
    if selected_gallery == "user":
        lora_models = get_user_lora_models(user['id'])
    else:  # public
        lora_models = get_lora_models_info()
    
    if selected_index is None:
        selected_lora = None
    else:
        selected_lora = lora_models[selected_index]

    generation_credits, _ = get_user_credits(user['id'])
    if selected_lora:
        model_name = selected_lora['lora_name']
        use_default = False
    else:
        model_name = "black-forest-labs/flux-pro"
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
    
    return image, new_generation_credits