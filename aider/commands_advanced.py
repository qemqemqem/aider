class AdvancedCommandsMixin:
    """Mixin class providing advanced commands."""

    def cmd_document(self, args):
        """Enter document/editor mode using 2 different models. If no prompt provided, switches to document/editor mode."""  # noqa
        return self._generic_chat_command(args, "document")

    def completions_document(self):
        files = set(self.coder.get_all_relative_files())
        files = files - set(self.coder.get_inchat_relative_files())
        files = [self.quote_fname(fn) for fn in files]
        return files
