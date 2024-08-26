import replicate
import os
from huggingface_hub import create_repo
from database import create_lora_models
from config import HF_OWNER, REPLICATE_OWNER

def lora_pipeline(user_id, zip_path, model_name, trigger_word="TOK", steps=1000, lora_rank=16, batch_size=1, autocaption=True, learning_rate=0.0004):
    print(f'Creating dataset for {model_name}')
    model_name = model_name.lower().replace(' ', '_')
    hf_repo_name = f"{HF_OWNER}/flux-dev-{model_name}"
    replicate_repo_name = f"{REPLICATE_OWNER}/flux-dev-{model_name}"
    create_repo(hf_repo_name, repo_type='model')

    lora_name = f"flux-dev-{model_name}"
    
    model = replicate.models.create(
        owner=REPLICATE_OWNER,
        name=lora_name,
        visibility="private",  # or "private" if you prefer
        hardware="gpu-t4",  # Replicate will override this for fine-tuned models
        description="A fine-tuned FLUX.1 model"
    )

    print(f"Model created: {model.name}")
    print(f"Model URL: https://replicate.com/{model.owner}/{model.name}")

    # Now use this model as the destination for your training
    print(f"[INFO] Starting training")
    
    print(f'\n[INFO] Parametros a entrenar: \n Trigger word: {trigger_word}\n steps: {steps} \n lora_rank: {lora_rank}\n autocaption: {autocaption}\n learning_rate: {learning_rate}\n') 
    training = replicate.trainings.create(
        version="ostris/flux-dev-lora-trainer:1296f0ab2d695af5a1b5eeee6e8ec043145bef33f1675ce1a2cdb0f81ec43f02",
        input={
            "input_images": open(zip_path, "rb"),
            "steps": steps,
            "lora_rank": lora_rank,
            "batch_size": batch_size,
            "autocaption": autocaption,
            "trigger_word": trigger_word,
            "learning_rate": learning_rate,
            "hf_token": os.getenv('HF_TOKEN'),  # optional
            "hf_repo_id": hf_repo_name,  # optional
        },
        destination=f"{model.owner}/{model.name}"
    )

    print(f"Training started: {training.status}")
    print(f"Training URL: https://replicate.com/p/{training.id}")
    print(f"Creating model in Database")
    training_url = f"https://replicate.com/p/{training.id}"
    create_lora_models(user_id, replicate_repo_name, trigger_word, steps, lora_rank, batch_size, learning_rate, hf_repo_name, training_url)