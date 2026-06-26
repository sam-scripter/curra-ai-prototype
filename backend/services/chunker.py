"""
chunker.py — Text chunking service.

This is the second step in the ingestion pipeline. It takes parsed pages
and splits them into fixed-size token segments suitable for embedding.

Why chunk at all?
  Storing one entire lecture slide as a single vector makes poor RAG.
  If a slide covers three concepts, a query about one concept matches
  weakly because the embedding averages across all three. Chunking
  isolates topics so each chunk matches precisely.

Why 500 tokens?
  - text-embedding-3-small performs well on chunks of 256–512 tokens
  - 500 gives enough context for a complete thought without diluting the signal
  - At ~4 characters per token, 500 tokens ≈ 2,000 characters ≈ one dense slide

Why 50-token overlap?
  A sentence explaining a concept might land at the boundary between two
  chunks. Without overlap, the second chunk loses the beginning of that
  sentence. The 50-token tail of chunk N becomes the 50-token head of
  chunk N+1, preserving continuity.

Why use tiktoken instead of len(text.split())?
  Word count is an approximation. "don't" is 2 tokens, "OpenAI" is 1,
  "pgvector" might be 3. Using the exact tokeniser that the embedding
  model uses means the 500-token limit is a guarantee, not an estimate.
"""

import tiktoken
from typing import TypedDict


class TextChunk(TypedDict):
    """
    One chunk ready for embedding and database storage.

    content:     The text of this chunk — what gets embedded.
    chunk_index: Position of this chunk within the whole document (0-indexed,
                 counting across all pages). Used to reconstruct order.
    page_number: The source page/slide — used for citations in AI responses.
    token_count: Actual number of tokens in this chunk. Useful for debugging.
    """
    content: str
    chunk_index: int
    page_number: int
    token_count: int


# cl100k_base is the tokeniser used by text-embedding-3-small and GPT-4.
# We load it once at module level so it is not re-initialised on every call.
TOKENIZER = tiktoken.get_encoding("cl100k_base")

CHUNK_SIZE = 500   # Target tokens per chunk
OVERLAP    = 50    # Tokens shared between the end of one chunk and the start of the next


def chunk_pages(pages: list[dict]) -> list[TextChunk]:
    """
    Convert a list of ParsedPage objects into a flat list of TextChunk objects.

    Iterates over pages in order, chunking each one independently.
    chunk_index is global across the whole document — chunk 0 is the first
    chunk of the first page, chunk N is wherever we are by the last page.

    Args:
        pages: Output from parser.parse_file() — list of {page_number, text}

    Returns:
        Flat list of TextChunk objects ordered by their position in the document.
    """
    all_chunks: list[TextChunk] = []
    chunk_index = 0  # Increments across pages so the index is document-wide

    for page in pages:
        page_chunks = _chunk_text(
            text=page["text"],
            page_number=page["page_number"],
            start_index=chunk_index,
        )
        all_chunks.extend(page_chunks)
        chunk_index += len(page_chunks)

    return all_chunks


def _chunk_text(text: str, page_number: int, start_index: int) -> list[TextChunk]:
    """
    Split a single block of text into overlapping token-based chunks.

    Algorithm:
      1. Encode the text into a list of integer token IDs
      2. Slide a window of CHUNK_SIZE tokens across the list,
         advancing by (CHUNK_SIZE - OVERLAP) each step
      3. Decode each window back to a string
      4. Wrap in a TextChunk dict

    Args:
        text:        Raw text from one page/slide
        page_number: Source page number, attached to every chunk from this page
        start_index: The chunk_index value to start counting from

    Returns:
        List of TextChunk objects from this page.
    """
    chunks: list[TextChunk] = []

    # Encode text → list of token IDs
    tokens = TOKENIZER.encode(text)

    if not tokens:
        return chunks

    step = CHUNK_SIZE - OVERLAP  # How far to advance the window each iteration
    index = start_index

    for start in range(0, len(tokens), step):
        end = start + CHUNK_SIZE
        chunk_tokens = tokens[start:end]

        # Decode token IDs back to text.
        # errors="ignore" handles edge cases where the window boundary
        # splits a multi-byte character (rare but possible with Unicode).
        chunk_text = TOKENIZER.decode(chunk_tokens, errors="ignore").strip()

        if not chunk_text:
            continue

        chunks.append({
            "content":     chunk_text,
            "chunk_index": index,
            "page_number": page_number,
            "token_count": len(chunk_tokens),
        })

        index += 1

        # Once end exceeds the token list length, we have processed every token.
        # Without this break the loop would produce empty or duplicate chunks.
        if end >= len(tokens):
            break

    return chunks