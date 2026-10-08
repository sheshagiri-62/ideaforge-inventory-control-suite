"""
Supplier Manager Module
Manages supplier information and relationships.
Implements INV-F-020, INV-F-021.
"""

from typing import List, Dict, Optional
from .storage import StorageManager
from .logger import LogManager


class SupplierManager:
    """Manages supplier operations."""

    def __init__(self, storage: StorageManager = None, logger: LogManager = None):
        """
        Initialize supplier manager.

        Args:
            storage: StorageManager instance (optional)
            logger: LogManager instance (optional)
        """
        self.storage = storage or StorageManager()
        self.logger = logger or LogManager(self.storage)

    def add_supplier(self, name: str, contact_person: str = "",
                    email: str = "", phone: str = "",
                    address: str = "", user: str = "system") -> int:
        """
        Add new supplier (INV-F-020).

        Args:
            name: Supplier name
            contact_person: Contact person name
            email: Email address
            phone: Phone number
            address: Physical address
            user: Username performing the action

        Returns:
            Supplier ID

        Raises:
            ValueError: If supplier name is empty
        """
        # Validate inputs
        if not name or name.strip() == "":
            raise ValueError("Supplier name is required")

        # Add supplier
        supplier_id = self.storage.add_supplier(name, contact_person, email, phone, address)

        # Log action
        self.logger.log_action(
            user,
            "ADD_SUPPLIER",
            f"Added supplier: {name}"
        )

        return supplier_id

    def get_all_suppliers(self) -> List[Dict]:
        """
        Get all suppliers (INV-F-021).

        Returns:
            List of supplier dictionaries
        """
        return self.storage.get_all_suppliers()

    def get_supplier(self, supplier_id: int) -> Optional[Dict]:
        """
        Get supplier by ID.

        Args:
            supplier_id: Supplier ID

        Returns:
            Supplier dictionary or None if not found
        """
        return self.storage.get_supplier_by_id(supplier_id)

    def search_suppliers(self, search_term: str) -> List[Dict]:
        """
        Search suppliers by name, contact, or email (INV-F-021).

        Args:
            search_term: Search string

        Returns:
            List of matching supplier dictionaries
        """
        return self.storage.search_suppliers(search_term)

    def update_supplier(self, supplier_id: int, user: str = "system", **kwargs) -> bool:
        """
        Update supplier details.

        Args:
            supplier_id: Supplier ID to update
            user: Username performing the action
            **kwargs: Fields to update (name, contact_person, email, phone, address)

        Returns:
            True if successful, False otherwise
        """
        # Get current supplier for logging
        supplier = self.get_supplier(supplier_id)
        if not supplier:
            return False

        # Update supplier
        success = self.storage.update_supplier(supplier_id, **kwargs)

        if success:
            # Log action
            updates = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
            self.logger.log_action(
                user,
                "UPDATE_SUPPLIER",
                f"Updated supplier {supplier['name']} (ID: {supplier_id}): {updates}"
            )

        return success

    def display_suppliers(self, suppliers: List[Dict]):
        """
        Display suppliers in a formatted table.

        Args:
            suppliers: List of supplier dictionaries to display
        """
        if not suppliers:
            print("\nNo suppliers found.")
            return

        print("\n" + "="*120)
        header = (f"{'ID':<5} {'Name':<25} {'Contact Person':<20} "
                 f"{'Email':<25} {'Phone':<15} {'Address':<25}")
        print(header)
        print("="*120)

        for supplier in suppliers:
            supplier_id = str(supplier.get('id', ''))[:4]
            name = supplier.get('name', '')[:24]
            contact = supplier.get('contact_person', '')[:19]
            email = supplier.get('email', '')[:24]
            phone = supplier.get('phone', '')[:14]
            address = supplier.get('address', '')[:24]

            row = (f"{supplier_id:<5} {name:<25} {contact:<20} "
                  f"{email:<25} {phone:<15} {address:<25}")
            print(row)

        print("="*120 + "\n")

    def filter_suppliers_by_name(self, name_part: str) -> List[Dict]:
        """
        Filter suppliers by name (INV-F-021).

        Args:
            name_part: Part of name to filter by

        Returns:
            List of matching suppliers
        """
        all_suppliers = self.get_all_suppliers()
        return [s for s in all_suppliers if name_part.lower() in s['name'].lower()]

    def sort_suppliers(self, suppliers: List[Dict], sort_by: str = 'name') -> List[Dict]:
        """
        Sort suppliers by a field (INV-F-021).

        Args:
            suppliers: List of suppliers to sort
            sort_by: Field to sort by ('name', 'contact_person', 'email')

        Returns:
            Sorted list of suppliers
        """
        valid_fields = ['name', 'contact_person', 'email', 'phone']
        if sort_by not in valid_fields:
            sort_by = 'name'

        return sorted(suppliers, key=lambda s: s.get(sort_by, '').lower())
