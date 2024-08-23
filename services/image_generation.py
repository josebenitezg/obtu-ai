import replicate
from PIL import Image
import requests
from io import BytesIO
from database import get_lora_models_info


def generate_image(model_name, prompt, steps, cfg_scale, width, height, lora_scale, progress, use_default=False, trigger_word='hi'):
    print(f"Generating image for prompt: {prompt}")
    if use_default:
        img_url = replicate.run(
            "black-forest-labs/flux-pro",
            input={
                "steps": steps,
                "prompt": prompt,
                "guidance": cfg_scale,
                "interval": 2,
                "aspect_ratio": "1:1",
                "safety_tolerance": 2
            }
        )
    else:
        input = {
                "model": "dev",
                "steps": steps,
                "prompt": prompt,
                "guidance": cfg_scale,
                "interval": 2,
                "aspect_ratio": "1:1",
                "safety_tolerance": 2
            }

        db_loras = get_lora_models_info()

        for lora in db_loras:
            if lora["lora_name"] == model_name:
                if lora["hf_repo"]:
                    input["hf_lora"] = lora["hf_repo"]
                    model_name = "lucataco/flux-dev-lora:a22c463f11808638ad5e2ebd582e07a469031f48dd567366fb4c6fdab91d614d"
                    
        if ':' not in model_name:
            model_version = replicate.models.get(model_name).latest_version.id
            print(f"Model version: {model_version}")
            model_name = f"{model_name}:{model_version}"
            
        img_url = replicate.run(
            model_name,
            input=input
        )
    return img_url

