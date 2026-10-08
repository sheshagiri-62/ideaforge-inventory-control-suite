"""
Integration tests for viewing suppliers.
Tests INV-F-020, INV-F-021.
"""

import pytest
import tempfile
import os
from io import StringIO
import sys
from src.supplier_manager import SupplierManager
from src.storage import StorageManager
from src.logger import LogManager


class TestViewSuppliersIntegration:
    """Integration tests for viewing suppliers."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.sqlite')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def supplier_manager(self, temp_db):
        """Create supplier manager with temporary database."""
        storage = StorageManager(temp_db)
        logger = LogManager(storage)
        return SupplierManager(storage, logger)

    def test_view_all_suppliers_workflow(self, supplier_manager):
        """Test complete workflow of adding and viewing suppliers."""
        # Add multiple suppliers
        supplier_manager.add_supplier(
            "ABC Suppliers", 
            "John Smith", 
            "john@abc.com", 
            "555-1234", 
            "123 Main St"
        )
        supplier_manager.add_supplier(
            "XYZ Corp",
            "Jane Doe",
            "jane@xyz.com",
            "555-5678",
            "456 Oak Ave"
        )
        supplier_manager.add_supplier(
            "Global Trading",
            "Bob Wilson",
            "bob@global.com",
            "555-9012",
            "789 Pine Rd"
        )
        
        # Get all suppliers
        suppliers = supplier_manager.get_all_suppliers()
        
        # Verify all suppliers are retrieved
        assert len(suppliers) == 3
        
        # Verify each supplier has required fields
        for supplier in suppliers:
            assert 'id' in supplier
            assert 'name' in supplier
            assert supplier['id'] > 0

    def test_search_suppliers_integration(self, supplier_manager):
        """Test searching suppliers with real data."""
        # Add test suppliers
        supplier_manager.add_supplier("Tech Supplies Inc", "Alice", "alice@tech.com")
        supplier_manager.add_supplier("Office Depot", "Bob", "bob@office.com")
        supplier_manager.add_supplier("Tech Warehouse", "Carol", "carol@warehouse.com")
        
        # Search for "Tech"
        results = supplier_manager.search_suppliers("Tech")
        
        assert len(results) == 2
        assert any("Tech Supplies" in s['name'] for s in results)
        assert any("Tech Warehouse" in s['name'] for s in results)

    def test_update_supplier_integration(self, supplier_manager):
        """Test updating supplier with real data."""
        # Add a supplier
        supplier_id = supplier_manager.add_supplier(
            "Old Name Corp",
            "John",
            "old@email.com"
        )
        
        # Update the supplier
        success = supplier_manager.update_supplier(
            supplier_id,
            name="New Name Corp",
            email="new@email.com",
            user="testuser"
        )
        
        assert success is True
        
        # Verify update
        supplier = supplier_manager.get_supplier(supplier_id)
        assert supplier['name'] == "New Name Corp"
        assert supplier['email'] == "new@email.com"

    def test_filter_suppliers_by_name(self, supplier_manager):
        """Test filtering suppliers by name."""
        supplier_manager.add_supplier("ABC Company")
        supplier_manager.add_supplier("XYZ Corporation")
        supplier_manager.add_supplier("ABC Industries")
        
        results = supplier_manager.filter_suppliers_by_name("ABC")
        
        assert len(results) == 2
        assert all("ABC" in s['name'] for s in results)

    def test_sort_suppliers(self, supplier_manager):
        """Test sorting suppliers."""
        supplier_manager.add_supplier("Zebra Corp", "Alice")
        supplier_manager.add_supplier("Apple Inc", "Bob")
        supplier_manager.add_supplier("Microsoft", "Carol")
        
        suppliers = supplier_manager.get_all_suppliers()
        sorted_suppliers = supplier_manager.sort_suppliers(suppliers, 'name')
        
        assert sorted_suppliers[0]['name'] == "Apple Inc"
        assert sorted_suppliers[1]['name'] == "Microsoft"
        assert sorted_suppliers[2]['name'] == "Zebra Corp"

    def test_display_suppliers_with_data(self, supplier_manager, capsys):
        """Test displaying suppliers with real data."""
        supplier_manager.add_supplier(
            "Test Supplier",
            "Test Contact",
            "test@example.com",
            "555-0000",
            "Test Address"
        )
        
        suppliers = supplier_manager.get_all_suppliers()
        supplier_manager.display_suppliers(suppliers)
        
        captured = capsys.readouterr()
        assert "Test Supplier" in captured.out
        assert "Test Contact" in captured.out
        assert "test@example.com" in captured.out

    def test_display_suppliers_empty(self, supplier_manager, capsys):
        """Test displaying empty supplier list."""
        supplier_manager.display_suppliers([])
        
        captured = capsys.readouterr()
        assert "No suppliers found" in captured.out

    def test_get_supplier_not_found(self, supplier_manager):
        """Test getting non-existent supplier."""
        supplier = supplier_manager.get_supplier(99999)
        assert supplier is None

    def test_update_supplier_not_found(self, supplier_manager):
        """Test updating non-existent supplier."""
        success = supplier_manager.update_supplier(99999, name="Test")
        assert success is False

    def test_add_supplier_validation(self, supplier_manager):
        """Test adding supplier with empty name."""
        with pytest.raises(ValueError, match="Supplier name is required"):
            supplier_manager.add_supplier("")

    def test_add_supplier_whitespace_name(self, supplier_manager):
        """Test adding supplier with whitespace-only name."""
        with pytest.raises(ValueError, match="Supplier name is required"):
            supplier_manager.add_supplier("   ")

    def test_sort_suppliers_invalid_field(self, supplier_manager):
        """Test sorting suppliers with invalid field defaults to name."""
        supplier_manager.add_supplier("Zebra")
        supplier_manager.add_supplier("Apple")
        
        suppliers = supplier_manager.get_all_suppliers()
        sorted_suppliers = supplier_manager.sort_suppliers(suppliers, 'invalid_field')
        
        # Should default to sorting by name
        assert sorted_suppliers[0]['name'] == "Apple"
        assert sorted_suppliers[1]['name'] == "Zebra"

    def test_complete_supplier_lifecycle(self, supplier_manager):
        """Test complete supplier lifecycle: add, view, update, search."""
        # Add supplier
        supplier_id = supplier_manager.add_supplier(
            "Lifecycle Test Corp",
            "Test Manager",
            "test@lifecycle.com",
            "555-TEST",
            "Test Street"
        )
        
        # View supplier
        supplier = supplier_manager.get_supplier(supplier_id)
        assert supplier is not None
        assert supplier['name'] == "Lifecycle Test Corp"
        
        # Update supplier
        supplier_manager.update_supplier(
            supplier_id,
            contact_person="Updated Manager",
            phone="555-UPDT"
        )
        
        # Verify update
        updated = supplier_manager.get_supplier(supplier_id)
        assert updated['contact_person'] == "Updated Manager"
        assert updated['phone'] == "555-UPDT"
        
        # Search for supplier
        results = supplier_manager.search_suppliers("Lifecycle")
        assert len(results) == 1
        assert results[0]['id'] == supplier_id
