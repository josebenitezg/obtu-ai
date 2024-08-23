from pydantic import BaseModel

class User(BaseModel):
    id: str
    google_id: str
    email: str
    name: str
    given_name: str
    profile_picture: str
    generation_credits: int
    train_credits: int