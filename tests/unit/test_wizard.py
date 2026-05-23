"""
Unit tests for the Wizard (commands/wizard.py).
"""

import pytest
from tests.expectations import expect
from unittest.mock import MagicMock


class TestWizard:
    """Tests for the wizard module."""

    def test_wizard_completed_flag(self, mock_sublime):
        """Test wizard_completed checks settings flag."""
        mock_settings = MagicMock()
        mock_settings.get = MagicMock(return_value=False)
        mock_sublime.load_settings = MagicMock(return_value=mock_settings)

        from src.commands.wizard import wizard_completed
        result = wizard_completed()
        expect(result).to_be_false()

    def test_wizard_completed_true(self, mock_sublime):
        """Test wizard_completed returns True when flag is set."""
        mock_settings = MagicMock()
        mock_settings.get = MagicMock(return_value=True)
        mock_sublime.load_settings = MagicMock(return_value=mock_settings)

        from src.commands.wizard import wizard_completed
        result = wizard_completed()
        expect(result).to_be_true()

    def test_mark_wizard_completed(self, mock_sublime):
        """Test marking wizard as completed."""
        mock_settings = MagicMock()
        mock_sublime.load_settings = MagicMock(return_value=mock_settings)

        from src.commands.wizard import mark_wizard_completed
        mark_wizard_completed()

        mock_settings.set.assert_called_once_with("boxlang_wizard_completed", True)
        mock_sublime.save_settings.assert_called_once()

    def test_cfml_package_not_installed(self, mock_sublime):
        """Test CFML package detection when not installed."""
        mock_sublime.load_resource = MagicMock(side_effect=Exception("Not found"))

        from src.commands.wizard import _is_cfml_package_installed
        result = _is_cfml_package_installed()
        expect(result).to_be_false()

    def test_cfml_package_installed(self, mock_sublime):
        """Test CFML package detection when installed."""
        mock_sublime.load_resource = MagicMock(return_value="# CFML package")

        from src.commands.wizard import _is_cfml_package_installed
        result = _is_cfml_package_installed()
        expect(result).to_be_true()

    def test_set_cfml_fallback_enabled(self, mock_sublime):
        """Test enabling CFML fallback."""
        mock_settings = MagicMock()
        mock_sublime.load_settings = MagicMock(return_value=mock_settings)

        from src.commands.wizard import _set_cfml_fallback
        _set_cfml_fallback(True)

        mock_settings.set.assert_called_once_with("boxlang_enable_cfml_fallback", True)
        mock_sublime.save_settings.assert_called_once()

    def test_set_cfml_fallback_disabled(self, mock_sublime):
        """Test disabling CFML fallback."""
        mock_settings = MagicMock()
        mock_sublime.load_settings = MagicMock(return_value=mock_settings)

        from src.commands.wizard import _set_cfml_fallback
        _set_cfml_fallback(False)

        mock_settings.set.assert_called_once_with("boxlang_enable_cfml_fallback", False)


class TestWizardCommand:
    """Tests for the wizard command class."""

    def test_wizard_command_exists(self):
        """Test that the wizard command class exists."""
        from src.commands.wizard import BoxlangRunWizardCommand
        expect(BoxlangRunWizardCommand).not_to_be_none()
