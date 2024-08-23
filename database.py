import json
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_user_credits(user_id):
    user = supabase.table("users").select("generation_credits, train_credits").eq("id", user_id).execute()
    if user.data:
        return user.data[0]["generation_credits"], user.data[0]["train_credits"]
    return 0, 0

def update_user_credits(user_id, generation_credits, train_credits):
    supabase.table("users").update({
        "generation_credits": generation_credits,
        "train_credits": train_credits
    }).eq("id", user_id).execute()

def get_or_create_user(google_id, email, name, given_name, profile_picture):
    user = supabase.table("users").select("*").eq("google_id", google_id).execute()
    
    if not user.data:
        new_user = {
            "google_id": google_id,
            "email": email,
            "name": name,
            "profile_picture": profile_picture,
            "generation_credits": 2,
            "train_credits": 1,
            "given_name": given_name
        }
        result = supabase.table("users").insert(new_user).execute()
        return result.data[0]
    else:
        return user.data[0]
    
def get_lora_models_info():
    lora_models = supabase.table("lora_models").select("*").is_("user_id", None).execute()
    
    return lora_models.data

def get_user_by_id(user_id):
    user = supabase.table("users").select("*").eq("id", user_id).execute()
    if user.data:
        return user.data[0]
    return None

def create_lora_models(user_id, replicate_repo_name, trigger_word, steps, lora_rank, batch_size, learning_rate, hf_repo_name, training_url):
    # create a jsonb from trigger_word, train_steps, lora_rank, batch_size, learning_rate values
    model_config = {
        "train_steps": steps,
        "lora_rank": lora_rank,
        "batch_size": batch_size,
        "learning_rate": learning_rate
    }
    result = supabase.table("lora_models").insert({
        "user_id": user_id,
        "trigger_word": trigger_word,
        "lora_name": replicate_repo_name,
        "hf_repo": hf_repo_name,
        "configs": model_config,
        "training_url": training_url
    }).execute()
    
def get_user_lora_models(user_id):
    user_models = supabase.table("lora_models").select("*").eq("user_id", user_id).execute()
    return user_models.data