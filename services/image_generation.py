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
        model_name = model_name.lower().replace(' ', '_')
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
