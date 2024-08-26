import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from config import SECRET_KEY
from routes import router, get_user
from gradio_app_og import login_demo, main_demo
import gradio as gr
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

login_demo.queue()
main_demo.queue()

static_dir = Path("./static")
app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")
#app.mount("/assets", StaticFiles(directory="assets", html=True), name="assets")

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, max_age=3600)

app.include_router(router)

app = gr.mount_gradio_app(app, login_demo, path="/main")
app = gr.mount_gradio_app(app, main_demo, path="/gradio", auth_dependency=get_user, show_error=True)

if __name__ == "__main__":
    uvicorn.run(app)
    
    