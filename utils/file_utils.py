from pathlib import Path

def load_css(file_path):
    path = Path(__file__).parent.parent / file_path
    if path.is_file():
        with path.open() as file:
            return file.read()
    return ""

def load_html(file_path):
    path = Path(__file__).parent.parent / file_path
    if path.is_file():
        with path.open() as file:
            return file.read()
    return ""