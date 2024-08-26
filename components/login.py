import gradio as gr

def create_login_demo(login_css, landing_page):
    with gr.Blocks(theme=gr.themes.Soft(), css=login_css) as login_demo:
        with gr.Column(elem_id="google-btn-container", elem_classes="google-btn-container svelte-vt1mxs gap"):
            btn = gr.Button("Iniciar Sesion con Google", elem_classes="login-with-google-btn")
        _js_redirect = """
        () => {
            url = '/login' + window.location.search;
            window.open(url, '_blank');
        }
        """
        btn.click(None, js=_js_redirect)
        gr.HTML(landing_page)
    return login_demo