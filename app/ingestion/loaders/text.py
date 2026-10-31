import logfire

def parse_text(file_path: str):
    """
    parses plain text files.
    """
    with logfire.span("Text Parsing", filename=file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            logfire.error(f"File not found: {file_path}")
            return None
        except Exception as e:
            logfire.error(f"Text Parse Failed: {str(e)}")
            return None
    