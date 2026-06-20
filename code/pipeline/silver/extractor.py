"""Text extraction from PDF and DOCX files — strategy pattern (task 23).

Usage:
    extractor = get_extractor("application/pdf")
    text = extractor.extract(Path("file.pdf"))
"""

from __future__ import annotations
import logging
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

log = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """Strategy interface for text extraction."""

    @abstractmethod
    def extract(self, path: Path) -> str:
        """Extract plain text from a file.

        Returns:
            Extracted text, stripped of excess whitespace.

        Raises:
            ValueError: If the file is empty or extraction fails.
        """


class PdfExtractor(BaseExtractor):
    """Extract text from a PDF using pdftotext (poppler)."""

    def extract(self, path: Path) -> str:
        try:
            result = subprocess.run(
                ["pdftotext", "-enc", "UTF-8", str(path), "-"],
                capture_output=True,
                check=True,
            )
            text = result.stdout.decode("utf-8", errors="replace").strip()
        except subprocess.CalledProcessError as exc:
            raise ValueError(f"pdftotext failed for {path.name}: {exc.stderr.decode()!r}") from exc
        except FileNotFoundError as exc:
            raise ValueError("pdftotext not found — install poppler-utils") from exc

        if not text:
            raise ValueError(f"PDF extraction produced empty text for {path.name}")
        return text


class DocxExtractor(BaseExtractor):
    """Extract text from a DOCX using python-docx."""

    def extract(self, path: Path) -> str:
        try:
            from docx import Document
            doc = Document(str(path))
        except Exception as exc:
            raise ValueError(f"Failed to open DOCX {path.name}: {exc}") from exc

        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(paragraphs).strip()

        if not text:
            raise ValueError(f"DOCX extraction produced empty text for {path.name}")
        return text


_REGISTRY: dict[str, BaseExtractor] = {
    "application/pdf": PdfExtractor(),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocxExtractor(),
}


def get_extractor(content_type: str) -> BaseExtractor:
    """Return the correct extractor for a given ContentType.

    Raises:
        KeyError: If the content type is not supported.
    """
    if content_type not in _REGISTRY:
        raise KeyError(f"No extractor registered for content type: {content_type!r}")
    return _REGISTRY[content_type]
