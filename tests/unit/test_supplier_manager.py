"""
Unit tests for supplier_manager module.
Tests INV-F-020, INV-F-021.
"""

import pytest
import tempfile
import os
from src.supplier_manager import SupplierManager
from src.storage import StorageManager
from src.logger import LogManager


class TestSupplierManager:
    """Test supplier manager."""

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

    def test_add_supplier_success(self, supplier_manager):
        """Test adding supplier successfully (INV-F-020)."""
        supplier_id = supplier_manager.add_supplier(
            name="ABC Suppliers",
            contact_person="John Smith",
            email="john@abc.com",
            phone="555-1234",
            address="123 Main St"
        )
        
        assert supplier_id is not None
        assert supplier_id > 0

    def test_add_supplier_minimal(self, supplier_manager):
        """Test adding supplier with minimal information."""
        supplier_id = supplier_manager.add_supplier(name="XYZ Corp")
        
        assert supplier_id is not None
        assert supplier_id > 0

    def test_add_supplier_empty_name(self, supplier_manager):
        """Test adding supplier with empty name raises error."""
        with pytest.raises(ValueError):
            supplier_manager.add_supplier(name="")

    def test_get_all_suppliers(self, supplier_manager):
        """Test getting all suppliers (INV-F-021)."""
        supplier_manager.add_supplier("Supplier 1", "Contact 1", "email1@test.com")
        supplier_manager.add_supplier("Supplier 2", "Contact 2", "email2@test.com")
        
        suppliers = supplier_manager.get_all_suppliers()
        
        assert len(suppliers) >= 2

    def test_get_supplier(self, supplier_manager):
        """Test getting single supplier by ID."""
        supplier_id = supplier_manager.add_supplier("Test Supplier", "Contact", "email@test.com")
        
        supplier = supplier_manager.get_supplier(supplier_id)
        
        assert supplier is not None
        assert supplier['name'] == "Test Supplier"
        assert supplier['contact_person'] == "Contact"

    def test_search_suppliers_by_name(self, supplier_manager):
        """Test searching suppliers by name (INV-F-021)."""
        supplier_manager.add_supplier("ABC Electronics", "John", "john@abc.com")
        supplier_manager.add_supplier("XYZ Electronics", "Jane", "jane@xyz.com")
        supplier_manager.add_supplier("Office Supplies Co", "Bob", "bob@office.com")
        
        results = supplier_manager.search_suppliers("Electronics")
        
        assert len(results) == 2

    def test_search_suppliers_by_email(self, supplier_manager):
        """Test searching suppliers by email (INV-F-021)."""
        supplier_manager.add_supplier("Supplier 1", "Contact", "special@domain.com")
        supplier_manager.add_supplier("Supplier 2", "Contact", "other@test.com")
        
        results = supplier_manager.search_suppliers("special")
        
        assert len(results) >= 1

    def test_update_supplier_success(self, supplier_manager):
        """Test updating supplier details."""
        supplier_id = supplier_manager.add_supplier("Old Name", "Old Contact", "old@email.com")
        
        success = supplier_manager.update_supplier(
            supplier_id,
            name="New Name",
            email="new@email.com"
        )
        
        assert success is True
        
        supplier = supplier_manager.get_supplier(supplier_id)
        assert supplier['name'] == "New Name"
        assert supplier['email'] == "new@email.com"

    def test_update_supplier_not_found(self, supplier_manager):
        """Test updating non-existent supplier fails."""
        success = supplier_manager.update_supplier(99999, name="Test")
        
        assert success is False

    def test_filter_suppliers_by_name(self, supplier_manager):
        """Test filtering suppliers by name (INV-F-021)."""
        supplier_manager.add_supplier("ABC Corp", "Contact 1", "abc@test.com")
        supplier_manager.add_supplier("ABC Industries", "Contact 2", "industries@test.com")
        supplier_manager.add_supplier("XYZ Ltd", "Contact 3", "xyz@test.com")
        
        filtered = supplier_manager.filter_suppliers_by_name("ABC")
        
        assert len(filtered) == 2

    def test_sort_suppliers_by_name(self, supplier_manager):
        """Test sorting suppliers (INV-F-021)."""
        supplier_manager.add_supplier("Zebra Corp", "Contact", "zebra@test.com")
        supplier_manager.add_supplier("Alpha Corp", "Contact", "alpha@test.com")
        supplier_manager.add_supplier("Beta Corp", "Contact", "beta@test.com")
        
        suppliers = supplier_manager.get_all_suppliers()
        sorted_suppliers = supplier_manager.sort_suppliers(suppliers, sort_by='name')
        
        assert sorted_suppliers[0]['name'] == "Alpha Corp"
        assert sorted_suppliers[-1]['name'] == "Zebra Corp"

    def test_sort_suppliers_invalid_field(self, supplier_manager):
        """Test sorting with invalid field defaults to name."""
        supplier_manager.add_supplier("Zebra Corp", "Contact", "zebra@test.com")
        supplier_manager.add_supplier("Alpha Corp", "Contact", "alpha@test.com")
        
        suppliers = supplier_manager.get_all_suppliers()
        sorted_suppliers = supplier_manager.sort_suppliers(suppliers, sort_by='invalid_field')
        
        # Should default to name sorting
        assert sorted_suppliers[0]['name'] == "Alpha Corp"
