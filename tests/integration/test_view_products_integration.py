"""
Integration tests for viewing products with stock levels.
Tests INV-F-002 (View all products).
"""

import pytest
import tempfile
import os
from src.product_manager import ProductManager
from src.storage import StorageManager
from src.logger import LogManager


class TestViewProductsIntegration:
    """Integration tests for viewing products."""

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

    def test_view_all_products_workflow(self, product_manager):
        """Test complete workflow of adding and viewing products."""
        # Add multiple products
        product_manager.add_product("LAPTOP001", "Gaming Laptop", 1299.99, "Electronics", 15)
        product_manager.add_product("MOUSE001", "Wireless Mouse", 29.99, "Accessories", 100)
        product_manager.add_product("DESK001", "Standing Desk", 499.99, "Furniture", 5)
        
        # Get all products
        products = product_manager.get_all_products()
        
        # Verify all products are retrieved
        assert len(products) == 3
        
        # Verify each product has stock information
        for product in products:
            assert 'stock' in product
            assert product['stock'] >= 0
            assert 'sku' in product
            assert 'name' in product
            assert 'price' in product
            assert 'category' in product

    def test_view_products_shows_stock_levels(self, product_manager):
        """Test that viewing products displays stock levels correctly."""
        # Add products with different stock levels
        product_manager.add_product("LOW001", "Low Stock Item", 10.00, "Test", 2)
        product_manager.add_product("MED001", "Medium Stock Item", 20.00, "Test", 50)
        product_manager.add_product("HIGH001", "High Stock Item", 30.00, "Test", 500)
        
        products = product_manager.get_all_products()
        
        # Create a mapping of SKU to stock
        stock_map = {p['sku']: p['stock'] for p in products}
        
        # Verify stock levels
        assert stock_map['LOW001'] == 2
        assert stock_map['MED001'] == 50
        assert stock_map['HIGH001'] == 500

    def test_display_shows_all_product_fields(self, product_manager, capsys):
        """Test that display shows all relevant product fields."""
        # Add a product with all fields
        product_manager.add_product(
            sku="FULL001",
            name="Complete Product Info",
            price=99.99,
            category="Test Category",
            stock=25,
            description="Full product description"
        )
        
        products = product_manager.get_all_products()
        product_manager.display_products(products)
        
        captured = capsys.readouterr()
        
        # Verify all fields are displayed
        assert "FULL001" in captured.out
        assert "Complete Product Info" in captured.out
        assert "Test Category" in captured.out
        assert "$99.99" in captured.out
        assert "25" in captured.out

    def test_view_products_after_multiple_operations(self, product_manager):
        """Test viewing products after various operations."""
        # Add products
        id1 = product_manager.add_product("PROD001", "Product 1", 10.00, "Cat1", 50)
        id2 = product_manager.add_product("PROD002", "Product 2", 20.00, "Cat2", 30)
        product_manager.add_product("PROD003", "Product 3", 30.00, "Cat3", 40)
        
        # Get all products
        products = product_manager.get_all_products()
        
        # Verify count
        assert len(products) == 3
        
        # Verify all products have required fields
        for product in products:
            assert 'id' in product
            assert 'sku' in product
            assert 'name' in product
            assert 'stock' in product
            assert 'price' in product
            assert 'category' in product

    def test_empty_inventory_display(self, product_manager, capsys):
        """Test displaying products when inventory is empty."""
        products = product_manager.get_all_products()
        product_manager.display_products(products)
        
        captured = capsys.readouterr()
        assert "No products found" in captured.out
