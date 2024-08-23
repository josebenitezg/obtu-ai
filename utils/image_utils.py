import requests
from PIL import Image
from io import BytesIO

def url_to_pil_image(url):
    try:
        # Ensure url is a string, not a list
        if isinstance(url, list):
            url = url[0]  # Take the first URL if it's a list
        
        response = requests.get(url)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        
        # Convert to RGB if the image is in RGBA mode (for transparency)
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        
        return image
    except Exception as e:
        print(f"Error loading image from URL: {url}")
        print(f"Error details: {str(e)}")
        return None