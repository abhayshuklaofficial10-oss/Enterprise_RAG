from typing import List
import logfire

def chunk_text(text:str,chunk_size:int=1500) -> List[str]:
    """
    simple semantic-ish chunker that splits by paragraph.
    ensure chunks do not exceed the specified size.
    """

    with logfire.span("Text Chunking", text_length=len(text)):
        if not text.strip():
            return []

        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk =""

        for p in paragraphs:
            if len(current_chunk) + len(p) < chunk_size:
                current_chunk += "\n\n" + p
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = p  + "\n\n"

        if current_chunk:
            chunks.append(current_chunk.strip())
        
        valid_chunks=[c for c in chunks if c.strip()]
        logfire.info(f"Genrated {len(valid_chunks)} chunks")
        return valid_chunks



