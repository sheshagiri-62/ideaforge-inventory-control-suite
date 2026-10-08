"""
Unit tests for deletion confirmation feature.
Tests INV-8: Confirm before deletion user story.
"""

import pytest
from unittest.mock import Mock, patch, call
from src.cli import CLI


class TestDeletionConfirmation:
    """Test deletion confirmation functionality."""

    @pytest.fixture
    def cli(self):
        """Create CLI instance for testing."""
        return CLI()

    def test_confirm_deletion_with_yes_and_delete(self, cli):
        """Test confirmation succeeds with correct inputs."""
        with patch('builtins.input', side_effect=['yes', 'DELETE']):
            result = cli.confirm_deletion("Product", "Test Product (SKU: TEST001)")
            assert result is True

    def test_confirm_deletion_with_no(self, cli):
        """Test confirmation fails when user says no."""
        with patch('builtins.input', side_effect=['no']):
            result = cli.confirm_deletion("Product", "Test Product")
            assert result is False

    def test_confirm_deletion_with_n(self, cli):
        """Test confirmation fails with 'n'."""
        with patch('builtins.input', side_effect=['n']):
            result = cli.confirm_deletion("Product", "Test Product")
            assert result is False

    def test_confirm_deletion_with_wrong_second_input(self, cli):
        """Test confirmation fails with incorrect DELETE confirmation."""
        with patch('builtins.input', side_effect=['yes', 'delete']):  # lowercase
            result = cli.confirm_deletion("Product", "Test Product")
            assert result is False

    def test_confirm_deletion_with_wrong_text(self, cli):
        """Test confirmation fails with wrong confirmation text."""
        with patch('builtins.input', side_effect=['yes', 'REMOVE']):
            result = cli.confirm_deletion("Product", "Test Product")
            assert result is False

    def test_confirm_deletion_with_empty_first_input(self, cli):
        """Test confirmation fails with empty first input."""
        with patch('builtins.input', side_effect=['', 'DELETE']):
            result = cli.confirm_deletion("Product", "Test Product")
            assert result is False

    def test_confirm_deletion_with_y_and_delete(self, cli):
        """Test confirmation succeeds with 'y' shorthand."""
        with patch('builtins.input', side_effect=['y', 'DELETE']):
            result = cli.confirm_deletion("Product", "Test Product")
            assert result is True

    def test_confirm_deletion_with_spaces(self, cli):
        """Test confirmation handles extra spaces correctly."""
        with patch('builtins.input', side_effect=['  yes  ', 'DELETE']):
            result = cli.confirm_deletion("Product", "Test Product")
            assert result is True

    def test_confirm_deletion_case_sensitive_delete(self, cli):
        """Test that DELETE must be case-sensitive."""
        with patch('builtins.input', side_effect=['yes', 'Delete']):
            result = cli.confirm_deletion("Product", "Test Product")
            assert result is False

    def test_confirm_deletion_different_item_types(self, cli):
        """Test confirmation works with different item types."""
        with patch('builtins.input', side_effect=['yes', 'DELETE']):
            result = cli.confirm_deletion("Supplier", "ABC Corp (ID: 123)")
            assert result is True

    def test_confirm_deletion_displays_warning(self, cli, capsys):
        """Test that confirmation displays warning message."""
        with patch('builtins.input', side_effect=['yes', 'DELETE']):
            cli.confirm_deletion("Product", "Test Product")
            captured = capsys.readouterr()
            assert "WARNING" in captured.out
            assert "cannot be undone" in captured.out

    def test_confirm_deletion_shows_item_description(self, cli, capsys):
        """Test that item description is shown to user."""
        item_desc = "Gaming Laptop (SKU: LAPTOP001)"
        with patch('builtins.input', side_effect=['yes', 'DELETE']):
            cli.confirm_deletion("Product", item_desc)
            captured = capsys.readouterr()
            assert item_desc in captured.out

    def test_confirm_deletion_shows_audit_message(self, cli, capsys):
        """Test that audit logging message is displayed."""
        with patch('builtins.input', side_effect=['yes', 'DELETE']):
            cli.confirm_deletion("Product", "Test")
            captured = capsys.readouterr()
            assert "logged" in captured.out.lower() or "audit" in captured.out.lower()

    def test_confirm_deletion_cancellation_message_on_no(self, cli, capsys):
        """Test cancellation message shown when user says no."""
        with patch('builtins.input', side_effect=['no']):
            cli.confirm_deletion("Product", "Test")
            captured = capsys.readouterr()
            assert "cancelled" in captured.out.lower() or "canceled" in captured.out.lower()

    def test_confirm_deletion_cancellation_message_on_wrong_delete(self, cli, capsys):
        """Test cancellation message shown when DELETE is wrong."""
        with patch('builtins.input', side_effect=['yes', 'WRONG']):
            cli.confirm_deletion("Product", "Test")
            captured = capsys.readouterr()
            assert "cancelled" in captured.out.lower() or "canceled" in captured.out.lower()

    def test_delete_product_uses_confirmation(self, cli):
        """Test that delete_product calls confirm_deletion."""
        # Mock dependencies
        cli.auth.is_admin = Mock(return_value=True)
        cli.auth.get_current_username = Mock(return_value="admin")
        
        test_product = {
            'id': 1,
            'sku': 'TEST001',
            'name': 'Test Product',
            'category': 'Test',
            'price': 10.0,
            'stock': 5,
            'description': 'Test'
        }
        cli.product_manager.get_product = Mock(return_value=test_product)
        cli.product_manager.delete_product = Mock(return_value=True)
        cli.confirm_deletion = Mock(return_value=True)
        
        with patch('builtins.input', side_effect=['1', '']):  # Product ID, then Enter
            cli.delete_product()
        
        # Verify confirmation was called
        cli.confirm_deletion.assert_called_once()

    def test_delete_product_not_deleted_when_confirmation_fails(self, cli):
        """Test product is not deleted when confirmation is declined."""
        cli.auth.is_admin = Mock(return_value=True)
        
        test_product = {
            'id': 1,
            'sku': 'TEST001',
            'name': 'Test Product',
            'category': 'Test',
            'price': 10.0,
            'stock': 5
        }
        cli.product_manager.get_product = Mock(return_value=test_product)
        cli.product_manager.delete_product = Mock(return_value=True)
        
        # Simulate user declining confirmation
        with patch('builtins.input', side_effect=['1', 'no', '']):
            cli.delete_product()
        
        # Verify delete was NOT called
        cli.product_manager.delete_product.assert_not_called()

    def test_delete_product_deleted_when_confirmation_succeeds(self, cli):
        """Test product is deleted when confirmation succeeds."""
        cli.auth.is_admin = Mock(return_value=True)
        cli.auth.get_current_username = Mock(return_value="admin")
        
        test_product = {
            'id': 1,
            'sku': 'TEST001',
            'name': 'Test Product',
            'category': 'Test',
            'price': 10.0,
            'stock': 5,
            'description': 'Test'
        }
        cli.product_manager.get_product = Mock(return_value=test_product)
        cli.product_manager.delete_product = Mock(return_value=True)
        
        # Simulate user confirming deletion
        with patch('builtins.input', side_effect=['1', 'yes', 'DELETE', '']):
            cli.delete_product()
        
        # Verify delete WAS called
        cli.product_manager.delete_product.assert_called_once_with(1, "admin")

    def test_delete_product_shows_detailed_info(self, cli, capsys):
        """Test that detailed product information is shown before confirmation."""
        cli.auth.is_admin = Mock(return_value=True)
        
        test_product = {
            'id': 42,
            'sku': 'LAPTOP001',
            'name': 'Gaming Laptop',
            'category': 'Electronics',
            'price': 1299.99,
            'stock': 15,
            'description': 'High-end gaming laptop'
        }
        cli.product_manager.get_product = Mock(return_value=test_product)
        
        with patch('builtins.input', side_effect=['42', 'no', '']):
            cli.delete_product()
        
        captured = capsys.readouterr()
        assert 'LAPTOP001' in captured.out
        assert 'Gaming Laptop' in captured.out
        assert '1299.99' in captured.out
        assert '15' in captured.out

    def test_multiple_confirmation_steps_required(self, cli):
        """Test that both confirmation steps are required."""
        # Test that answering only first step isn't enough
        with patch('builtins.input', side_effect=['yes', 'wrong']):
            result = cli.confirm_deletion("Product", "Test")
            assert result is False
        
        # Test that both correct answers are needed
        with patch('builtins.input', side_effect=['yes', 'DELETE']):
            result = cli.confirm_deletion("Product", "Test")
            assert result is True
