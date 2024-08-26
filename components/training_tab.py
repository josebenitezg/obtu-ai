import os
import zipfile
import gradio as gr
from services.train_lora import lora_pipeline
from database import get_user_credits, update_user_credits

def create_training_tab():
    with gr.TabItem("Training"):
        with gr.Row():
            with gr.Column():
                files = gr.File(label="Upload Images", file_count="multiple", file_types=["image"])
                model_name = gr.Textbox(label="Model Name", placeholder="Enter a name for your model")
                trigger_word = gr.Textbox(label="Trigger Word", placeholder="Enter a trigger word")
            with gr.Column():
                train_steps = gr.Slider(label="Training Steps", minimum=100, maximum=2000, value=1000, step=100)
                lora_rank = gr.Slider(label="LoRA Rank", minimum=4, maximum=128, value=4, step=4)
                batch_size = gr.Slider(label="Batch Size", minimum=1, maximum=32, value=1, step=1)
                learning_rate = gr.Slider(label="Learning Rate", minimum=1e-6, maximum=1e-3, value=1e-4, step=1e-6)
        
        train_button = gr.Button("Train Model")
        output = gr.Textbox(label="Training Output")
        
        train_button.click(
            compress_and_train,
            inputs=[files, model_name, trigger_word, train_steps, lora_rank, batch_size, learning_rate],
            outputs=[output]
        )

def compress_and_train(request: gr.Request, files, model_name, trigger_word, train_steps, lora_rank, batch_size, learning_rate):
    if not files:
        return "No hay imágenes. Sube algunas imágenes para poder entrenar."
    
    user = request.session.get('user')
    
    _, training_credits = get_user_credits(user['id'])
    
    if training_credits <= 0:
        raise gr.Error("Ya no tienes creditos disponibles. Compra para continuar.")
    
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
    
    return gr.Info("Tu modelo esta entrenando, En unos 20 minutos estará listo para que lo pruebes en 'Generación'."), new_training_credits