
import logfire
from bs4 import BeautifulSoup


def parse_html(file_path: str) -> str | None:
    """
    Parses an HTML file and returns cleaned plain text.

    Returns None when the file cannot be read or parsed.
    """
    with logfire.span("HTML Parsing", filename=file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()

            soup = BeautifulSoup(content, "html.parser")

            # Remove junk (scripts, styles, metadata, noscript)
            for tag in soup(["script", "style", "meta", "noscript"]):
                tag.decompose()

            # Extract text
            text = soup.get_text(separator="\n")

            # Clean up whitespace: strip each line, split on spaces, drop blanks
            lines = (line.strip() for line in text.splitlines())
            chunks = (
                phrase.strip()
                for line in lines
                for phrase in line.split(" ")
            )
            text_clean = "\n".join(chunk for chunk in chunks if chunk)

            return text_clean or None
        except FileNotFoundError:
            logfire.error(f"File not found: {file_path}")
            return None
        except Exception as e:
            logfire.error(f"HTML Parse Failed: {str(e)}")
            return None
