# Load static files
def load_file_content(file_path):
    if file_path.is_file():
        with file_path.open() as file:
            return file.read()
    return ""