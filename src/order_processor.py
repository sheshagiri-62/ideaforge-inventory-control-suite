"""
Order Processor Module
Handles order processing and workflow.
Implements INV-F-010, INV-F-011, INV-F-012, INV-F-031.
"""

from typing import List, Dict, Optional
from .storage import StorageManager
from .logger import LogManager
from .product_manager import ProductManager


class OrderProcessor:
    """Processes customer orders."""

    def __init__(self, storage=None, logger=None, product_manager=None):
        """
        Initialize order processor.

        Args:
            storage: StorageManager instance (optional)
            logger: LogManager instance (optional)
            product_manager: ProductManager instance (optional)
        """
        self.storage = storage or StorageManager()
        self.logger = logger or LogManager(self.storage)
        self.product_manager = product_manager or ProductManager(self.storage, self.logger)

    def create_sales_order(self, product_id: int, quantity: int,
                          user: str = "system") -> Optional[int]:
        """
        Create sales order and reduce stock (INV-F-010, INV-F-011).

        Args:
            product_id: Product ID
            quantity: Quantity to sell
            user: Username performing the action

        Returns:
            Order ID if successful, None if insufficient stock

        Raises:
            ValueError: If product not found or invalid quantity
        """
        # Validate quantity
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        # Get product
        product = self.product_manager.get_product(product_id)
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")

        # Check stock availability (INV-F-011)
        if product['stock'] < quantity:
            return None  # Insufficient stock

        # Calculate total price
        total_price = product['price'] * quantity

        # Create sales order
        order_id = self.storage.create_sales_order(product_id, quantity, total_price)

        # Reduce stock
        new_stock = product['stock'] - quantity
        self.product_manager.update_product(product_id, stock=new_stock, user=user)

        # Log action
        self.logger.log_action(
            user,
            "CREATE_SALES_ORDER",
            f"Sold {quantity} units of {product['name']} (Order ID: {order_id}, Total: ${total_price:.2f})"
        )

        return order_id

    def create_purchase_order(self, product_id: int, supplier_id: int,
                             quantity: int, unit_price: float,
                             user: str = "system") -> int:
        """
        Create purchase order and increase stock (INV-F-012).

        Args:
            product_id: Product ID
            supplier_id: Supplier ID
            quantity: Quantity to purchase
            unit_price: Price per unit
            user: Username performing the action

        Returns:
            Order ID

        Raises:
            ValueError: If product/supplier not found or invalid inputs
        """
        # Validate inputs
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if unit_price < 0:
            raise ValueError("Unit price cannot be negative")

        # Get product
        product = self.product_manager.get_product(product_id)
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")

        # Calculate total price
        total_price = unit_price * quantity

        # Create purchase order
        order_id = self.storage.create_purchase_order(
            product_id, supplier_id, quantity, unit_price, total_price
        )

        # Increase stock
        new_stock = product['stock'] + quantity
        self.product_manager.update_product(product_id, stock=new_stock, user=user)

        # Log action
        self.logger.log_action(
            user,
            "CREATE_PURCHASE_ORDER",
            f"Purchased {quantity} units of {product['name']} (Order ID: {order_id}, Total: ${total_price:.2f})"
        )

        return order_id

    def get_sales_orders(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        Get sales orders with optional date filtering (INV-F-031).

        Args:
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)

        Returns:
            List of sales order dictionaries
        """
        return self.storage.get_sales_orders(start_date, end_date)

    def get_purchase_orders(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        Get purchase orders with optional date filtering (INV-F-031).

        Args:
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)

        Returns:
            List of purchase order dictionaries
        """
        return self.storage.get_purchase_orders(start_date, end_date)

    def get_sales_report(self, start_date: str = None, end_date: str = None) -> Dict:
        """
        Generate sales report (INV-F-031).

        Args:
            start_date: Start date in ISO format
            end_date: End date in ISO format

        Returns:
            Dictionary with sales summary
        """
        orders = self.get_sales_orders(start_date, end_date)

        total_orders = len(orders)
        total_revenue = sum(order['total_price'] for order in orders)
        total_units = sum(order['quantity'] for order in orders)

        return {
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'total_units': total_units,
            'orders': orders
        }

    def get_purchase_report(self, start_date: str = None, end_date: str = None) -> Dict:
        """
        Generate purchase report (INV-F-031).

        Args:
            start_date: Start date in ISO format
            end_date: End date in ISO format

        Returns:
            Dictionary with purchase summary
        """
        orders = self.get_purchase_orders(start_date, end_date)

        total_orders = len(orders)
        total_cost = sum(order['total_price'] for order in orders)
        total_units = sum(order['quantity'] for order in orders)

        return {
            'total_orders': total_orders,
            'total_cost': total_cost,
            'total_units': total_units,
            'orders': orders
        }

    def display_sales_orders(self, orders: List[Dict]):
        """Display sales orders in formatted table."""
        if not orders:
            print("\nNo sales orders found.")
            return

        print("\n" + "="*100)
        print(f"{'Order ID':<10} {'Product':<30} {'Quantity':<10} {'Total Price':<15} {'Date':<25}")
        print("="*100)

        for order in orders:
            order_id = str(order.get('id', ''))
            product_name = order.get('product_name', 'Unknown')[:29]
            quantity = str(order.get('quantity', 0))
            total_price = f"${order.get('total_price', 0):.2f}"
            order_date = order.get('order_date', '')[:24]

            print(f"{order_id:<10} {product_name:<30} {quantity:<10} {total_price:<15} {order_date:<25}")

        print("="*100 + "\n")

    def display_purchase_orders(self, orders: List[Dict]):
        """Display purchase orders in formatted table."""
        if not orders:
            print("\nNo purchase orders found.")
            return

        print("\n" + "="*120)
        print(f"{'Order ID':<10} {'Product':<25} {'Supplier':<20} {'Quantity':<10} {'Unit Price':<12} {'Total':<12} {'Date':<20}")
        print("="*120)

        for order in orders:
            order_id = str(order.get('id', ''))
            product_name = order.get('product_name', 'Unknown')[:24]
            supplier_name = order.get('supplier_name', 'N/A')[:19]
            quantity = str(order.get('quantity', 0))
            unit_price = f"${order.get('unit_price', 0):.2f}"
            total_price = f"${order.get('total_price', 0):.2f}"
            order_date = order.get('order_date', '')[:19]

            print(f"{order_id:<10} {product_name:<25} {supplier_name:<20} {quantity:<10} {unit_price:<12} {total_price:<12} {order_date:<20}")

        print("="*120 + "\n")
