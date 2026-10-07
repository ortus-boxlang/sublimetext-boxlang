"""Open the BoxLang documentation website."""
import sublime_plugin
import webbrowser

DOCS_URL = 'https://boxlang.ortusbooks.com'
SUPPORT_URL = 'https://www.boxlang.io/plans'
TESTBOX_DOCS_URL = 'https://testbox.ortusbooks.com'


def _open_url(url):
    webbrowser.open_new_tab(url)


class BoxlangOpenDocsCommand(sublime_plugin.ApplicationCommand):
    """Open BoxLang docs in the default browser."""

    def run(self):
        _open_url(DOCS_URL)


class BoxlangGetSupportCommand(sublime_plugin.ApplicationCommand):
    """Open BoxLang support plans in the default browser."""

    def run(self):
        _open_url(SUPPORT_URL)


class BoxlangOpenTestboxDocsCommand(sublime_plugin.ApplicationCommand):
    """Open TestBox documentation in the default browser."""

    def run(self):
        _open_url(TESTBOX_DOCS_URL)