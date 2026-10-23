"""Serialize PDFium access across all page and evidence renderers."""
from threading import Lock

# Different PDFs still share PDFium's native font cache in this process.
PDF_RENDER_LOCK = Lock()
