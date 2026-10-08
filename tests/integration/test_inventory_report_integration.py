"""
Integration tests for inventory report generation feature.
Tests the complete workflow of generating inventory reports through the CLI.
User Story: Generate inventory report
As a staff member, I want to generate an inventory report to check stock levels.
"""

import os
import sys
import pytest
from io import StringIO

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.cli import CLI
from src.storage import StorageManager
from src.product_manager import ProductManager


@pytest.fixture
def test_cli(tmp_path, monkeypatch):
    """Create a CLI instance with temporary database."""
    db_path = os.path.join(tmp_path, "test.db")
    
    cli = CLI()
    cli.storage = StorageManager(db_path=db_path)
    cli.product_manager.storage = cli.storage
    cli.logger.storage = cli.storage
    
    # Login as admin for testing
    monkeypatch.setattr(cli.auth, 'is_authenticated', lambda: True)
    monkeypatch.setattr(cli.auth, 'get_current_username', lambda: 'test_admin')
    monkeypatch.setattr(cli.auth, 'is_admin', lambda: True)
    
    return cli


@pytest.fixture
def populated_inventory(test_cli):
    """Populate test inventory with sample products."""
    products = [
        ("LAPTOP001", "Dell Laptop", 1200.00, "Electronics", 25, "Business laptop"),
        ("MOUSE001", "Wireless Mouse", 30.00, "Electronics", 150, "Ergonomic mouse"),
        ("CHAIR001", "Office Chair", 250.00, "Furniture", 2, "Leather chair"),  # Low stock
        ("DESK001", "Standing Desk", 500.00, "Furniture", 0, "Adjustable desk"),  # Out of stock
        ("PEN001", "Blue Pen", 2.50, "Stationery", 500, "Ballpoint pen"),
    ]
    
    for sku, name, price, category, stock, description in products:
        test_cli.product_manager.add_product(
            sku=sku,
            name=name,
            price=price,
            category=category,
            stock=stock,
            description=description,
            user="test_admin"
        )
    
    return test_cli


class TestInventoryReportIntegration:
    """Integration tests for inventory report generation."""

    def test_generate_report_from_cli(self, populated_inventory, capsys, monkeypatch):
        """Test generating report through CLI interface."""
        # Simulate user choosing not to save
        monkeypatch.setattr('builtins.input', lambda _: 'n')
        
        # Generate report
        populated_inventory.generate_inventory_report()
        
        # Capture output
        captured = capsys.readouterr()
        
        # Verify report sections are displayed
        assert "INVENTORY REPORT" in captured.out
        assert "SUMMARY" in captured.out
        assert "Total Products: 5" in captured.out
        assert "Total Stock Units: 677" in captured.out  # 25+150+2+0+500
        assert "Low Stock Items: 2" in captured.out  # Chair and Desk
        assert "CATEGORY BREAKDOWN" in captured.out
        assert "Electronics" in captured.out
        assert "Furniture" in captured.out
        assert "Stationery" in captured.out
        assert "LOW STOCK ALERTS" in captured.out
        assert "DETAILED INVENTORY" in captured.out

    def test_save_report_to_file(self, populated_inventory, tmp_path, monkeypatch, capsys):
        """Test saving inventory report to file."""
        # Create reports directory in tmp_path
        reports_dir = os.path.join(tmp_path, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        # Generate report
        report = populated_inventory.product_manager.generate_inventory_report(user="test_admin")
        
        # Manually set the reports directory for testing
        from src import cli
        original_dirname = os.path.dirname
        
        def mock_dirname(path):
            if 'cli.py' in path:
                return str(tmp_path)
            return original_dirname(path)
        
        monkeypatch.setattr(os.path, 'dirname', mock_dirname)
        
        # Save report
        populated_inventory.save_inventory_report(report)
        
        # Verify file was created - check actual output for path
        captured = capsys.readouterr()
        assert "[OK] Report saved successfully" in captured.out

    def test_report_reflects_real_time_data(self, populated_inventory):
        """Test that report shows current inventory state."""
        # Generate initial report
        report1 = populated_inventory.product_manager.generate_inventory_report(user="test_admin")
        initial_total_stock = report1['total_stock']
        
        # Add a new product
        populated_inventory.product_manager.add_product(
            sku="NEW001",
            name="New Product",
            price=100.00,
            category="Test",
            stock=50,
            user="test_admin"
        )
        
        # Generate new report
        report2 = populated_inventory.product_manager.generate_inventory_report(user="test_admin")
        
        # Verify report reflects the change
        assert report2['total_products'] == report1['total_products'] + 1
        assert report2['total_stock'] == initial_total_stock + 50

    def test_report_with_zero_inventory(self, test_cli, capsys, monkeypatch):
        """Test report generation with no products."""
        monkeypatch.setattr('builtins.input', lambda _: 'n')
        
        test_cli.generate_inventory_report()
        
        captured = capsys.readouterr()
        
        # Should still generate report with zeros
        assert "Total Products: 0" in captured.out
        assert "Total Stock Units: 0" in captured.out
        assert "Total Inventory Value: $0.00" in captured.out

    def test_report_category_totals_accuracy(self, populated_inventory):
        """Test that category totals are calculated correctly."""
        report = populated_inventory.product_manager.generate_inventory_report(user="test_admin")
        
        category_breakdown = report['category_breakdown']
        
        # Verify Electronics
        electronics = category_breakdown['Electronics']
        assert electronics['count'] == 2
        assert electronics['total_stock'] == 175  # 25 + 150
        electronics_value = (1200.00 * 25) + (30.00 * 150)
        assert abs(electronics['total_value'] - electronics_value) < 0.01
        
        # Verify Furniture
        furniture = category_breakdown['Furniture']
        assert furniture['count'] == 2
        assert furniture['total_stock'] == 2  # 2 + 0
        furniture_value = (250.00 * 2) + (500.00 * 0)
        assert abs(furniture['total_value'] - furniture_value) < 0.01
        
        # Verify Stationery
        stationery = category_breakdown['Stationery']
        assert stationery['count'] == 1
        assert stationery['total_stock'] == 500
        assert abs(stationery['total_value'] - (2.50 * 500)) < 0.01

    def test_report_low_stock_identification(self, populated_inventory):
        """Test that low stock items are correctly identified."""
        report = populated_inventory.product_manager.generate_inventory_report(user="test_admin")
        
        low_stock_items = report['low_stock_items']
        low_stock_skus = [item['sku'] for item in low_stock_items]
        
        # Should identify Chair and Desk as low stock
        assert 'CHAIR001' in low_stock_skus
        assert 'DESK001' in low_stock_skus
        
        # Should not identify others as low stock
        assert 'LAPTOP001' not in low_stock_skus
        assert 'MOUSE001' not in low_stock_skus
        assert 'PEN001' not in low_stock_skus

    def test_report_total_value_calculation(self, populated_inventory):
        """Test that total inventory value is calculated correctly."""
        report = populated_inventory.product_manager.generate_inventory_report(user="test_admin")
        
        expected_value = (
            (1200.00 * 25) +  # Laptop
            (30.00 * 150) +   # Mouse
            (250.00 * 2) +    # Chair
            (500.00 * 0) +    # Desk
            (2.50 * 500)      # Pen
        )
        
        assert abs(report['total_inventory_value'] - expected_value) < 0.01

    def test_report_logs_generation(self, populated_inventory):
        """Test that report generation is logged properly."""
        # Generate report
        populated_inventory.product_manager.generate_inventory_report(user="staff_user")
        
        # Check logs
        logs = populated_inventory.logger.get_recent_logs(limit=10)
        
        # Find the report generation log
        report_logs = [log for log in logs if log['action'] == 'GENERATE_INVENTORY_REPORT']
        assert len(report_logs) >= 1
        
        # Verify log content
        latest_log = report_logs[0]
        assert latest_log['user'] == 'staff_user'
        assert 'products' in latest_log['details']
        assert 'low stock items' in latest_log['details']

    def test_multiple_report_generations(self, populated_inventory):
        """Test generating multiple reports in succession."""
        # Generate first report
        report1 = populated_inventory.product_manager.generate_inventory_report(user="user1")
        
        # Generate second report
        report2 = populated_inventory.product_manager.generate_inventory_report(user="user2")
        
        # Both reports should be identical (same inventory state)
        assert report1['total_products'] == report2['total_products']
        assert report1['total_stock'] == report2['total_stock']
        assert report1['total_inventory_value'] == report2['total_inventory_value']
        
        # Check that both generations were logged
        logs = populated_inventory.logger.get_recent_logs(limit=10)
        report_logs = [log for log in logs if log['action'] == 'GENERATE_INVENTORY_REPORT']
        assert len(report_logs) >= 2

    def test_report_after_stock_updates(self, populated_inventory):
        """Test that report reflects stock updates."""
        # Get initial report
        report1 = populated_inventory.product_manager.generate_inventory_report(user="test_admin")
        
        # Update stock for a product
        product = populated_inventory.storage.get_product_by_sku("LAPTOP001")
        populated_inventory.product_manager.update_product(
            product['id'],
            stock=50,  # Increase from 25 to 50
            user="test_admin"
        )
        
        # Generate new report
        report2 = populated_inventory.product_manager.generate_inventory_report(user="test_admin")
        
        # Total stock should increase by 25
        assert report2['total_stock'] == report1['total_stock'] + 25
        
        # Total value should also increase
        value_increase = 1200.00 * 25
        assert abs(report2['total_inventory_value'] - report1['total_inventory_value'] - value_increase) < 0.01

    def test_reports_menu_navigation(self, populated_inventory, monkeypatch):
        """Test navigating to reports menu and selecting inventory report."""
        inputs = iter(['1', 'n', '0'])  # Select option 1, don't save, go back
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))
        
        # Call reports menu
        try:
            populated_inventory.reports_menu()
        except StopIteration:
            # This is expected when input runs out
            pass

    def test_report_display_formatting(self, populated_inventory, capsys, monkeypatch):
        """Test that report is displayed with proper formatting."""
        monkeypatch.setattr('builtins.input', lambda _: 'n')
        
        populated_inventory.generate_inventory_report()
        
        captured = capsys.readouterr()
        
        # Check for proper formatting elements
        assert "=" in captured.out  # Headers with separators
        assert "LAPTOP001" in captured.out  # Product SKUs
        assert "Dell Laptop" in captured.out  # Product names
        assert "$" in captured.out  # Price formatting
        assert "Electronics" in captured.out  # Categories
        assert "CRITICAL" in captured.out or "LOW" in captured.out  # Stock status


class TestInventoryReportEdgeCases:
    """Test edge cases for inventory report generation."""

    def test_report_with_very_large_inventory(self, test_cli):
        """Test report with many products."""
        # Add 100 products
        for i in range(100):
            test_cli.product_manager.add_product(
                sku=f"PROD{i:03d}",
                name=f"Product {i}",
                price=10.00 + i,
                category=f"Category{i % 5}",
                stock=i * 2,
                user="test_admin"
            )
        
        # Generate report
        report = test_cli.product_manager.generate_inventory_report(user="test_admin")
        
        # Verify all products are included
        assert report['total_products'] == 100
        assert len(report['all_products']) == 100
        assert len(report['category_breakdown']) == 5

    def test_report_with_special_characters(self, test_cli):
        """Test report with products containing special characters."""
        test_cli.product_manager.add_product(
            sku="SPEC-001",
            name="Product & Test's \"Quote\"",
            price=50.00,
            category="Special/Category",
            stock=10,
            description="Test's description with \"quotes\" & symbols",
            user="test_admin"
        )
        
        report = test_cli.product_manager.generate_inventory_report(user="test_admin")
        
        # Should handle special characters without errors
        assert report['total_products'] == 1
        product = report['all_products'][0]
        assert "&" in product['name'] or "Test" in product['name']

    def test_report_with_very_high_prices(self, test_cli):
        """Test report with very expensive products."""
        test_cli.product_manager.add_product(
            sku="EXPENSIVE",
            name="Expensive Item",
            price=999999.99,
            category="Luxury",
            stock=10,
            user="test_admin"
        )
        
        report = test_cli.product_manager.generate_inventory_report(user="test_admin")
        
        expected_value = 999999.99 * 10
        assert abs(report['total_inventory_value'] - expected_value) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
