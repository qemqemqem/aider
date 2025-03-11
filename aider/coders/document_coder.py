from .base_coder import Coder
from .document_prompts import DocumentPrompts


class DocumentCoder(Coder):
    """Improve documentation without changing functional code."""

    edit_format = "document"
    gpt_prompts = DocumentPrompts()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
