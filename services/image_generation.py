import replicate
from PIL import Image
import requests
from io import BytesIO


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
        # check if the model has a version. the model is something like model='user/model-name:version' but sometimes we just got model='user/model-name' in this case, let get and add the model version
        if ':' not in model_name:
            model_version = replicate.models.get(model_name).latest_version.id
            print(f"Model version: {model_version}")
            model_name = f"{model_name}:{model_version}"
            
        img_url = replicate.run(
            model_name,
            input={
                "model": "dev",
                "steps": steps,
                "prompt": prompt,
                "guidance": cfg_scale,
                "interval": 2,
                "aspect_ratio": "1:1",
                "safety_tolerance": 2
            }
        )
    return img_url
