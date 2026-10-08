"""
Unit tests for product_manager module.
Tests INV-F-001 (Add product with details).
"""

import pytest
import tempfile
import os
from src.product_manager import ProductManager
from src.storage import StorageManager
from src.logger import LogManager


class TestProductManager:
    """Test product manager - Add product functionality."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.sqlite')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def product_manager(self, temp_db):
        """Create product manager with temporary database."""
        storage = StorageManager(temp_db)
        logger = LogManager(storage)
        return ProductManager(storage, logger)

    def test_add_product_success(self, product_manager):
        """Test adding product successfully (INV-F-001)."""
        product_id = product_manager.add_product(
            sku="LAPTOP001",
            name="Gaming Laptop",
            price=1299.99,
            category="Electronics",
            stock=15,
            description="High-performance gaming laptop"
        )
        
        assert product_id is not None
        assert product_id > 0

    def test_add_product_duplicate_sku(self, product_manager):
        """Test adding product with duplicate SKU fails."""
        product_manager.add_product("LAPTOP001", "Laptop 1", 999.99, "Electronics", 10)
        
        # Try to add with same SKU
        result = product_manager.add_product("LAPTOP001", "Laptop 2", 899.99, "Electronics", 5)
        
        assert result is None

    def test_add_product_negative_price(self, product_manager):
        """Test adding product with negative price raises error."""
        with pytest.raises(ValueError):
            product_manager.add_product("TEST001", "Test", -10.00, "Cat", 10)

    def test_add_product_negative_stock(self, product_manager):
        """Test adding product with negative stock raises error."""
        with pytest.raises(ValueError):
            product_manager.add_product("TEST001", "Test", 10.00, "Cat", -5)

    def test_get_all_products(self, product_manager):
        """Test getting all products (INV-F-002)."""
        product_manager.add_product("PROD001", "Product 1", 10.00, "Cat1", 50)
        product_manager.add_product("PROD002", "Product 2", 20.00, "Cat2", 30)
        
        products = product_manager.get_all_products()
        
        assert len(products) >= 2

    def test_get_product(self, product_manager):
        """Test getting single product by ID."""
        product_id = product_manager.add_product("PROD001", "Product 1", 10.00, "Cat1", 50)
        
        product = product_manager.get_product(product_id)
        
        assert product is not None
        assert product['sku'] == "PROD001"
        assert product['name'] == "Product 1"

    def test_search_products(self, product_manager):
        """Test searching products (INV-F-002)."""
        product_manager.add_product("LAPTOP001", "Gaming Laptop", 1299.99, "Electronics", 10)
        product_manager.add_product("LAPTOP002", "Business Laptop", 999.99, "Electronics", 15)
        product_manager.add_product("CHAIR001", "Office Chair", 199.99, "Furniture", 20)
        
        # Search by keyword
        results = product_manager.search_products("Laptop")
        assert len(results) == 2
        
        # Search by category
        results = product_manager.search_products("Electronics")
        assert len(results) == 2

    def test_update_product_success(self, product_manager):
        """Test updating product (INV-F-003)."""
        product_id = product_manager.add_product("PROD001", "Old Name", 10.00, "Cat1", 50)
        
        success = product_manager.update_product(
            product_id,
            name="New Name",
            price=15.00,
            stock=60
        )
        
        assert success is True
        
        product = product_manager.get_product(product_id)
        assert product['name'] == "New Name"
        assert product['price'] == 15.00
        assert product['stock'] == 60

    def test_update_product_not_found(self, product_manager):
        """Test updating non-existent product fails."""
        success = product_manager.update_product(99999, name="Test")
        
        assert success is False

    def test_update_product_negative_price(self, product_manager):
        """Test updating product with negative price raises error."""
        product_id = product_manager.add_product("PROD001", "Product", 10.00, "Cat", 50)
        
        with pytest.raises(ValueError):
            product_manager.update_product(product_id, price=-5.00)

    def test_add_product_logs_action(self, product_manager):
        """Test that adding product creates a log entry."""
        product_manager.add_product(
            sku="PROD001",
            name="Test Product",
            price=99.99,
            category="Test",
            stock=10,
            user="testuser"
        )
        
        logs = product_manager.logger.get_recent_logs(limit=5)
        
        # Check that at least one log entry exists
        assert len(logs) > 0
        
        # Check that the most recent log is for ADD_PRODUCT
        latest_log = logs[0]
        assert latest_log['action'] == "ADD_PRODUCT"
        assert latest_log['user'] == "testuser"
        assert "PROD001" in latest_log['details']

    def test_add_product_with_minimal_info(self, product_manager):
        """Test adding product with only required fields."""
        product_id = product_manager.add_product(
            sku="MIN001",
            name="Minimal Product",
            price=50.00,
            category="General",
            stock=5
        )
        
        assert product_id is not None
        
        product = product_manager.get_product(product_id)
        assert product['sku'] == "MIN001"
        assert product['name'] == "Minimal Product"
        assert product['price'] == 50.00
        assert product['stock'] == 5

    def test_display_products_with_data(self, product_manager, capsys):
        """Test displaying products shows formatted table."""
        # Add some products
        product_manager.add_product("PROD001", "Product 1", 10.00, "Cat1", 50, "Desc 1")
        product_manager.add_product("PROD002", "Product 2", 20.00, "Cat2", 30, "Desc 2")
        
        # Get all products
        products = product_manager.get_all_products()
        
        # Display them
        product_manager.display_products(products)
        
        # Capture output
        captured = capsys.readouterr()
        
        # Verify output contains product data
        assert "PROD001" in captured.out
        assert "Product 1" in captured.out
        assert "PROD002" in captured.out
        assert "Product 2" in captured.out

    def test_display_products_empty(self, product_manager, capsys):
        """Test displaying empty product list shows appropriate message."""
        products = []
        
        product_manager.display_products(products)
        
        captured = capsys.readouterr()
        assert "No products found" in captured.out

    # ========== Stock Adjustment Tests (INV-F-004) ==========

    def test_check_stock_availability_sufficient(self, product_manager):
        """Test checking stock availability when sufficient."""
        product_id = product_manager.add_product("PROD001", "Product", 10.00, "Cat", 50)
        
        available = product_manager.check_stock_availability(product_id, 30)
        
        assert available is True

    def test_check_stock_availability_insufficient(self, product_manager):
        """Test checking stock availability when insufficient."""
        product_id = product_manager.add_product("PROD001", "Product", 10.00, "Cat", 10)
        
        available = product_manager.check_stock_availability(product_id, 20)
        
        assert available is False

    def test_check_stock_availability_exact(self, product_manager):
        """Test checking stock availability when exact match."""
        product_id = product_manager.add_product("PROD001", "Product", 10.00, "Cat", 50)
        
        available = product_manager.check_stock_availability(product_id, 50)
        
        assert available is True

    def test_check_stock_availability_not_found(self, product_manager):
        """Test checking stock for non-existent product."""
        available = product_manager.check_stock_availability(99999, 10)
        
        assert available is False

    def test_adjust_stock_increase(self, product_manager):
        """Test increasing stock quantity."""
        product_id = product_manager.add_product("PROD001", "Product", 10.00, "Cat", 50)
        
        success = product_manager.adjust_stock(product_id, 20)
        
        assert success is True
        
        product = product_manager.get_product(product_id)
        assert product['stock'] == 70

    def test_adjust_stock_decrease(self, product_manager):
        """Test decreasing stock quantity."""
        product_id = product_manager.add_product("PROD001", "Product", 10.00, "Cat", 50)
        
        success = product_manager.adjust_stock(product_id, -10)
        
        assert success is True
        
        product = product_manager.get_product(product_id)
        assert product['stock'] == 40

    def test_adjust_stock_insufficient(self, product_manager):
        """Test adjusting stock below zero raises error."""
        product_id = product_manager.add_product("PROD001", "Product", 10.00, "Cat", 10)
        
        with pytest.raises(ValueError):
            product_manager.adjust_stock(product_id, -20)

    def test_adjust_stock_not_found(self, product_manager):
        """Test adjusting stock for non-existent product."""
        success = product_manager.adjust_stock(99999, 10)
        
        assert success is False

    def test_adjust_stock_logs_action(self, product_manager):
        """Test that stock adjustment is logged."""
        product_id = product_manager.add_product("STOCK001", "Stock Test", 10.00, "Test", 50)
        
        product_manager.adjust_stock(product_id, 25, user="staff")
        
        logs = product_manager.logger.get_recent_logs(limit=5)
        
        # Check that the log entry exists for stock update
        assert len(logs) > 0
        latest_log = logs[0]
        assert latest_log['action'] == "UPDATE_PRODUCT"
        assert latest_log['user'] == "staff"
        assert "stock=75" in latest_log['details']

    # ========== Deletion Logging Tests ==========

    def test_delete_product_success(self, product_manager):
        """Test deleting product successfully."""
        product_id = product_manager.add_product("PROD001", "Product", 10.00, "Cat", 50)
        
        success = product_manager.delete_product(product_id, user="admin")
        
        assert success is True
        
        # Verify product is deleted
        product = product_manager.get_product(product_id)
        assert product is None

    def test_delete_product_not_found(self, product_manager):
        """Test deleting non-existent product fails."""
        success = product_manager.delete_product(99999, user="admin")
        
        assert success is False

    def test_delete_product_logs_action(self, product_manager):
        """Test that deleting product creates a log entry with details."""
        product_id = product_manager.add_product(
            sku="DEL001",
            name="Product To Delete",
            price=99.99,
            category="Test",
            stock=10
        )
        
        # Delete the product
        success = product_manager.delete_product(product_id, user="admin")
        assert success is True
        
        # Get deletion logs
        deletion_logs = product_manager.logger.get_deletion_logs(limit=10)
        
        # Verify deletion was logged
        assert len(deletion_logs) > 0
        
        # Check the most recent deletion log
        latest_log = deletion_logs[0]
        assert latest_log['action'] == "DELETE_PRODUCT"
        assert latest_log['user'] == "admin"
        assert "Product To Delete" in latest_log['details']
        assert "DEL001" in latest_log['details']
        assert str(product_id) in latest_log['details']

    def test_delete_product_logs_include_timestamp(self, product_manager):
        """Test that deletion logs include timestamp."""
        product_id = product_manager.add_product("TEST001", "Test Product", 50.00, "Test", 5)
        
        product_manager.delete_product(product_id, user="admin")
        
        logs = product_manager.logger.get_deletion_logs(limit=1)
        
        assert len(logs) > 0
        assert 'timestamp' in logs[0]
        assert logs[0]['timestamp'] is not None

    def test_multiple_deletions_logged_separately(self, product_manager):
        """Test that multiple deletions are logged as separate entries."""
        # Add and delete multiple products
        prod1 = product_manager.add_product("PROD001", "Product 1", 10.00, "Cat", 5)
        prod2 = product_manager.add_product("PROD002", "Product 2", 20.00, "Cat", 10)
        prod3 = product_manager.add_product("PROD003", "Product 3", 30.00, "Cat", 15)
        
        product_manager.delete_product(prod1, user="admin")
        product_manager.delete_product(prod2, user="manager")
        product_manager.delete_product(prod3, user="admin")
        
        # Get deletion logs
        deletion_logs = product_manager.logger.get_deletion_logs(limit=10)
        
        # Should have at least 3 deletion logs
        assert len(deletion_logs) >= 3
        
        # Verify all products are in the logs
        log_details = [log['details'] for log in deletion_logs]
        combined_details = " ".join(log_details)
        assert "PROD001" in combined_details
        assert "PROD002" in combined_details
        assert "PROD003" in combined_details

    def test_deletion_log_shows_who_deleted(self, product_manager):
        """Test that deletion logs clearly show who deleted the product."""
        product_id = product_manager.add_product("TEST001", "Test", 10.00, "Cat", 5)
        
        product_manager.delete_product(product_id, user="john_admin")
        
        logs = product_manager.logger.get_deletion_logs(limit=5)
        
        # Find the deletion log
        deletion_log = None
        for log in logs:
            if "TEST001" in log['details']:
                deletion_log = log
                break
        
        assert deletion_log is not None
        assert deletion_log['user'] == "john_admin"

    # ========== Additional Coverage Tests ==========

    def test_get_product_confirmation_success(self, product_manager):
        """Test getting confirmation details for newly added product."""
        product_id = product_manager.add_product(
            sku="CONF001",
            name="Confirmation Test",
            price=99.99,
            category="Test",
            stock=10,
            description="Test description"
        )
        
        confirmation = product_manager.get_product_confirmation(product_id)
        
        assert confirmation['success'] is True
        assert "Confirmation Test" in confirmation['message']
        assert confirmation['product'] is not None
        assert confirmation['product']['sku'] == "CONF001"

    def test_get_product_confirmation_not_found(self, product_manager):
        """Test confirmation for non-existent product."""
        confirmation = product_manager.get_product_confirmation(99999)
        
        assert confirmation['success'] is False
        assert 'not found' in confirmation['message'].lower()
        assert confirmation['product'] is None

    def test_add_product_with_confirmation_success(self, product_manager):
        """Test adding product with confirmation."""
        result = product_manager.add_product_with_confirmation(
            sku="NEW001",
            name="New Product",
            price=50.00,
            category="Test",
            stock=20,
            description="Test desc",
            user="testuser"
        )
        
        assert result['success'] is True
        assert "New Product" in result['message']
        assert result['product'] is not None
        assert result['product']['sku'] == "NEW001"

    def test_add_product_with_confirmation_duplicate(self, product_manager):
        """Test adding product with duplicate SKU returns failure."""
        product_manager.add_product("DUP001", "Product 1", 10.00, "Cat", 5)
        
        result = product_manager.add_product_with_confirmation(
            sku="DUP001",
            name="Product 2",
            price=20.00,
            category="Cat",
            stock=10,
            user="testuser"
        )
        
        assert result['success'] is False
        assert "already exists" in result['message']
        assert result['product'] is None

    def test_add_product_with_confirmation_negative_price(self, product_manager):
        """Test adding product with negative price via confirmation."""
        result = product_manager.add_product_with_confirmation(
            sku="NEG001",
            name="Negative Price",
            price=-10.00,
            category="Cat",
            stock=5,
            user="testuser"
        )
        
        assert result['success'] is False
        assert "negative" in result['message'].lower()

    def test_add_product_with_confirmation_negative_stock(self, product_manager):
        """Test adding product with negative stock via confirmation."""
        result = product_manager.add_product_with_confirmation(
            sku="NEG002",
            name="Negative Stock",
            price=10.00,
            category="Cat",
            stock=-5,
            user="testuser"
        )
        
        assert result['success'] is False
        assert "negative" in result['message'].lower()

    def test_get_all_products(self, product_manager):
        """Test getting all products."""
        product_manager.add_product("P001", "Product 1", 10.00, "Cat1", 5)
        product_manager.add_product("P002", "Product 2", 20.00, "Cat2", 10)
        
        products = product_manager.get_all_products()
        
        assert len(products) >= 2
        skus = [p['sku'] for p in products]
        assert "P001" in skus
        assert "P002" in skus

    def test_get_product_by_id(self, product_manager):
        """Test getting single product by ID."""
        product_id = product_manager.add_product("GET001", "Get Test", 15.00, "Cat", 8)
        
        product = product_manager.get_product(product_id)
        
        assert product is not None
        assert product['id'] == product_id
        assert product['sku'] == "GET001"
        assert product['name'] == "Get Test"

    def test_get_product_not_found(self, product_manager):
        """Test getting non-existent product returns None."""
        product = product_manager.get_product(99999)
        
        assert product is None

    def test_search_products_by_name(self, product_manager):
        """Test searching products by name."""
        product_manager.add_product("SEARCH1", "Gaming Laptop", 1000.00, "Electronics", 5)
        product_manager.add_product("SEARCH2", "Gaming Mouse", 50.00, "Electronics", 10)
        product_manager.add_product("SEARCH3", "Office Chair", 200.00, "Furniture", 3)
        
        results = product_manager.search_products("Gaming")
        
        assert len(results) == 2
        names = [p['name'] for p in results]
        assert any("Laptop" in name for name in names)
        assert any("Mouse" in name for name in names)

    def test_search_products_by_sku(self, product_manager):
        """Test searching products by SKU."""
        product_manager.add_product("LAPTOP001", "Gaming Laptop", 1000.00, "Electronics", 5)
        product_manager.add_product("LAPTOP002", "Business Laptop", 800.00, "Electronics", 3)
        
        results = product_manager.search_products("LAPTOP")
        
        assert len(results) == 2

    def test_search_products_by_category(self, product_manager):
        """Test searching products by category."""
        product_manager.add_product("PROD1", "Product 1", 10.00, "Electronics", 5)
        product_manager.add_product("PROD2", "Product 2", 20.00, "Electronics", 3)
        product_manager.add_product("PROD3", "Product 3", 30.00, "Furniture", 2)
        
        results = product_manager.search_products("Electronics")
        
        assert len(results) == 2

    def test_update_product_success(self, product_manager):
        """Test updating product successfully."""
        product_id = product_manager.add_product("UPD001", "Old Name", 10.00, "Cat", 5)
        
        success = product_manager.update_product(
            product_id,
            name="New Name",
            price=15.00,
            stock=10,
            user="admin"
        )
        
        assert success is True
        
        product = product_manager.get_product(product_id)
        assert product['name'] == "New Name"
        assert product['price'] == 15.00
        assert product['stock'] == 10

    def test_update_product_partial_update(self, product_manager):
        """Test partial update of product."""
        product_id = product_manager.add_product("PART001", "Original", 100.00, "Cat", 50)
        
        success = product_manager.update_product(product_id, name="Updated Name", user="admin")
        
        assert success is True
        product = product_manager.get_product(product_id)
        assert product['name'] == "Updated Name"
        assert product['price'] == 100.00  # Unchanged

    def test_update_product_not_found(self, product_manager):
        """Test updating non-existent product."""
        success = product_manager.update_product(99999, name="Test", user="admin")
        
        assert success is False

    def test_update_product_negative_price_raises_error(self, product_manager):
        """Test updating with negative price raises ValueError."""
        product_id = product_manager.add_product("TEST001", "Test", 10.00, "Cat", 5)
        
        with pytest.raises(ValueError, match="negative"):
            product_manager.update_product(product_id, price=-5.00, user="admin")

    def test_update_product_negative_stock_raises_error(self, product_manager):
        """Test updating with negative stock raises ValueError."""
        product_id = product_manager.add_product("TEST001", "Test", 10.00, "Cat", 5)
        
        with pytest.raises(ValueError, match="negative"):
            product_manager.update_product(product_id, stock=-5, user="admin")

    def test_get_low_stock_products_default_threshold(self, product_manager):
        """Test getting low stock products with default threshold."""
        product_manager.add_product("LOW1", "Low Stock 1", 10.00, "Cat", 2)
        product_manager.add_product("LOW2", "Low Stock 2", 20.00, "Cat", 3)
        product_manager.add_product("HIGH1", "High Stock", 30.00, "Cat", 100)
        
        low_stock = product_manager.get_low_stock_products()
        
        assert len(low_stock) >= 2

    def test_get_low_stock_products_custom_threshold(self, product_manager):
        """Test getting low stock with custom threshold."""
        product_manager.add_product("PROD1", "Product 1", 10.00, "Cat", 5)
        product_manager.add_product("PROD2", "Product 2", 20.00, "Cat", 15)
        
        low_stock = product_manager.get_low_stock_products(threshold=10)
        
        assert len(low_stock) >= 1
        assert all(p['stock'] <= 10 for p in low_stock)

    def test_check_stock_availability_sufficient(self, product_manager):
        """Test checking stock availability when sufficient."""
        product_id = product_manager.add_product("STOCK1", "Product", 10.00, "Cat", 50)
        
        available = product_manager.check_stock_availability(product_id, 30)
        
        assert available is True

    def test_check_stock_availability_insufficient(self, product_manager):
        """Test checking stock availability when insufficient."""
        product_id = product_manager.add_product("STOCK2", "Product", 10.00, "Cat", 10)
        
        available = product_manager.check_stock_availability(product_id, 50)
        
        assert available is False

    def test_check_stock_availability_product_not_found(self, product_manager):
        """Test checking stock for non-existent product."""
        available = product_manager.check_stock_availability(99999, 10)
        
        assert available is False

    def test_adjust_stock_increase(self, product_manager):
        """Test adjusting stock by increasing."""
        product_id = product_manager.add_product("ADJ1", "Product", 10.00, "Cat", 50)
        
        success = product_manager.adjust_stock(product_id, 20, user="admin")
        
        assert success is True
        product = product_manager.get_product(product_id)
        assert product['stock'] == 70

    def test_adjust_stock_decrease(self, product_manager):
        """Test adjusting stock by decreasing."""
        product_id = product_manager.add_product("ADJ2", "Product", 10.00, "Cat", 50)
        
        success = product_manager.adjust_stock(product_id, -10, user="admin")
        
        assert success is True
        product = product_manager.get_product(product_id)
        assert product['stock'] == 40

    def test_adjust_stock_insufficient_raises_error(self, product_manager):
        """Test adjusting stock below zero raises error."""
        product_id = product_manager.add_product("ADJ3", "Product", 10.00, "Cat", 10)
        
        with pytest.raises(ValueError, match="Insufficient stock"):
            product_manager.adjust_stock(product_id, -20, user="admin")

    def test_adjust_stock_product_not_found(self, product_manager):
        """Test adjusting stock for non-existent product."""
        success = product_manager.adjust_stock(99999, 10, user="admin")
        
        assert success is False

    def test_display_products_with_data(self, product_manager, capsys):
        """Test displaying products shows formatted output."""
        product_manager.add_product("DISP1", "Display Test 1", 10.00, "Cat1", 5, "Desc 1")
        product_manager.add_product("DISP2", "Display Test 2", 20.00, "Cat2", 10, "Desc 2")
        
        products = product_manager.get_all_products()
        product_manager.display_products(products)
        
        captured = capsys.readouterr()
        assert "DISP1" in captured.out
        assert "Display Test 1" in captured.out
        assert "DISP2" in captured.out

    def test_display_products_empty_list(self, product_manager, capsys):
        """Test displaying empty product list."""
        product_manager.display_products([])
        
        captured = capsys.readouterr()
        assert "No products found" in captured.out
