"""
Product Manager Module
Manages product inventory operations (CRUD).
Implements INV-F-001, INV-F-002, INV-F-003, INV-F-032.
"""

from typing import List, Dict, Optional
from .storage import StorageManager
from .logger import LogManager
from .config import LOW_STOCK_THRESHOLD


class ProductManager:
    """Manages product inventory."""

    def __init__(self, storage: StorageManager = None, logger: LogManager = None):
        """
        Initialize product manager.

        Args:
            storage: StorageManager instance (optional)
            logger: LogManager instance (optional)
        """
        self.storage = storage or StorageManager()
        self.logger = logger or LogManager(self.storage)

    def add_product(self, sku: str, name: str, price: float, category: str,
                   stock: int, description: str = "", user: str = "system") -> Optional[int]:
        """
        Add new product to inventory (INV-F-001).

        Args:
            sku: Unique product SKU
            name: Product name
            price: Product price
            category: Product category
            stock: Initial stock quantity
            description: Product description
            user: Username performing the action

        Returns:
            Product ID if successful, None if SKU already exists
        """
        # Check if SKU already exists
        existing = self.storage.get_product_by_sku(sku)
        if existing:
            return None

        # Validate inputs
        if price < 0:
            raise ValueError("Price cannot be negative")
        if stock < 0:
            raise ValueError("Stock cannot be negative")

        # Add product
        product_id = self.storage.add_product(sku, name, price, category, stock, description)

        # Log action
        self.logger.log_action(
            user,
            "ADD_PRODUCT",
            f"Added product: {name} (SKU: {sku})"
        )

        return product_id

    def get_product_confirmation(self, product_id: int) -> Dict:
        """
        Get confirmation details for a newly added product (INV-F-005).

        Args:
            product_id: ID of the newly added product

        Returns:
            Dictionary containing confirmation details
        """
        product = self.storage.get_product_by_id(product_id)
        
        if not product:
            return {
                'success': False,
                'message': 'Product not found',
                'product': None
            }
        
        return {
            'success': True,
            'message': f"Product '{product['name']}' (SKU: {product['sku']}) added successfully!",
            'product': {
                'id': product['id'],
                'sku': product['sku'],
                'name': product['name'],
                'price': product['price'],
                'category': product['category'],
                'stock': product['stock'],
                'description': product.get('description', ''),
                'created_at': product.get('created_at', '')
            }
        }

    def add_product_with_confirmation(self, sku: str, name: str, price: float, 
                                     category: str, stock: int, description: str = "", 
                                     user: str = "system") -> Dict:
        """
        Add new product and return confirmation details (INV-F-001 + INV-F-005).

        Args:
            sku: Unique product SKU
            name: Product name
            price: Product price
            category: Product category
            stock: Initial stock quantity
            description: Product description
            user: Username performing the action

        Returns:
            Dictionary with success status, message, and product details
        """
        # Check if SKU already exists
        existing = self.storage.get_product_by_sku(sku)
        if existing:
            return {
                'success': False,
                'message': f"Product with SKU '{sku}' already exists",
                'product': None
            }

        # Validate inputs
        try:
            if price < 0:
                raise ValueError("Price cannot be negative")
            if stock < 0:
                raise ValueError("Stock cannot be negative")
            
            # Add product
            product_id = self.add_product(sku, name, price, category, stock, description, user)
            
            # Get confirmation
            return self.get_product_confirmation(product_id)
            
        except ValueError as e:
            return {
                'success': False,
                'message': str(e),
                'product': None
            }

    def get_all_products(self) -> List[Dict]:
        """
        Get all products (INV-F-002).

        Returns:
            List of product dictionaries
        """
        return self.storage.get_all_products()

    def get_product(self, product_id: int) -> Optional[Dict]:
        """
        Get product by ID.

        Args:
            product_id: Product ID

        Returns:
            Product dictionary or None if not found
        """
        return self.storage.get_product_by_id(product_id)

    def search_products(self, search_term: str) -> List[Dict]:
        """
        Search products by name, SKU, or category (INV-F-002).

        Args:
            search_term: Search string

        Returns:
            List of matching product dictionaries
        """
        return self.storage.search_products(search_term)

    def update_product(self, product_id: int, user: str = "system", **kwargs) -> bool:
        """
        Update product details (INV-F-003).

        Args:
            product_id: Product ID to update
            user: Username performing the action
            **kwargs: Fields to update (name, price, category, stock, description)

        Returns:
            True if successful, False otherwise
        """
        # Validate price and stock if being updated
        if 'price' in kwargs and kwargs['price'] < 0:
            raise ValueError("Price cannot be negative")
        if 'stock' in kwargs and kwargs['stock'] < 0:
            raise ValueError("Stock cannot be negative")

        # Get current product for logging
        product = self.get_product(product_id)
        if not product:
            return False

        # Update product
        success = self.storage.update_product(product_id, **kwargs)

        if success:
            # Log action
            updates = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
            self.logger.log_action(
                user,
                "UPDATE_PRODUCT",
                f"Updated product {product['name']} (ID: {product_id}): {updates}"
            )

        return success

    def delete_product(self, product_id: int, user: str = "system") -> bool:
        """
        Delete product (admin only).
        Logs deletion details for admin review.

        Args:
            product_id: Product ID to delete
            user: Username performing the action

        Returns:
            True if successful, False otherwise
        """
        # Get product for logging before deletion
        product = self.get_product(product_id)
        if not product:
            return False

        # Delete product
        success = self.storage.delete_product(product_id)

        if success:
            # Log action (PRJ-SEC-003) with detailed information
            self.logger.log_action(
                user,
                "DELETE_PRODUCT",
                f"Deleted product: {product['name']} (SKU: {product['sku']}, ID: {product_id})"
            )

        return success

    def get_low_stock_products(self, threshold: int = None) -> List[Dict]:
        """
        Get products with low stock (INV-F-032).

        Args:
            threshold: Stock threshold (uses config default if not provided)

        Returns:
            List of products with stock at or below threshold
        """
        threshold = threshold if threshold is not None else LOW_STOCK_THRESHOLD
        return self.storage.get_low_stock_products(threshold)

    def check_stock_availability(self, product_id: int, quantity: int) -> bool:
        """
        Check if sufficient stock is available.

        Args:
            product_id: Product ID
            quantity: Required quantity

        Returns:
            True if sufficient stock available, False otherwise
        """
        product = self.get_product(product_id)
        if not product:
            return False
        return product['stock'] >= quantity

    def adjust_stock(self, product_id: int, quantity_change: int,
                    user: str = "system") -> bool:
        """
        Adjust product stock by a delta amount.

        Args:
            product_id: Product ID
            quantity_change: Amount to add (positive) or remove (negative)
            user: Username performing the action

        Returns:
            True if successful, False otherwise
        """
        product = self.get_product(product_id)
        if not product:
            return False

        new_stock = product['stock'] + quantity_change

        if new_stock < 0:
            raise ValueError("Insufficient stock for this operation")

        return self.update_product(product_id, stock=new_stock, user=user)

    def generate_inventory_report(self, user: str = "system") -> Dict:
        """
        Generate comprehensive inventory report (User Story: Generate inventory report).
        As a staff member, I want to generate an inventory report to check stock levels.

        Args:
            user: Username performing the action

        Returns:
            Dictionary containing inventory report data
        """
        # Get all products
        all_products = self.get_all_products()
        
        # Calculate total inventory value
        total_value = sum(product['price'] * product['stock'] for product in all_products)
        total_stock = sum(product['stock'] for product in all_products)
        
        # Get low stock items
        low_stock_items = self.get_low_stock_products()
        
        # Group by category
        category_stats = {}
        for product in all_products:
            category = product.get('category', 'Uncategorized')
            if category not in category_stats:
                category_stats[category] = {
                    'count': 0,
                    'total_stock': 0,
                    'total_value': 0.0
                }
            category_stats[category]['count'] += 1
            category_stats[category]['total_stock'] += product['stock']
            category_stats[category]['total_value'] += product['price'] * product['stock']
        
        # Create report
        report = {
            'total_products': len(all_products),
            'total_stock': total_stock,
            'total_inventory_value': total_value,
            'low_stock_count': len(low_stock_items),
            'low_stock_items': low_stock_items,
            'category_breakdown': category_stats,
            'all_products': all_products
        }
        
        # Log action
        self.logger.log_action(
            user,
            "GENERATE_INVENTORY_REPORT",
            f"Generated inventory report: {len(all_products)} products, "
            f"{len(low_stock_items)} low stock items"
        )
        
        return report

    def display_inventory_report(self, report: Dict):
        """
        Display inventory report in formatted output.

        Args:
            report: Report dictionary from generate_inventory_report
        """
        print("\n" + "="*100)
        print("  INVENTORY REPORT")
        print("="*100)
        
        # Summary section
        print("\n=== SUMMARY ===")
        print(f"Total Products: {report['total_products']}")
        print(f"Total Stock Units: {report['total_stock']}")
        print(f"Total Inventory Value: ${report['total_inventory_value']:.2f}")
        print(f"Low Stock Items: {report['low_stock_count']}")
        
        # Category breakdown
        if report['category_breakdown']:
            print("\n=== CATEGORY BREAKDOWN ===")
            print(f"{'Category':<20} {'Products':<10} {'Stock':<10} {'Value':<15}")
            print("-" * 55)
            for category, stats in sorted(report['category_breakdown'].items()):
                print(f"{category:<20} {stats['count']:<10} "
                      f"{stats['total_stock']:<10} ${stats['total_value']:<14.2f}")
        
        # Low stock items
        if report['low_stock_items']:
            print("\n=== LOW STOCK ALERTS ===")
            print(f"{'SKU':<12} {'Name':<30} {'Stock':<10} {'Status'}")
            print("-" * 70)
            for item in report['low_stock_items']:
                status = "CRITICAL" if item['stock'] == 0 else "LOW"
                print(f"{item['sku']:<12} {item['name']:<30} "
                      f"{item['stock']:<10} {status}")
        
        # All products detail
        print("\n=== DETAILED INVENTORY ===")
        self.display_products(report['all_products'])

    def display_products(self, products: List[Dict]):
        """
        Display products in a formatted table.

        Args:
            products: List of product dictionaries to display
        """
        if not products:
            print("\nNo products found.")
            return

        print("\n" + "="*120)
        print(f"{'ID':<5} {'SKU':<12} {'Name':<25} {'Category':<15} {'Price':<10} {'Stock':<8} {'Description':<30}")
        print("="*120)

        for product in products:
            product_id = str(product.get('id', ''))[:4]
            sku = product.get('sku', '')[:11]
            name = product.get('name', '')[:24]
            category = product.get('category', '')[:14]
            price = f"${product.get('price', 0):.2f}"
            stock = str(product.get('stock', 0))
            description = product.get('description', '')[:29]

            print(f"{product_id:<5} {sku:<12} {name:<25} {category:<15} {price:<10} {stock:<8} {description:<30}")

        print("="*120 + "\n")
