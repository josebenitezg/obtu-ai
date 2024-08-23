import replicate
from PIL import Image
import requests
from io import BytesIO

#model_custom_test = "josebenitezg/flux-dev-ruth-estilo-1:c7ff81b58007c7cee3f69416e1e999192dafd8d1b1f269ea6cae137f04b34172"
flux_pro = "black-forest-labs/flux-pro"
def generate_image(prompt, steps, cfg_scale, width, height, lora_scale, progress, trigger_word='hi'):
    print(f"Generating image for prompt: {prompt}")
    img_url = replicate.run(
        flux_pro,
        input={
            "steps": steps,
            "prompt": prompt,
            "guidance": cfg_scale,
            "interval": 2,
            "aspect_ratio": "1:1",
            "safety_tolerance": 2
        }
    )
    return img_url
