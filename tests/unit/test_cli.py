"""
Unit tests for CLI module.
Tests INV-NF-005 (User-friendly CLI) and INV-F-002 (View/Search Products).
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from io import StringIO
from src.cli import CLI
from src.storage import StorageManager
from src.product_manager import ProductManager


class TestCLI:
    """Test CLI functionality."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.sqlite')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def cli_with_db(self, temp_db):
        """Create CLI with temporary database."""
        storage = StorageManager(temp_db)
        
        with patch('src.cli.AuthManager') as MockAuth, \
             patch('src.cli.SupplierManager'), \
             patch('src.cli.OrderProcessor'), \
             patch('src.cli.BackupManager'):
            cli = CLI()
            cli.storage = storage
            cli.product_manager = ProductManager(storage, cli.logger)
            # Mock auth methods
            cli.auth.get_current_username.return_value = "testuser"
            cli.auth.is_authenticated.return_value = True
            cli.auth.is_admin.return_value = False
            return cli

    def test_cli_init(self, cli_with_db):
        """Test CLI initialization."""
        assert cli_with_db.storage is not None
        assert cli_with_db.auth is not None
        assert cli_with_db.logger is not None
        assert cli_with_db.product_manager is not None
        assert cli_with_db.running is True

    def test_print_header(self, cli_with_db, capsys):
        """Test header printing."""
        cli_with_db.print_header("Test Header")
        captured = capsys.readouterr()
        assert "Test Header" in captured.out
        assert "=" in captured.out

    def test_input_with_prompt_valid(self, cli_with_db):
        """Test input with valid value."""
        with patch('builtins.input', return_value='test value'):
            result = cli_with_db.input_with_prompt("Enter value")
            assert result == 'test value'

    def test_input_with_prompt_required(self, cli_with_db):
        """Test input with required field validation."""
        with patch('builtins.input', side_effect=['', '  ', 'valid']):
            result = cli_with_db.input_with_prompt("Enter value", required=True)
            assert result == 'valid'

    def test_input_with_prompt_not_required(self, cli_with_db):
        """Test input with optional field."""
        with patch('builtins.input', return_value=''):
            result = cli_with_db.input_with_prompt("Enter value", required=False)
            assert result == ''

    def test_input_number_valid_int(self, cli_with_db):
        """Test numeric input with valid integer."""
        with patch('builtins.input', return_value='42'):
            result = cli_with_db.input_number("Enter number")
            assert result == 42

    def test_input_number_valid_float(self, cli_with_db):
        """Test numeric input with valid float."""
        with patch('builtins.input', return_value='42.5'):
            result = cli_with_db.input_number("Enter number", allow_float=True)
            assert result == 42.5

    def test_input_number_invalid_then_valid(self, cli_with_db):
        """Test numeric input with invalid then valid value."""
        with patch('builtins.input', side_effect=['abc', '123']):
            result = cli_with_db.input_number("Enter number")
            assert result == 123

    def test_view_products_empty(self, cli_with_db, capsys):
        """Test viewing products when none exist."""
        with patch('builtins.input', return_value=''):
            cli_with_db.view_products()
            captured = capsys.readouterr()
            assert "No products found" in captured.out

    def test_view_products_with_data(self, cli_with_db, capsys):
        """Test viewing products with data (INV-F-002)."""
        # Add some products
        cli_with_db.product_manager.add_product(
            "SKU001", "Product 1", 10.00, "Category1", 50, "Description 1"
        )
        cli_with_db.product_manager.add_product(
            "SKU002", "Product 2", 20.00, "Category2", 30, "Description 2"
        )
        
        with patch('builtins.input', return_value=''):
            cli_with_db.view_products()
            captured = capsys.readouterr()
            assert "SKU001" in captured.out
            assert "Product 1" in captured.out
            assert "SKU002" in captured.out
            assert "Product 2" in captured.out

    def test_search_products_found(self, cli_with_db, capsys):
        """Test searching products with results (INV-F-002)."""
        # Add products
        cli_with_db.product_manager.add_product(
            "LAPTOP001", "Gaming Laptop", 1299.99, "Electronics", 10
        )
        cli_with_db.product_manager.add_product(
            "MOUSE001", "Gaming Mouse", 29.99, "Electronics", 50
        )
        
        with patch('builtins.input', side_effect=['Gaming', '']):
            cli_with_db.search_products()
            captured = capsys.readouterr()
            assert "Found 2 product(s)" in captured.out
            assert "LAPTOP001" in captured.out
            assert "MOUSE001" in captured.out

    def test_search_products_not_found(self, cli_with_db, capsys):
        """Test searching products with no results."""
        with patch('builtins.input', side_effect=['NonExistent', '']):
            cli_with_db.search_products()
            captured = capsys.readouterr()
            assert "Found 0 product(s)" in captured.out
            assert "No products found" in captured.out

    def test_add_product_success(self, cli_with_db, capsys):
        """Test adding product successfully."""
        # Mock the auth.get_current_username to return a string
        cli_with_db.auth.get_current_username = MagicMock(return_value="testuser")
        
        inputs = ['SKU123', 'Test Product', '99.99', 'Test Category', '25', 'Test Description', '']
        
        with patch('builtins.input', side_effect=inputs):
            cli_with_db.add_product()
            captured = capsys.readouterr()
            assert "[OK] Product added successfully" in captured.out

    def test_add_product_duplicate_sku(self, cli_with_db, capsys):
        """Test adding product with duplicate SKU."""
        # Add first product
        cli_with_db.product_manager.add_product("DUP001", "Product 1", 10.00, "Cat", 5)
        
        # Try to add duplicate
        inputs = ['DUP001', 'Product 2', '20.00', 'Cat', '10', '', '']
        
        with patch('builtins.input', side_effect=inputs):
            cli_with_db.add_product()
            captured = capsys.readouterr()
            assert "already exists" in captured.out

    def test_add_product_invalid_price(self, cli_with_db, capsys):
        """Test adding product with invalid price."""
        inputs = ['SKU123', 'Test Product', '-10.00', 'Test Category', '25', '', '']
        
        with patch('builtins.input', side_effect=inputs):
            cli_with_db.add_product()
            captured = capsys.readouterr()
            assert "Error" in captured.out

    def test_show_help(self, cli_with_db, capsys):
        """Test help display."""
        with patch('builtins.input', return_value=''):
            cli_with_db.show_help()
            captured = capsys.readouterr()
            assert "HELP & INFORMATION" in captured.out or "User Guide" in captured.out
            assert "Product Management" in captured.out

    def test_exit_application(self, cli_with_db, capsys):
        """Test application exit."""
        cli_with_db.exit_application()
        captured = capsys.readouterr()
        assert "Thank you" in captured.out
        assert "Goodbye" in captured.out
        assert cli_with_db.running is False

    def test_product_menu_view_products(self, cli_with_db, capsys):
        """Test product menu - view products option."""
        # Add a product first
        cli_with_db.product_manager.add_product("TEST001", "Test", 10.00, "Cat", 5)
        
        with patch('builtins.input', side_effect=['2', '', '0']):
            cli_with_db.product_menu()
            captured = capsys.readouterr()
            assert "TEST001" in captured.out

    def test_product_menu_search_products(self, cli_with_db, capsys):
        """Test product menu - search products option."""
        cli_with_db.product_manager.add_product("SEARCH001", "Searchable", 10.00, "Cat", 5)
        
        with patch('builtins.input', side_effect=['3', 'Searchable', '', '0']):
            cli_with_db.product_menu()
            captured = capsys.readouterr()
            assert "SEARCH001" in captured.out

    def test_product_menu_invalid_option(self, cli_with_db, capsys):
        """Test product menu with invalid option."""
        with patch('builtins.input', side_effect=['99', '', '0']):
            cli_with_db.product_menu()
            captured = capsys.readouterr()
            assert "Invalid option" in captured.out

    def test_product_menu_back_to_main(self, cli_with_db):
        """Test product menu - back to main menu."""
        with patch('builtins.input', return_value='0'):
            cli_with_db.product_menu()
            # Should exit cleanly without error

    def test_clear_screen_windows(self, cli_with_db):
        """Test clear screen on Windows."""
        with patch('os.name', 'nt'):
            with patch('os.system') as mock_system:
                cli_with_db.clear_screen()
                mock_system.assert_called_once_with('cls')

    def test_clear_screen_unix(self, cli_with_db, capsys):
        """Test clear screen on Unix/Linux."""
        with patch('os.name', 'posix'):
            cli_with_db.clear_screen()
            captured = capsys.readouterr()
            # Should output ANSI escape codes
            assert len(captured.out) > 0

    def test_update_product_success(self, cli_with_db, capsys):
        """Test updating product successfully."""
        # Add a product first
        product_id = cli_with_db.product_manager.add_product(
            "UPDATE001", "Old Product", 100.00, "Electronics", 50
        )
        
        # Mock input for update: product_id, name, price, category, stock, description
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            'New Product Name',  # New name
            '150.50',  # New price
            'New Category',  # New category
            '75',  # New stock
            'New description',  # New description
            ''  # Press Enter to continue
        ]):
            cli_with_db.update_product()
            captured = capsys.readouterr()
            assert "Product updated successfully" in captured.out
        
        # Verify the product was actually updated
        product = cli_with_db.product_manager.get_product(product_id)
        assert product['name'] == 'New Product Name'
        assert product['price'] == 150.50
        assert product['category'] == 'New Category'
        assert product['stock'] == 75

    def test_update_product_not_found(self, cli_with_db, capsys):
        """Test updating non-existent product."""
        with patch('builtins.input', side_effect=['99999', '']):
            cli_with_db.update_product()
            captured = capsys.readouterr()
            assert "Product not found" in captured.out

    def test_update_product_partial_update(self, cli_with_db, capsys):
        """Test updating only some fields."""
        # Add a product first
        product_id = cli_with_db.product_manager.add_product(
            "PARTIAL001", "Original Name", 100.00, "Cat1", 50
        )
        
        # Update only price and stock (leave other fields blank)
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            '',  # Keep name
            '200.00',  # New price
            '',  # Keep category
            '100',  # New stock
            '',  # Keep description
            ''  # Press Enter to continue
        ]):
            cli_with_db.update_product()
            captured = capsys.readouterr()
            assert "Product updated successfully" in captured.out
        
        # Verify partial update
        product = cli_with_db.product_manager.get_product(product_id)
        assert product['name'] == 'Original Name'  # Unchanged
        assert product['price'] == 200.00  # Changed
        assert product['category'] == 'Cat1'  # Unchanged
        assert product['stock'] == 100  # Changed

    def test_update_product_no_changes(self, cli_with_db, capsys):
        """Test update with no fields changed."""
        # Add a product first
        product_id = cli_with_db.product_manager.add_product(
            "NOCHANGE001", "Product", 100.00, "Cat", 50
        )
        
        # Leave all fields blank
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            '',  # No name change
            '',  # No price change
            '',  # No category change
            '',  # No stock change
            '',  # No description change
            ''  # Press Enter to continue
        ]):
            cli_with_db.update_product()
            captured = capsys.readouterr()
            assert "No changes made" in captured.out

    def test_update_product_invalid_price(self, cli_with_db, capsys):
        """Test updating product with invalid price."""
        # Add a product first
        product_id = cli_with_db.product_manager.add_product(
            "INVALID001", "Product", 100.00, "Cat", 50
        )
        
        # Try to update with negative price
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            '',  # Keep name
            '-50.00',  # Invalid negative price
            '',  # Keep category
            '',  # Keep stock
            '',  # Keep description
            ''  # Press Enter to continue
        ]):
            cli_with_db.update_product()
            captured = capsys.readouterr()
            assert "Error" in captured.out

    def test_update_product_invalid_id(self, cli_with_db, capsys):
        """Test updating product with invalid ID format."""
        with patch('builtins.input', side_effect=['invalid', '']):
            cli_with_db.update_product()
            captured = capsys.readouterr()
            assert "Error" in captured.out

    def test_product_menu_update_option(self, cli_with_db, capsys):
        """Test product menu - update product option."""
        # Add a product first
        product_id = cli_with_db.product_manager.add_product(
            "MENU001", "Menu Product", 50.00, "Cat", 25
        )
        
        # Select update option from menu
        with patch('builtins.input', side_effect=[
            '4',  # Select Update Product
            str(product_id),  # Product ID
            'Updated Name',  # New name
            '',  # Keep price
            '',  # Keep category
            '',  # Keep stock
            '',  # Keep description
            '',  # Press Enter after update
            '0'  # Exit menu
        ]):
            cli_with_db.product_menu()
            captured = capsys.readouterr()
            assert "UPDATE PRODUCT" in captured.out

    def test_adjust_stock_quantity_increase(self, cli_with_db, capsys):
        """Test increasing stock quantity."""
        # Add a product first
        product_id = cli_with_db.product_manager.add_product(
            "STOCK001", "Stock Test", 50.00, "Cat", 100
        )
        
        # Increase stock by 50
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            '1',  # Increase stock
            '50',  # Quantity to add
            ''  # Press Enter
        ]):
            cli_with_db.adjust_stock_quantity()
            captured = capsys.readouterr()
            assert "Stock increased successfully" in captured.out
            assert "New stock: 150" in captured.out
        
        # Verify the stock was actually increased
        product = cli_with_db.product_manager.get_product(product_id)
        assert product['stock'] == 150

    def test_adjust_stock_quantity_decrease(self, cli_with_db, capsys):
        """Test decreasing stock quantity."""
        # Add a product first
        product_id = cli_with_db.product_manager.add_product(
            "STOCK002", "Stock Test", 50.00, "Cat", 100
        )
        
        # Decrease stock by 30
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            '2',  # Decrease stock
            '30',  # Quantity to remove
            ''  # Press Enter
        ]):
            cli_with_db.adjust_stock_quantity()
            captured = capsys.readouterr()
            assert "Stock decreased successfully" in captured.out
            assert "New stock: 70" in captured.out
        
        # Verify the stock was actually decreased
        product = cli_with_db.product_manager.get_product(product_id)
        assert product['stock'] == 70

    def test_adjust_stock_quantity_set_exact(self, cli_with_db, capsys):
        """Test setting exact stock quantity."""
        # Add a product first
        product_id = cli_with_db.product_manager.add_product(
            "STOCK003", "Stock Test", 50.00, "Cat", 100
        )
        
        # Set stock to exactly 200
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            '3',  # Set exact quantity
            '200',  # New stock quantity
            ''  # Press Enter
        ]):
            cli_with_db.adjust_stock_quantity()
            captured = capsys.readouterr()
            assert "Stock set successfully" in captured.out
            assert "New stock: 200" in captured.out
        
        # Verify the stock was actually set
        product = cli_with_db.product_manager.get_product(product_id)
        assert product['stock'] == 200

    def test_adjust_stock_quantity_not_found(self, cli_with_db, capsys):
        """Test adjusting stock for non-existent product."""
        with patch('builtins.input', side_effect=['99999', '']):
            cli_with_db.adjust_stock_quantity()
            captured = capsys.readouterr()
            assert "Product not found" in captured.out

    def test_adjust_stock_quantity_insufficient(self, cli_with_db, capsys):
        """Test decreasing more stock than available."""
        # Add a product first
        product_id = cli_with_db.product_manager.add_product(
            "STOCK004", "Stock Test", 50.00, "Cat", 10
        )
        
        # Try to decrease by more than available
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            '2',  # Decrease stock
            '20',  # Quantity to remove (more than available)
            ''  # Press Enter
        ]):
            cli_with_db.adjust_stock_quantity()
            captured = capsys.readouterr()
            assert "Cannot remove" in captured.out

    def test_adjust_stock_quantity_negative_input(self, cli_with_db, capsys):
        """Test adjusting stock with negative input."""
        # Add a product first
        product_id = cli_with_db.product_manager.add_product(
            "STOCK005", "Stock Test", 50.00, "Cat", 100
        )
        
        # Try to add negative quantity
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            '1',  # Increase stock
            '-10',  # Negative quantity
            ''  # Press Enter
        ]):
            cli_with_db.adjust_stock_quantity()
            captured = capsys.readouterr()
            assert "Quantity must be positive" in captured.out

    def test_product_menu_adjust_stock_option(self, cli_with_db, capsys):
        """Test product menu - adjust stock option."""
        # Add a product first
        product_id = cli_with_db.product_manager.add_product(
            "MENU002", "Menu Product", 50.00, "Cat", 50
        )
        
        # Select adjust stock option from menu
        with patch('builtins.input', side_effect=[
            '6',  # Select Adjust Stock Quantity
            str(product_id),  # Product ID
            '1',  # Increase stock
            '25',  # Quantity to add
            '',  # Press Enter after adjustment
            '0'  # Exit menu
        ]):
            cli_with_db.product_menu()
            captured = capsys.readouterr()
            assert "ADJUST STOCK QUANTITY" in captured.out


# ========== Order Processing CLI Tests ==========

class TestOrderProcessingCLI:
    """Test Order Processing CLI functionality (INV-F-010, INV-F-011)."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.sqlite')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def cli_with_product(self, temp_db):
        """Create CLI with a test product."""
        from src.order_processor import OrderProcessor
        storage = StorageManager(temp_db)
        
        with patch('src.cli.AuthManager') as MockAuth, \
             patch('src.cli.SupplierManager'), \
             patch('src.cli.BackupManager'):
            cli = CLI()
            cli.storage = storage
            cli.product_manager = ProductManager(storage, cli.logger)
            cli.order_processor = OrderProcessor(storage, cli.logger, cli.product_manager)
            
            # Create a test product
            product_id = cli.product_manager.add_product(
                sku='TEST001',
                name='Test Product',
                category='Electronics',
                price=99.99,
                stock=100,
                user='testuser'
            )
            
            # Mock auth methods
            cli.auth.get_current_username.return_value = "testuser"
            cli.auth.is_authenticated.return_value = True
            cli.auth.is_admin.return_value = False
            
            return cli, product_id

    def test_create_sales_order_success(self, cli_with_product, capsys):
        """Test successful sales order creation (INV-F-010)."""
        cli, product_id = cli_with_product
        
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            '10',  # Quantity
            'yes',  # Confirm
            ''  # Press Enter
        ]):
            cli.create_sales_order()
            captured = capsys.readouterr()
            assert "CREATE SALES ORDER" in captured.out
            assert "Sales order created successfully" in captured.out
            assert "Order ID:" in captured.out
            assert "Remaining stock: 90 units" in captured.out

    def test_create_sales_order_insufficient_stock(self, cli_with_product, capsys):
        """Test sales order with insufficient stock (INV-F-011)."""
        cli, product_id = cli_with_product
        
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            '150',  # Quantity > stock
            ''  # Press Enter
        ]):
            cli.create_sales_order()
            captured = capsys.readouterr()
            assert "Insufficient stock" in captured.out

    def test_create_sales_order_product_not_found(self, cli_with_product, capsys):
        """Test sales order with non-existent product."""
        cli, _ = cli_with_product
        
        with patch('builtins.input', side_effect=[
            '99999',  # Invalid product ID
            ''  # Press Enter
        ]):
            cli.create_sales_order()
            captured = capsys.readouterr()
            assert "Product with ID 99999 not found" in captured.out

    def test_create_sales_order_invalid_quantity(self, cli_with_product, capsys):
        """Test sales order with invalid quantity."""
        cli, product_id = cli_with_product
        
        # Test zero quantity
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            '0',  # Invalid quantity
            ''  # Press Enter
        ]):
            cli.create_sales_order()
            captured = capsys.readouterr()
            assert "Quantity must be positive" in captured.out

    def test_create_sales_order_negative_quantity(self, cli_with_product, capsys):
        """Test sales order with negative quantity."""
        cli, product_id = cli_with_product
        
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            '-5',  # Negative quantity
            ''  # Press Enter
        ]):
            cli.create_sales_order()
            captured = capsys.readouterr()
            assert "Quantity must be positive" in captured.out

    def test_create_sales_order_cancelled(self, cli_with_product, capsys):
        """Test cancelling sales order."""
        cli, product_id = cli_with_product
        
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            '10',  # Quantity
            'no',  # Don't confirm
            ''  # Press Enter
        ]):
            cli.create_sales_order()
            captured = capsys.readouterr()
            assert "Order cancelled" in captured.out

    def test_create_sales_order_display_info(self, cli_with_product, capsys):
        """Test that sales order displays product information."""
        cli, product_id = cli_with_product
        
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            '10',  # Quantity
            'yes',  # Confirm
            ''  # Press Enter
        ]):
            cli.create_sales_order()
            captured = capsys.readouterr()
            assert "Test Product" in captured.out
            assert "TEST001" in captured.out
            assert "$99.99" in captured.out
            assert "Available Stock: 100 units" in captured.out

    def test_create_sales_order_order_summary(self, cli_with_product, capsys):
        """Test that sales order displays order summary."""
        cli, product_id = cli_with_product
        
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            '10',  # Quantity
            'yes',  # Confirm
            ''  # Press Enter
        ]):
            cli.create_sales_order()
            captured = capsys.readouterr()
            assert "Order Summary:" in captured.out
            assert "Quantity: 10 units" in captured.out
            assert "Total Price:" in captured.out

    def test_order_menu_display(self, cli_with_product, capsys):
        """Test order menu display."""
        cli, _ = cli_with_product
        
        with patch('builtins.input', side_effect=[
            '0'  # Exit menu
        ]):
            cli.order_menu()
            captured = capsys.readouterr()
            assert "ORDER PROCESSING" in captured.out
            assert "1. Create Sales Order" in captured.out
            assert "2. Create Purchase Order" in captured.out
            assert "3. View Sales Orders" in captured.out
            assert "4. View Purchase Orders" in captured.out

    def test_order_menu_create_sales_order_option(self, cli_with_product, capsys):
        """Test selecting create sales order from menu."""
        cli, product_id = cli_with_product
        
        with patch('builtins.input', side_effect=[
            '1',  # Select Create Sales Order
            str(product_id),  # Product ID
            '5',  # Quantity
            'yes',  # Confirm
            '',  # Press Enter after order
            '0'  # Exit menu
        ]):
            cli.order_menu()
            captured = capsys.readouterr()
            assert "CREATE SALES ORDER" in captured.out
            assert "Sales order created successfully" in captured.out

    def test_create_purchase_order_success(self, cli_with_product, capsys):
        """Test successful purchase order creation."""
        cli, product_id = cli_with_product
        
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            '1',  # Supplier ID (optional)
            '50',  # Quantity
            '75.00',  # Unit price
            'yes',  # Confirm
            ''  # Press Enter
        ]):
            cli.create_purchase_order()
            captured = capsys.readouterr()
            assert "Purchase order recorded successfully" in captured.out
            assert "Order ID:" in captured.out
            assert "Total: $3750.00" in captured.out
            assert "New stock: 150 units" in captured.out

    def test_create_purchase_order_no_supplier(self, cli_with_product, capsys):
        """Test purchase order without supplier ID."""
        cli, product_id = cli_with_product
        
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            '',  # No supplier ID
            '25',  # Quantity
            '80.00',  # Unit price
            'yes',  # Confirm
            ''  # Press Enter
        ]):
            cli.create_purchase_order()
            captured = capsys.readouterr()
            assert "Purchase order recorded successfully" in captured.out
            assert "Total: $2000.00" in captured.out

    def test_create_purchase_order_product_not_found(self, cli_with_product, capsys):
        """Test purchase order with non-existent product."""
        cli, _ = cli_with_product
        
        with patch('builtins.input', side_effect=[
            '99999',  # Invalid product ID
            ''  # Press Enter
        ]):
            cli.create_purchase_order()
            captured = capsys.readouterr()
            assert "Product with ID 99999 not found" in captured.out

    def test_create_purchase_order_invalid_product_id(self, cli_with_product, capsys):
        """Test purchase order with invalid product ID format."""
        cli, _ = cli_with_product
        
        with patch('builtins.input', side_effect=[
            'abc',  # Invalid product ID
            ''  # Press Enter
        ]):
            cli.create_purchase_order()
            captured = capsys.readouterr()
            assert "Product ID must be a number" in captured.out

    def test_create_purchase_order_empty_product_id(self, cli_with_product, capsys):
        """Test purchase order with empty product ID."""
        cli, _ = cli_with_product
        
        with patch('builtins.input', side_effect=[
            '',  # Empty product ID
            ''  # Press Enter
        ]):
            cli.create_purchase_order()
            captured = capsys.readouterr()
            assert "Product ID cannot be empty" in captured.out

    def test_create_purchase_order_invalid_supplier_id(self, cli_with_product, capsys):
        """Test purchase order with invalid supplier ID format."""
        cli, product_id = cli_with_product
        
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            'abc',  # Invalid supplier ID
            '20',  # Quantity
            '50.00',  # Unit price
            'yes',  # Confirm
            ''  # Press Enter
        ]):
            cli.create_purchase_order()
            captured = capsys.readouterr()
            assert "Supplier ID must be a number if provided" in captured.out
            # Should still succeed with None supplier
            assert "Purchase order recorded successfully" in captured.out

    def test_create_purchase_order_zero_quantity(self, cli_with_product, capsys):
        """Test purchase order with zero quantity."""
        cli, product_id = cli_with_product
        
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            '',  # No supplier
            '0',  # Zero quantity
            ''  # Press Enter
        ]):
            cli.create_purchase_order()
            captured = capsys.readouterr()
            assert "Quantity must be positive" in captured.out

    def test_create_purchase_order_negative_quantity(self, cli_with_product, capsys):
        """Test purchase order with negative quantity."""
        cli, product_id = cli_with_product
        
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            '',  # No supplier
            '-10',  # Negative quantity
            ''  # Press Enter
        ]):
            cli.create_purchase_order()
            captured = capsys.readouterr()
            assert "Quantity must be positive" in captured.out

    def test_create_purchase_order_invalid_quantity(self, cli_with_product, capsys):
        """Test purchase order with invalid quantity format."""
        cli, product_id = cli_with_product
        
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            '',  # No supplier
            'abc',  # Invalid quantity
            ''  # Press Enter
        ]):
            cli.create_purchase_order()
            captured = capsys.readouterr()
            assert "Quantity must be a number" in captured.out

    def test_create_purchase_order_empty_quantity(self, cli_with_product, capsys):
        """Test purchase order with empty quantity."""
        cli, product_id = cli_with_product
        
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            '',  # No supplier
            '',  # Empty quantity
            ''  # Press Enter
        ]):
            cli.create_purchase_order()
            captured = capsys.readouterr()
            assert "Quantity cannot be empty" in captured.out

    def test_create_purchase_order_negative_price(self, cli_with_product, capsys):
        """Test purchase order with negative unit price."""
        cli, product_id = cli_with_product
        
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            '',  # No supplier
            '10',  # Quantity
            '-50.00',  # Negative price
            ''  # Press Enter
        ]):
            cli.create_purchase_order()
            captured = capsys.readouterr()
            assert "Unit price cannot be negative" in captured.out

    def test_create_purchase_order_invalid_price(self, cli_with_product, capsys):
        """Test purchase order with invalid price format."""
        cli, product_id = cli_with_product
        
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            '',  # No supplier
            '10',  # Quantity
            'abc',  # Invalid price
            ''  # Press Enter
        ]):
            cli.create_purchase_order()
            captured = capsys.readouterr()
            assert "Unit price must be a number" in captured.out

    def test_create_purchase_order_empty_price(self, cli_with_product, capsys):
        """Test purchase order with empty price."""
        cli, product_id = cli_with_product
        
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            '',  # No supplier
            '10',  # Quantity
            '',  # Empty price
            ''  # Press Enter
        ]):
            cli.create_purchase_order()
            captured = capsys.readouterr()
            assert "Unit price cannot be empty" in captured.out

    def test_create_purchase_order_cancelled(self, cli_with_product, capsys):
        """Test cancelling purchase order."""
        cli, product_id = cli_with_product
        
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            '',  # No supplier
            '30',  # Quantity
            '60.00',  # Unit price
            'no',  # Don't confirm
            ''  # Press Enter
        ]):
            cli.create_purchase_order()
            captured = capsys.readouterr()
            assert "Purchase order cancelled" in captured.out

    def test_create_purchase_order_display_summary(self, cli_with_product, capsys):
        """Test that purchase order displays order summary."""
        cli, product_id = cli_with_product
        
        with patch('builtins.input', side_effect=[
            str(product_id),  # Product ID
            '2',  # Supplier ID
            '40',  # Quantity
            '65.50',  # Unit price
            'yes',  # Confirm
            ''  # Press Enter
        ]):
            cli.create_purchase_order()
            captured = capsys.readouterr()
            assert "Order Summary:" in captured.out
            assert "Product: Test Product" in captured.out
            assert "Quantity: 40 units" in captured.out
            assert "Unit Price: $65.50" in captured.out
            assert "Total Price: $2620.00" in captured.out

    def test_order_menu_create_purchase_order_option(self, cli_with_product, capsys):
        """Test selecting create purchase order from menu."""
        cli, product_id = cli_with_product
        
        with patch('builtins.input', side_effect=[
            '2',  # Select Create Purchase Order
            str(product_id),  # Product ID
            '',  # No supplier
            '15',  # Quantity
            '70.00',  # Unit price
            'yes',  # Confirm
            '',  # Press Enter after order
            '0'  # Exit menu
        ]):
            cli.order_menu()
            captured = capsys.readouterr()
            assert "CREATE PURCHASE ORDER" in captured.out
            assert "Purchase order recorded successfully" in captured.out


# ========== Low Stock Filter CLI Tests ==========

class TestLowStockCLI:
    """Test Low Stock Filter CLI functionality (INV-F-032)."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.sqlite')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def cli_with_products(self, temp_db):
        """Create CLI with multiple products at different stock levels."""
        storage = StorageManager(temp_db)
        
        with patch('src.cli.AuthManager') as MockAuth, \
             patch('src.cli.SupplierManager'), \
             patch('src.cli.BackupManager'):
            cli = CLI()
            cli.storage = storage
            cli.product_manager = ProductManager(storage, cli.logger)
            
            # Create products with different stock levels
            # Low stock products (stock <= 5)
            cli.product_manager.add_product(
                sku='LOW001',
                name='Low Stock Product 1',
                category='Electronics',
                price=99.99,
                stock=2,  # Below threshold
                user='testuser'
            )
            
            cli.product_manager.add_product(
                sku='LOW002',
                name='Low Stock Product 2',
                category='Electronics',
                price=149.99,
                stock=5,  # At threshold
                user='testuser'
            )
            
            # Normal stock products
            cli.product_manager.add_product(
                sku='NORMAL001',
                name='Normal Stock Product',
                category='Electronics',
                price=199.99,
                stock=50,  # Above threshold
                user='testuser'
            )
            
            cli.product_manager.add_product(
                sku='NORMAL002',
                name='High Stock Product',
                category='Electronics',
                price=299.99,
                stock=100,  # Well above threshold
                user='testuser'
            )
            
            # Mock auth methods
            cli.auth.get_current_username.return_value = "testuser"
            cli.auth.is_authenticated.return_value = True
            cli.auth.is_admin.return_value = False
            
            return cli

    def test_show_low_stock_with_low_stock_products(self, cli_with_products, capsys):
        """Test showing low stock products when they exist (INV-F-032)."""
        cli = cli_with_products
        
        with patch('builtins.input', side_effect=['']):  # Press Enter
            cli.show_low_stock()
            captured = capsys.readouterr()
            assert "LOW STOCK ALERT" in captured.out
            assert "Threshold: 5" in captured.out
            assert "2 product(s) with low stock:" in captured.out
            assert "Low Stock Product 1" in captured.out
            assert "Low Stock Product 2" in captured.out
            # Normal stock products should not appear
            assert "Normal Stock Product" not in captured.out
            assert "High Stock Product" not in captured.out

    def test_show_low_stock_displays_threshold(self, cli_with_products, capsys):
        """Test that low stock alert displays the threshold value."""
        cli = cli_with_products
        
        with patch('builtins.input', side_effect=['']):  # Press Enter
            cli.show_low_stock()
            captured = capsys.readouterr()
            assert "Threshold: 5" in captured.out

    def test_show_low_stock_displays_product_details(self, cli_with_products, capsys):
        """Test that low stock alert displays product details."""
        cli = cli_with_products
        
        with patch('builtins.input', side_effect=['']):  # Press Enter
            cli.show_low_stock()
            captured = capsys.readouterr()
            assert "LOW001" in captured.out  # SKU
            assert "LOW002" in captured.out  # SKU
            assert "$99.99" in captured.out  # Price
            assert "$149.99" in captured.out  # Price

    def test_show_low_stock_no_low_stock_products(self, temp_db, capsys):
        """Test showing low stock when all products have adequate stock."""
        storage = StorageManager(temp_db)
        
        with patch('src.cli.AuthManager'), \
             patch('src.cli.SupplierManager'), \
             patch('src.cli.BackupManager'):
            cli = CLI()
            cli.storage = storage
            cli.product_manager = ProductManager(storage, cli.logger)
            
            # Create only normal stock products
            cli.product_manager.add_product(
                sku='NORMAL001',
                name='Normal Stock Product',
                category='Electronics',
                price=199.99,
                stock=50,
                user='testuser'
            )
            
            with patch('builtins.input', side_effect=['']):  # Press Enter
                cli.show_low_stock()
                captured = capsys.readouterr()
                assert "LOW STOCK ALERT" in captured.out
                assert "All products have adequate stock" in captured.out

    def test_show_low_stock_header_formatting(self, cli_with_products, capsys):
        """Test that low stock alert has proper header formatting."""
        cli = cli_with_products
        
        with patch('builtins.input', side_effect=['']):  # Press Enter
            cli.show_low_stock()
            captured = capsys.readouterr()
            # Check for header separator
            assert "=" * 80 in captured.out

    def test_product_menu_low_stock_option(self, cli_with_products, capsys):
        """Test selecting low stock alert from product menu."""
        cli = cli_with_products
        
        with patch('builtins.input', side_effect=[
            '7',  # Select Low Stock Alert
            '',  # Press Enter after viewing
            '0'  # Exit menu
        ]):
            cli.product_menu()
            captured = capsys.readouterr()
            assert "PRODUCT MANAGEMENT" in captured.out
            assert "7. Low Stock Alert" in captured.out
            assert "LOW STOCK ALERT" in captured.out
            assert "2 product(s) with low stock:" in captured.out

    def test_show_low_stock_count_accuracy(self, cli_with_products, capsys):
        """Test that low stock count is accurate."""
        cli = cli_with_products
        
        with patch('builtins.input', side_effect=['']):  # Press Enter
            cli.show_low_stock()
            captured = capsys.readouterr()
            # Should show exactly 2 products (stock 2 and stock 5)
            assert "2 product(s) with low stock:" in captured.out

    def test_show_low_stock_only_shows_at_or_below_threshold(self, temp_db, capsys):
        """Test that only products at or below threshold are shown."""
        storage = StorageManager(temp_db)
        
        with patch('src.cli.AuthManager'), \
             patch('src.cli.SupplierManager'), \
             patch('src.cli.BackupManager'):
            cli = CLI()
            cli.storage = storage
            cli.product_manager = ProductManager(storage, cli.logger)
            
            # Product at threshold
            cli.product_manager.add_product(
                sku='AT_THRESHOLD',
                name='At Threshold Product',
                category='Electronics',
                price=99.99,
                stock=5,  # Exactly at threshold
                user='testuser'
            )
            
            # Product just above threshold
            cli.product_manager.add_product(
                sku='ABOVE_THRESHOLD',
                name='Above Threshold Product',
                category='Electronics',
                price=99.99,
                stock=6,  # Just above threshold
                user='testuser'
            )
            
            with patch('builtins.input', side_effect=['']):  # Press Enter
                cli.show_low_stock()
                captured = capsys.readouterr()
                # Only the product at threshold should show
                assert "At Threshold Product" in captured.out
                assert "Above Threshold Product" not in captured.out
                assert "1 product(s) with low stock:" in captured.out


class TestCLIAuthentication:
    """Test CLI authentication features."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.sqlite')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def cli_with_real_auth(self, temp_db):
        """Create CLI with real auth for testing."""
        with patch('src.cli.SupplierManager'), \
             patch('src.cli.OrderProcessor'), \
             patch('src.cli.BackupManager'):
            cli = CLI()
            cli.storage = StorageManager(temp_db)
            # Reinitialize auth with real storage
            from src.auth import AuthManager
            cli.auth = AuthManager(cli.storage)
            return cli

    def test_login_success(self, cli_with_real_auth, capsys):
        """Test successful login."""
        with patch('builtins.input', side_effect=['admin', 'admin123', '']):
            cli_with_real_auth.login()
            captured = capsys.readouterr()
            assert "[OK] Login successful!" in captured.out
            assert "Welcome, admin" in captured.out
            assert cli_with_real_auth.auth.is_authenticated()

    def test_login_failure(self, cli_with_real_auth, capsys):
        """Test failed login."""
        with patch('builtins.input', side_effect=['admin', 'wrongpassword', '']):
            cli_with_real_auth.login()
            captured = capsys.readouterr()
            assert "[X] Invalid username or password" in captured.out
            assert not cli_with_real_auth.auth.is_authenticated()

    def test_auth_menu_login(self, cli_with_real_auth, capsys):
        """Test auth menu when not logged in."""
        assert not cli_with_real_auth.auth.is_authenticated()
        with patch('builtins.input', side_effect=['admin', 'admin123', '']):
            cli_with_real_auth.auth_menu()
            captured = capsys.readouterr()
            assert "[OK] Login successful!" in captured.out

    def test_auth_menu_logout(self, cli_with_real_auth, capsys):
        """Test auth menu when logged in (logout)."""
        # Login first
        cli_with_real_auth.auth.login('admin', 'admin123')
        assert cli_with_real_auth.auth.is_authenticated()
        
        with patch('builtins.input', return_value=''):
            cli_with_real_auth.auth_menu()
            captured = capsys.readouterr()
            assert "[OK] Logged out successfully" in captured.out
            assert "Goodbye, admin" in captured.out
            assert not cli_with_real_auth.auth.is_authenticated()

    def test_exit_application_with_logout(self, cli_with_real_auth, capsys):
        """Test exit application logs out user."""
        cli_with_real_auth.auth.login('admin', 'admin123')
        assert cli_with_real_auth.auth.is_authenticated()
        
        cli_with_real_auth.exit_application()
        captured = capsys.readouterr()
        assert "Logging out admin" in captured.out
        assert "Thank you" in captured.out
        assert not cli_with_real_auth.running


class TestCLIBackup:
    """Test CLI backup functionality."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.sqlite')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def admin_cli(self, temp_db):
        """Create CLI with admin user."""
        cli = CLI()
        cli.storage = StorageManager(temp_db)
        from src.auth import AuthManager
        cli.auth = AuthManager(cli.storage)
        cli.auth.login('admin', 'admin123')
        return cli

    def test_backup_menu_admin_access(self, admin_cli, capsys):
        """Test backup menu requires admin."""
        assert admin_cli.auth.is_admin()
        with patch('builtins.input', side_effect=['0']):  # Exit menu
            admin_cli.backup_menu()
            captured = capsys.readouterr()
            assert "BACKUP & RESTORE" in captured.out

    def test_backup_menu_non_admin_denied(self, temp_db, capsys):
        """Test backup menu denies non-admin."""
        cli = CLI()
        cli.storage = StorageManager(temp_db)
        from src.auth import AuthManager
        cli.auth = AuthManager(cli.storage)
        # Create and login as regular user
        cli.auth.register_user('user', 'pass123', 'user')
        cli.auth.login('user', 'pass123')
        
        assert not cli.auth.is_admin()
        with patch('builtins.input', return_value=''):
            cli.backup_menu()
            captured = capsys.readouterr()
            assert "[X] Admin privileges required" in captured.out

    def test_create_backup(self, admin_cli, capsys):
        """Test create backup."""
        # Mock the backup manager methods
        admin_cli.backup_manager.create_backup = MagicMock(return_value='/path/to/backup.enc')
        
        with patch('builtins.input', return_value=''):
            admin_cli.create_backup()
            captured = capsys.readouterr()
            assert "CREATE BACKUP" in captured.out

    def test_list_backups(self, admin_cli, capsys):
        """Test list backups."""
        # Mock the backup manager methods
        admin_cli.backup_manager.display_backups = MagicMock()
        
        with patch('builtins.input', return_value=''):
            admin_cli.list_backups()
            captured = capsys.readouterr()
            assert "AVAILABLE BACKUPS" in captured.out

    def test_restore_backup_cancelled(self, admin_cli, capsys):
        """Test restore backup cancelled."""
        # Mock the backup manager methods
        admin_cli.backup_manager.display_backups = MagicMock()
        
        with patch('builtins.input', side_effect=['backup.enc', 'no', '']):
            admin_cli.restore_backup()
            captured = capsys.readouterr()
            assert "Restore cancelled" in captured.out

    def test_delete_backup_cancelled(self, admin_cli, capsys):
        """Test delete backup cancelled."""
        # Mock the backup manager methods
        admin_cli.backup_manager.display_backups = MagicMock()
        
        with patch('builtins.input', side_effect=['backup.enc', 'no', '']):
            admin_cli.delete_backup()
            captured = capsys.readouterr()
            assert "Deletion cancelled" in captured.out


class TestCLILogs:
    """Test CLI logs functionality."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.sqlite')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def admin_cli(self, temp_db):
        """Create CLI with admin user."""
        cli = CLI()
        cli.storage = StorageManager(temp_db)
        from src.auth import AuthManager
        cli.auth = AuthManager(cli.storage)
        cli.auth.login('admin', 'admin123')
        return cli

    def test_logs_menu_admin_access(self, admin_cli, capsys):
        """Test logs menu for admin."""
        with patch('builtins.input', side_effect=['0']):  # Exit menu
            admin_cli.logs_menu()
            captured = capsys.readouterr()
            assert "SYSTEM LOGS" in captured.out

    def test_logs_menu_non_admin_denied(self, temp_db, capsys):
        """Test logs menu denies non-admin."""
        cli = CLI()
        cli.storage = StorageManager(temp_db)
        from src.auth import AuthManager
        cli.auth = AuthManager(cli.storage)
        cli.auth.register_user('user', 'pass123', 'user')
        cli.auth.login('user', 'pass123')
        
        with patch('builtins.input', return_value=''):
            cli.logs_menu()
            captured = capsys.readouterr()
            assert "[X] Admin privileges required" in captured.out

    def test_view_all_logs(self, admin_cli, capsys):
        """Test view all logs."""
        # Add a log entry
        admin_cli.logger.log_action('admin', 'Test Action', 'Test details')
        
        with patch('builtins.input', return_value=''):
            admin_cli.view_all_logs()
            captured = capsys.readouterr()
            assert "ALL RECENT LOGS" in captured.out

    def test_view_deletion_logs(self, admin_cli, capsys):
        """Test view deletion logs."""
        with patch('builtins.input', return_value=''):
            admin_cli.view_deletion_logs()
            captured = capsys.readouterr()
            assert "DELETION LOGS" in captured.out

    def test_view_logs_by_user(self, admin_cli, capsys):
        """Test view logs by user."""
        with patch('builtins.input', side_effect=['admin', '']):
            admin_cli.view_logs_by_user()
            captured = capsys.readouterr()
            assert "LOGS BY USER" in captured.out


class TestCLIMenus:
    """Test CLI menu navigation."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.sqlite')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def cli_with_db(self, temp_db):
        """Create CLI with temporary database."""
        cli = CLI()
        cli.storage = StorageManager(temp_db)
        from src.auth import AuthManager
        cli.auth = AuthManager(cli.storage)
        return cli

    def test_product_menu_navigation(self, cli_with_db, capsys):
        """Test product menu navigation."""
        with patch('builtins.input', side_effect=['0']):  # Exit
            cli_with_db.product_menu()
            captured = capsys.readouterr()
            assert "PRODUCT MANAGEMENT" in captured.out

    def test_supplier_menu_navigation(self, cli_with_db, capsys):
        """Test supplier menu navigation."""
        with patch('builtins.input', side_effect=['0']):  # Exit
            cli_with_db.supplier_menu()
            captured = capsys.readouterr()
            assert "SUPPLIER MANAGEMENT" in captured.out

    def test_order_menu_navigation(self, cli_with_db, capsys):
        """Test order menu navigation."""
        with patch('builtins.input', side_effect=['0']):  # Exit
            cli_with_db.order_menu()
            captured = capsys.readouterr()
            assert "ORDER PROCESSING" in captured.out

    def test_reports_menu_navigation(self, cli_with_db, capsys):
        """Test reports menu navigation."""
        with patch('builtins.input', side_effect=['0']):  # Exit
            cli_with_db.reports_menu()
            captured = capsys.readouterr()
            assert "REPORTS & ANALYTICS" in captured.out

    def test_input_number_valid_int(self, cli_with_db):
        """Test input_number with valid integer."""
        with patch('builtins.input', return_value='42'):
            result = cli_with_db.input_number("Enter number", allow_float=False)
            assert result == 42

    def test_input_number_valid_float(self, cli_with_db):
        """Test input_number with valid float."""
        with patch('builtins.input', return_value='42.5'):
            result = cli_with_db.input_number("Enter number", allow_float=True)
            assert result == 42.5

    def test_input_number_invalid_then_valid(self, cli_with_db, capsys):
        """Test input_number with invalid then valid input."""
        with patch('builtins.input', side_effect=['abc', '42']):
            result = cli_with_db.input_number("Enter number", allow_float=False)
            assert result == 42
            captured = capsys.readouterr()
            assert "valid number" in captured.out

    def test_input_with_prompt_required(self, cli_with_db, capsys):
        """Test input_with_prompt when required."""
        with patch('builtins.input', side_effect=['', 'valid']):
            result = cli_with_db.input_with_prompt("Enter value", required=True)
            assert result == "valid"
            captured = capsys.readouterr()
            assert "required" in captured.out

    def test_input_with_prompt_not_required(self, cli_with_db):
        """Test input_with_prompt when not required."""
        with patch('builtins.input', return_value=''):
            result = cli_with_db.input_with_prompt("Enter value", required=False)
            assert result == ""

    def test_clear_screen(self, cli_with_db, capsys):
        """Test clear_screen method."""
        cli_with_db.clear_screen()
        # Just verify it doesn't crash

    def test_print_header(self, cli_with_db, capsys):
        """Test print_header method."""
        cli_with_db.print_header("TEST HEADER")
        captured = capsys.readouterr()
        assert "TEST HEADER" in captured.out
        assert "=" in captured.out

    def test_show_main_menu_authenticated_admin(self, cli_with_db, capsys):
        """Test main menu display for authenticated admin."""
        cli_with_db.auth.login('admin', 'admin123')
        cli_with_db.show_main_menu()
        captured = capsys.readouterr()
        assert "Logged in as: admin (Admin)" in captured.out
        assert "Product Management" in captured.out

    def test_show_main_menu_not_authenticated(self, cli_with_db, capsys):
        """Test main menu display for non-authenticated user."""
        cli_with_db.show_main_menu()
        captured = capsys.readouterr()
        assert "Not logged in" in captured.out or "Guest mode" in captured.out

    def test_confirm_deletion_yes(self, cli_with_db):
        """Test confirm_deletion with yes."""
        with patch('builtins.input', side_effect=['yes', 'DELETE']):
            result = cli_with_db.confirm_deletion("Product", "Test Product")
            assert result is True

    def test_confirm_deletion_no(self, cli_with_db):
        """Test confirm_deletion with no."""
        with patch('builtins.input', return_value='no'):
            result = cli_with_db.confirm_deletion("Product", "Test Product")
            assert result is False

    def test_confirm_deletion_invalid_then_yes(self, cli_with_db, capsys):
        """Test confirm_deletion with invalid confirmation word."""
        with patch('builtins.input', side_effect=['yes', 'delete']):  # lowercase won't work
            result = cli_with_db.confirm_deletion("Product", "Test Product")
            assert result is False  # Should fail because it needs 'DELETE' not 'delete'
            captured = capsys.readouterr()
            assert "Incorrect confirmation" in captured.out
