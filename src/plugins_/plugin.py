"""
Base plugin class for BoxLang.
"""


class BoxlangPlugin:
    """Base class for BoxLang plugins."""

    def get_completion_docs(self, boxlang_view):
        """Get completion documentation."""
        return None

    def get_completions(self, boxlang_view):
        """Get completions."""
        return None

    def get_goto_boxlang_file(self, boxlang_view):
        """Get file navigation info."""
        return None

    def get_inline_documentation(self, boxlang_view, doc_type):
        """Get inline documentation."""
        return None

    def get_method_preview(self, boxlang_view):
        """Get method preview."""
        return None
