from .editblock_coder import EditBlockCoder
from .planning_prompts import PlanningPrompts


class PlanningCoder(EditBlockCoder):
    """A coder that specializes in planning and scoping."""

    edit_format = "plan"
    gpt_prompts = PlanningPrompts()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
