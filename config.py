import os
from dotenv import load_dotenv
import logging

load_dotenv()

REPLICATE_OWNER = "josebenitezg"
HF_OWNER = "joselobenitezg"

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

DOMAIN = os.getenv("DOMAIN")


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)