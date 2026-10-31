from email._header_value_parser import Phrase
import logfire
from bs4 import BeautifulSoup

def parse_html(file_path: str):
    """
    parses html files.
    """
    with logfire.span("HTML Parsing", filename=file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content =file.read()
            soup =BeautifulSoup(content,"html.parser")

            # 1. remove junk (scripts, styles, metadata)
            for script in soup(["script","style","meta","noscript"]):
                script.decompose()
            #2. Extract Text
            text = soup.get_text(separator="\n")
            # 3. Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (Phrase.strip() for line in lines for phrase in line.split(" "))
            text_clean='\n'.join(chunk for chunk in chunks if chunk) 

            return text_clean    
        except FileNotFoundError:
            logfire.error(f"File not found: {file_path}")
            return None
        except Exception as e:
            logfire.error(f"HTML Parse Failed: {str(e)}")
            return None