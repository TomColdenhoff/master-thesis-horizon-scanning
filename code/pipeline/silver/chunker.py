"""Window-based text chunker (task 25)."""

from __future__ import annotations


def chunk(text: str, size: int, overlap: int) -> list[str]:
    """Split text into overlapping character-window chunks.

    Args:
        text: Plain text to split.
        size: Approximate chunk size in characters.
        overlap: Number of characters shared between consecutive chunks.

    Returns:
        Ordered list of non-empty chunk strings.

    Raises:
        ValueError: If size <= 0, overlap < 0, or overlap >= size.
    """
    if size <= 0:
        raise ValueError(f"size must be > 0, got {size}")
    if overlap < 0:
        raise ValueError(f"overlap must be >= 0, got {overlap}")
    if overlap >= size:
        raise ValueError(f"overlap ({overlap}) must be less than size ({size})")

    step = size - overlap
    chunks = []
    start = 0

    while start < len(text):
        end = start + size
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append(chunk_text)
        start += step

    return chunks
