from .document_prompts import DocumentPrompts
from .editblock_coder import EditBlockCoder


class DocumentCoder(EditBlockCoder):
    """A coder that specializes in writing and improving documentation."""

    edit_format = "document"
    gpt_prompts = DocumentPrompts()
