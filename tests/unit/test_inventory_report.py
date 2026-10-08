"""
Unit tests for inventory report generation functionality.
Tests User Story: Generate inventory report
As a staff member, I want to generate an inventory report to check stock levels.
"""

import os
import sys
import pytest
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.product_manager import ProductManager
from src.storage import StorageManager
from src.logger import LogManager


@pytest.fixture
def test_storage(tmp_path):
    """Create a temporary storage manager for testing."""
    db_path = os.path.join(tmp_path, "test.db")
    storage = StorageManager(db_path=db_path)
    return storage


@pytest.fixture
def test_logger(test_storage):
    """Create a logger for testing."""
    return LogManager(test_storage)


@pytest.fixture
def product_manager(test_storage, test_logger):
    """Create a product manager for testing."""
    return ProductManager(test_storage, test_logger)


@pytest.fixture
def sample_products(product_manager):
    """Create sample products for testing."""
    products = []
    
    # Add products from different categories with varying stock levels
    product_data = [
        ("SKU001", "Laptop", 999.99, "Electronics", 50, "High-end laptop"),
        ("SKU002", "Mouse", 25.99, "Electronics", 100, "Wireless mouse"),
        ("SKU003", "Keyboard", 49.99, "Electronics", 3, "Mechanical keyboard"),  # Low stock
        ("SKU004", "Monitor", 299.99, "Electronics", 0, "27-inch monitor"),  # Out of stock
        ("SKU005", "Desk Chair", 199.99, "Furniture", 25, "Ergonomic chair"),
        ("SKU006", "Desk", 349.99, "Furniture", 15, "Standing desk"),
        ("SKU007", "Notebook", 5.99, "Stationery", 200, "Spiral notebook"),
        ("SKU008", "Pen", 1.99, "Stationery", 2, "Ballpoint pen"),  # Low stock
    ]
    
    for sku, name, price, category, stock, description in product_data:
        product_id = product_manager.add_product(
            sku=sku,
            name=name,
            price=price,
            category=category,
            stock=stock,
            description=description,
            user="test_user"
        )
        products.append(product_id)
    
    return products


class TestInventoryReportGeneration:
    """Test inventory report generation functionality."""

    def test_generate_inventory_report_basic(self, product_manager, sample_products):
        """Test basic inventory report generation."""
        report = product_manager.generate_inventory_report(user="test_user")
        
        # Verify report structure
        assert 'total_products' in report
        assert 'total_stock' in report
        assert 'total_inventory_value' in report
        assert 'low_stock_count' in report
        assert 'low_stock_items' in report
        assert 'category_breakdown' in report
        assert 'all_products' in report

    def test_inventory_report_totals(self, product_manager, sample_products):
        """Test that report calculates correct totals."""
        report = product_manager.generate_inventory_report(user="test_user")
        
        # Should have 8 products
        assert report['total_products'] == 8
        
        # Total stock: 50+100+3+0+25+15+200+2 = 395
        assert report['total_stock'] == 395
        
        # Total value calculation
        expected_value = (
            999.99 * 50 +  # Laptop
            25.99 * 100 +  # Mouse
            49.99 * 3 +    # Keyboard
            299.99 * 0 +   # Monitor
            199.99 * 25 +  # Desk Chair
            349.99 * 15 +  # Desk
            5.99 * 200 +   # Notebook
            1.99 * 2       # Pen
        )
        assert abs(report['total_inventory_value'] - expected_value) < 0.01

    def test_inventory_report_low_stock_detection(self, product_manager, sample_products):
        """Test that report correctly identifies low stock items."""
        report = product_manager.generate_inventory_report(user="test_user")
        
        # Should have 3 low stock items (stock <= 5): Keyboard(3), Monitor(0), Pen(2)
        assert report['low_stock_count'] == 3
        assert len(report['low_stock_items']) == 3
        
        # Verify low stock items
        low_stock_skus = [item['sku'] for item in report['low_stock_items']]
        assert 'SKU003' in low_stock_skus  # Keyboard
        assert 'SKU004' in low_stock_skus  # Monitor
        assert 'SKU008' in low_stock_skus  # Pen

    def test_inventory_report_category_breakdown(self, product_manager, sample_products):
        """Test category breakdown in report."""
        report = product_manager.generate_inventory_report(user="test_user")
        
        category_breakdown = report['category_breakdown']
        
        # Should have 3 categories
        assert len(category_breakdown) == 3
        assert 'Electronics' in category_breakdown
        assert 'Furniture' in category_breakdown
        assert 'Stationery' in category_breakdown
        
        # Verify Electronics category
        electronics = category_breakdown['Electronics']
        assert electronics['count'] == 4  # 4 electronic products
        assert electronics['total_stock'] == 153  # 50+100+3+0
        
        # Verify Furniture category
        furniture = category_breakdown['Furniture']
        assert furniture['count'] == 2
        assert furniture['total_stock'] == 40  # 25+15
        
        # Verify Stationery category
        stationery = category_breakdown['Stationery']
        assert stationery['count'] == 2
        assert stationery['total_stock'] == 202  # 200+2

    def test_inventory_report_empty_inventory(self, product_manager):
        """Test report generation with empty inventory."""
        report = product_manager.generate_inventory_report(user="test_user")
        
        assert report['total_products'] == 0
        assert report['total_stock'] == 0
        assert report['total_inventory_value'] == 0
        assert report['low_stock_count'] == 0
        assert len(report['low_stock_items']) == 0
        assert len(report['category_breakdown']) == 0
        assert len(report['all_products']) == 0

    def test_inventory_report_single_product(self, product_manager):
        """Test report with single product."""
        product_manager.add_product(
            sku="TEST001",
            name="Test Product",
            price=100.00,
            category="Test",
            stock=10,
            user="test_user"
        )
        
        report = product_manager.generate_inventory_report(user="test_user")
        
        assert report['total_products'] == 1
        assert report['total_stock'] == 10
        assert report['total_inventory_value'] == 1000.00
        assert len(report['category_breakdown']) == 1
        assert 'Test' in report['category_breakdown']

    def test_inventory_report_logs_action(self, product_manager, test_logger, sample_products):
        """Test that report generation is logged."""
        product_manager.generate_inventory_report(user="staff_member")
        
        # Get recent logs
        logs = product_manager.logger.get_recent_logs(limit=5)
        
        # Should have a log entry for report generation
        report_logs = [log for log in logs if log['action'] == 'GENERATE_INVENTORY_REPORT']
        assert len(report_logs) >= 1
        
        # Verify log details
        latest_log = report_logs[0]
        assert latest_log['user'] == 'staff_member'
        assert '8 products' in latest_log['details']
        assert 'low stock items' in latest_log['details']

    def test_display_inventory_report(self, product_manager, sample_products, capsys):
        """Test that report display function works correctly."""
        report = product_manager.generate_inventory_report(user="test_user")
        
        # Display the report
        product_manager.display_inventory_report(report)
        
        # Capture output
        captured = capsys.readouterr()
        
        # Verify output contains key sections
        assert "INVENTORY REPORT" in captured.out
        assert "SUMMARY" in captured.out
        assert "CATEGORY BREAKDOWN" in captured.out
        assert "LOW STOCK ALERTS" in captured.out
        assert "DETAILED INVENTORY" in captured.out
        
        # Verify summary values in output
        assert "Total Products: 8" in captured.out
        assert "Total Stock Units: 395" in captured.out
        assert "Low Stock Items: 3" in captured.out

    def test_inventory_report_category_value_calculation(self, product_manager, sample_products):
        """Test that category breakdown includes correct value calculations."""
        report = product_manager.generate_inventory_report(user="test_user")
        
        category_breakdown = report['category_breakdown']
        
        # Verify Electronics category value
        electronics_value = category_breakdown['Electronics']['total_value']
        expected_electronics = (999.99 * 50) + (25.99 * 100) + (49.99 * 3) + (299.99 * 0)
        assert abs(electronics_value - expected_electronics) < 0.01
        
        # Verify Furniture category value
        furniture_value = category_breakdown['Furniture']['total_value']
        expected_furniture = (199.99 * 25) + (349.99 * 15)
        assert abs(furniture_value - expected_furniture) < 0.01
        
        # Verify Stationery category value
        stationery_value = category_breakdown['Stationery']['total_value']
        expected_stationery = (5.99 * 200) + (1.99 * 2)
        assert abs(stationery_value - expected_stationery) < 0.01

    def test_inventory_report_all_products_included(self, product_manager, sample_products):
        """Test that all products are included in the report."""
        report = product_manager.generate_inventory_report(user="test_user")
        
        all_products = report['all_products']
        assert len(all_products) == 8
        
        # Verify all SKUs are present
        skus = [p['sku'] for p in all_products]
        for i in range(1, 9):
            assert f"SKU00{i}" in skus

    def test_inventory_report_zero_price_products(self, product_manager):
        """Test report with zero-price products."""
        product_manager.add_product(
            sku="FREE001",
            name="Free Sample",
            price=0.00,
            category="Promotional",
            stock=100,
            user="test_user"
        )
        
        report = product_manager.generate_inventory_report(user="test_user")
        
        assert report['total_products'] == 1
        assert report['total_stock'] == 100
        assert report['total_inventory_value'] == 0.00

    def test_inventory_report_high_value_accuracy(self, product_manager):
        """Test report with high-value products for calculation accuracy."""
        product_manager.add_product(
            sku="EXPENSIVE",
            name="Expensive Item",
            price=99999.99,
            category="Luxury",
            stock=100,
            user="test_user"
        )
        
        report = product_manager.generate_inventory_report(user="test_user")
        
        expected_value = 99999.99 * 100
        assert abs(report['total_inventory_value'] - expected_value) < 0.01


class TestInventoryReportIntegration:
    """Integration tests for inventory report with other system components."""

    def test_report_after_stock_adjustment(self, product_manager):
        """Test report reflects stock adjustments."""
        # Add initial product
        product_id = product_manager.add_product(
            sku="ADJ001",
            name="Adjustable Product",
            price=50.00,
            category="Test",
            stock=10,
            user="test_user"
        )
        
        # Generate initial report
        report1 = product_manager.generate_inventory_report(user="test_user")
        assert report1['total_stock'] == 10
        
        # Adjust stock
        product_manager.adjust_stock(product_id, 15, user="test_user")
        
        # Generate new report
        report2 = product_manager.generate_inventory_report(user="test_user")
        assert report2['total_stock'] == 25
        assert report2['total_inventory_value'] == 1250.00

    def test_report_after_product_deletion(self, product_manager):
        """Test report after product deletion."""
        # Add products
        id1 = product_manager.add_product("DEL001", "Product 1", 10.00, "Test", 5, "", "test_user")
        id2 = product_manager.add_product("DEL002", "Product 2", 20.00, "Test", 10, "", "test_user")
        
        # Initial report
        report1 = product_manager.generate_inventory_report(user="test_user")
        assert report1['total_products'] == 2
        
        # Delete one product
        product_manager.delete_product(id1, user="test_user")
        
        # New report
        report2 = product_manager.generate_inventory_report(user="test_user")
        assert report2['total_products'] == 1
        assert report2['total_stock'] == 10
        assert report2['total_inventory_value'] == 200.00

    def test_report_with_multiple_users(self, product_manager):
        """Test report generation by different users."""
        # Add product
        product_manager.add_product("MULTI001", "Product", 10.00, "Test", 5, "", "user1")
        
        # Generate reports by different users
        report1 = product_manager.generate_inventory_report(user="user1")
        report2 = product_manager.generate_inventory_report(user="user2")
        
        # Both should see same inventory
        assert report1['total_products'] == report2['total_products']
        assert report1['total_stock'] == report2['total_stock']
        assert report1['total_inventory_value'] == report2['total_inventory_value']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
