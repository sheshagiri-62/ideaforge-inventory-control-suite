"""
Command-Line Interface Module
Handles user interaction and command parsing for the IMS.
Implements INV-NF-005 (User-friendly CLI).
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=wrong-import-position
from src.storage import StorageManager
from src.auth import AuthManager
from src.logger import LogManager
from src.product_manager import ProductManager
from src.supplier_manager import SupplierManager
from src.order_processor import OrderProcessor
from src.backup_security import BackupManager
from src.config import LOW_STOCK_THRESHOLD

# Configure UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'replace')
    except Exception:  # pylint: disable=broad-exception-caught
        # Fallback: use ASCII-safe output
        pass


class CLI:
    """Command-line interface for IMS."""

    def __init__(self):
        """Initialize CLI and all managers."""
        self.storage = StorageManager()
        self.auth = AuthManager(self.storage)  # pylint: disable=too-many-function-args
        self.logger = LogManager(self.storage)
        self.product_manager = ProductManager(self.storage, self.logger)
        self.supplier_manager = SupplierManager(self.storage, self.logger)  # pylint: disable=too-many-function-args
        self.order_processor = OrderProcessor(self.storage, self.logger, self.product_manager)  # pylint: disable=too-many-function-args
        self.backup_manager = BackupManager(self.logger)  # pylint: disable=too-many-function-args
        self.running = True

    def clear_screen(self):
        """Clear the terminal screen."""
        # Use ANSI escape codes instead of os.system for security (B605)
        if os.name == 'nt':
            # Windows
            os.system('cls')  # nosec B605 - safe, no user input
        else:
            # Unix/Linux
            print('\033[2J\033[H', end='')

    def print_header(self, title: str):
        """Print formatted header."""
        print("\n" + "="*80)
        print(f"  {title}")
        print("="*80)

    def input_with_prompt(self, prompt: str, required: bool = True) -> str:
        """Get input with validation."""
        while True:
            value = input(f"{prompt}: ").strip()
            if not required or value:
                return value
            print("  [!] This field is required. Please enter a value.")

    def input_number(self, prompt: str, allow_float: bool = False) -> float:
        """Get numeric input with validation."""
        while True:
            try:
                value = input(f"{prompt}: ").strip()
                if allow_float:
                    return float(value)
                return int(value)
            except ValueError:
                print("  [!] Please enter a valid number.")

    def show_main_menu(self):
        """Display main menu."""
        self.clear_screen()
        self.print_header("INVENTORY MANAGEMENT SYSTEM")

        if self.auth.is_authenticated():  # pylint: disable=no-member
            username = self.auth.get_current_username()  # pylint: disable=no-member
            role = "Admin" if self.auth.is_admin() else "User"  # pylint: disable=no-member
            print(f"\nLogged in as: {username} ({role})")
        else:
            print("\nNot logged in (Guest mode - limited access)")

        print("\n1. Product Management")
        print("2. Supplier Management")
        print("3. Order Processing")
        print("4. Reports & Analytics")
        print("5. Backup & Restore (Admin)")
        print("6. View Logs (Admin)")
        print("7. Login / Logout")
        print("8. Help")
        print("0. Exit")
        print()

    def main_menu(self):
        """Handle main menu selection."""
        while self.running:
            self.show_main_menu()
            choice = input("Select an option: ").strip()

            if choice == '1':
                self.product_menu()
            elif choice == '2':
                self.supplier_menu()
            elif choice == '3':
                self.order_menu()
            elif choice == '4':
                self.reports_menu()
            elif choice == '5':
                self.backup_menu()
            elif choice == '6':
                self.logs_menu()
            elif choice == '7':
                self.auth_menu()
            elif choice == '8':
                self.show_help()
            elif choice == '0':
                self.exit_application()
            else:
                print("Invalid option. Please try again.")
                input("\nPress Enter to continue...")

    # ========== Product Management ==========

    def product_menu(self):
        """Product management submenu."""
        while True:
            self.clear_screen()
            self.print_header("PRODUCT MANAGEMENT")
            print("\n1. Add Product")
            print("2. View All Products")
            print("3. Search Products")
            print("4. Update Product")
            print("5. Delete Product (Admin)")
            print("6. Adjust Stock Quantity")
            print("7. Low Stock Alert")
            print("0. Back to Main Menu")
            print()

            choice = input("Select an option: ").strip()

            if choice == '1':
                self.add_product()
            elif choice == '2':
                self.view_products()
            elif choice == '3':
                self.search_products()
            elif choice == '4':
                self.update_product()
            elif choice == '5':
                self.delete_product()
            elif choice == '6':
                self.adjust_stock_quantity()
            elif choice == '7':
                self.show_low_stock()
            elif choice == '0':
                break
            else:
                print("Invalid option.")
                input("\nPress Enter to continue...")

    def add_product(self):
        """Add new product (INV-F-001)."""
        self.clear_screen()
        self.print_header("ADD NEW PRODUCT")

        try:
            sku = self.input_with_prompt("SKU (unique)")
            name = self.input_with_prompt("Product Name")
            price = self.input_number("Price", allow_float=True)
            category = self.input_with_prompt("Category")
            stock = self.input_number("Initial Stock Quantity")
            description = self.input_with_prompt("Description (optional)", required=False)

            user = self.auth.get_current_username()  # pylint: disable=no-member
            product_id = self.product_manager.add_product(
                sku, name, price, category, stock, description, user
            )

            if product_id:
                print(f"\n[OK] Product added successfully! ID: {product_id}")
            else:
                print(f"\n[X] Error: SKU '{sku}' already exists.")
        except ValueError as error:
            print(f"\n[X] Error: {str(error)}")

        input("\nPress Enter to continue...")

    def view_products(self):
        """View all products (INV-F-002)."""
        self.clear_screen()
        self.print_header("ALL PRODUCTS")

        products = self.product_manager.get_all_products()
        self.product_manager.display_products(products)

        input("Press Enter to continue...")

    def search_products(self):
        """Search products (INV-F-002)."""
        self.clear_screen()
        self.print_header("SEARCH PRODUCTS")

        search_term = self.input_with_prompt("Enter search term (name/SKU/category)")
        products = self.product_manager.search_products(search_term)

        print(f"\nFound {len(products)} product(s):")
        self.product_manager.display_products(products)

        input("Press Enter to continue...")

    def update_product(self):
        """Update product (INV-F-003)."""
        self.clear_screen()
        self.print_header("UPDATE PRODUCT")
        
        try:
            product_id = int(self.input_with_prompt("Product ID"))
            product = self.product_manager.get_product(product_id)
            
            if not product:
                print("\n[X] Product not found.")
                input("\nPress Enter to continue...")
                return
            
            print(f"\nCurrent details for: {product['name']}")
            print(f"  SKU: {product['sku']}")
            print(f"  Price: ${product['price']:.2f}")
            print(f"  Category: {product['category']}")
            print(f"  Stock: {product['stock']}")
            print(f"  Description: {product['description']}")
            
            print("\nLeave fields blank to keep current value:")
            updates = {}
            
            name = input("New Name: ").strip()
            if name:
                updates['name'] = name
            
            price_str = input("New Price: ").strip()
            if price_str:
                updates['price'] = float(price_str)
            
            category = input("New Category: ").strip()
            if category:
                updates['category'] = category
            
            stock_str = input("New Stock: ").strip()
            if stock_str:
                updates['stock'] = int(stock_str)
            
            description = input("New Description: ").strip()
            if description:
                updates['description'] = description
            
            if updates:
                user = self.auth.get_current_username()
                success = self.product_manager.update_product(product_id, user=user, **updates)
                if success:
                    print("\n[OK] Product updated successfully!")
                else:
                    print("\n[X] Update failed.")
            else:
                print("\nNo changes made.")
        except Exception as e:
            print(f"\n[X] Error: {str(e)}")
        
        input("\nPress Enter to continue...")

    def adjust_stock_quantity(self):
        """Adjust stock quantity (INV-F-004)."""
        self.clear_screen()
        self.print_header("ADJUST STOCK QUANTITY")
        
        try:
            product_id = int(self.input_with_prompt("Product ID"))
            product = self.product_manager.get_product(product_id)
            
            if not product:
                print("\n[X] Product not found.")
                input("\nPress Enter to continue...")
                return
            
            print(f"\nProduct: {product['name']} (SKU: {product['sku']})")
            print(f"Current stock: {product['stock']}")
            
            print("\nAdjustment Options:")
            print("  1. Increase stock (e.g., new inventory received)")
            print("  2. Decrease stock (e.g., damage, theft, correction)")
            print("  3. Set exact quantity")
            
            adjustment_type = input("\nSelect adjustment type (1-3): ").strip()
            
            if adjustment_type == '1':
                # Increase stock
                quantity = int(self.input_with_prompt("Quantity to add"))
                if quantity <= 0:
                    print("\n[X] Quantity must be positive.")
                    input("\nPress Enter to continue...")
                    return
                
                user = self.auth.get_current_username()
                success = self.product_manager.adjust_stock(product_id, quantity, user=user)
                
                if success:
                    new_product = self.product_manager.get_product(product_id)
                    print(f"\n[OK] Stock increased successfully!")
                    print(f"Previous stock: {product['stock']}")
                    print(f"Added: +{quantity}")
                    print(f"New stock: {new_product['stock']}")
                else:
                    print("\n[X] Stock adjustment failed.")
                    
            elif adjustment_type == '2':
                # Decrease stock
                quantity = int(self.input_with_prompt("Quantity to remove"))
                if quantity <= 0:
                    print("\n[X] Quantity must be positive.")
                    input("\nPress Enter to continue...")
                    return
                
                if quantity > product['stock']:
                    print(f"\n[X] Cannot remove {quantity} units. Only {product['stock']} in stock.")
                    input("\nPress Enter to continue...")
                    return
                
                user = self.auth.get_current_username()
                success = self.product_manager.adjust_stock(product_id, -quantity, user=user)
                
                if success:
                    new_product = self.product_manager.get_product(product_id)
                    print(f"\n[OK] Stock decreased successfully!")
                    print(f"Previous stock: {product['stock']}")
                    print(f"Removed: -{quantity}")
                    print(f"New stock: {new_product['stock']}")
                else:
                    print("\n[X] Stock adjustment failed.")
                    
            elif adjustment_type == '3':
                # Set exact quantity
                new_stock = int(self.input_with_prompt("New stock quantity"))
                if new_stock < 0:
                    print("\n[X] Stock cannot be negative.")
                    input("\nPress Enter to continue...")
                    return
                
                user = self.auth.get_current_username()
                success = self.product_manager.update_product(product_id, stock=new_stock, user=user)
                
                if success:
                    print(f"\n[OK] Stock set successfully!")
                    print(f"Previous stock: {product['stock']}")
                    print(f"New stock: {new_stock}")
                    print(f"Change: {new_stock - product['stock']:+d}")
                else:
                    print("\n[X] Stock update failed.")
            else:
                print("\n[X] Invalid option.")
                
        except ValueError as e:
            print(f"\n[X] Invalid input: {str(e)}")
        except Exception as e:
            print(f"\n[X] Error: {str(e)}")
        
        input("\nPress Enter to continue...")

    def show_low_stock(self):
        """Show low stock products (INV-F-032)."""
        self.clear_screen()
        self.print_header(f"LOW STOCK ALERT (Threshold: {LOW_STOCK_THRESHOLD})")
        
        products = self.product_manager.get_low_stock_products()
        
        if products:
            print(f"\n[!] {len(products)} product(s) with low stock:")
            self.product_manager.display_products(products)
        else:
            print("\n[OK] All products have adequate stock.")
        
        input("Press Enter to continue...")

    def confirm_deletion(self, item_type: str, item_description: str) -> bool:
        """
        Confirm deletion with double-check to avoid mistakes.
        Implements INV-8: Confirm before deletion user story.
        
        Args:
            item_type: Type of item being deleted (e.g., "Product", "Supplier")
            item_description: Description of the item being deleted
            
        Returns:
            True if user confirms deletion, False otherwise
        """
        print(f"\n{'='*80}")
        print(f"⚠️  DELETION CONFIRMATION")
        print(f"{'='*80}")
        print(f"\n{item_type} to delete: {item_description}")
        print("\n⚠️  WARNING: This action cannot be undone!")
        print("The deletion will be logged for audit purposes.")
        print(f"{'='*80}\n")
        
        # First confirmation
        confirm1 = input("Do you want to proceed with deletion? (yes/no): ").strip().lower()
        
        if confirm1 not in ['yes', 'y']:
            print("\n[INFO] Deletion cancelled - No changes made.")
            return False
        
        # Second confirmation for extra safety
        print("\n⚠️  FINAL CONFIRMATION REQUIRED")
        confirm2 = input("Type 'DELETE' to confirm (case-sensitive): ").strip()
        
        if confirm2 == 'DELETE':
            print("\n[INFO] Deletion confirmed. Processing...")
            return True
        else:
            print("\n[INFO] Deletion cancelled - Incorrect confirmation.")
            return False

    def delete_product(self):
        """
        Delete product (Admin only).
        Implements INV-7: Log deletions and INV-8: Confirm before deletion.
        """
        self.clear_screen()
        self.print_header("DELETE PRODUCT (ADMIN ONLY)")
        
        if not self.auth.is_admin():
            print("\n[X] Admin privileges required.")
            input("\nPress Enter to continue...")
            return
        
        try:
            product_id = int(self.input_with_prompt("Product ID to delete"))
            product = self.product_manager.get_product(product_id)
            
            if not product:
                print("\n[X] Product not found.")
                input("\nPress Enter to continue...")
                return
            
            # Show detailed product information
            print("\n" + "="*80)
            print("PRODUCT DETAILS")
            print("="*80)
            print(f"ID:          {product['id']}")
            print(f"SKU:         {product['sku']}")
            print(f"Name:        {product['name']}")
            print(f"Category:    {product['category']}")
            print(f"Price:       ${product['price']:.2f}")
            print(f"Stock:       {product['stock']} units")
            print(f"Description: {product.get('description', 'N/A')}")
            print("="*80)
            
            # Use enhanced confirmation system
            item_desc = f"{product['name']} (SKU: {product['sku']}, ID: {product_id})"
            confirmed = self.confirm_deletion("Product", item_desc)
            
            if confirmed:
                user = self.auth.get_current_username()
                success = self.product_manager.delete_product(product_id, user)
                if success:
                    print("\n✓ [OK] Product deleted successfully!")
                    print("✓ [INFO] Deletion has been logged for admin review.")
                else:
                    print("\n[X] Deletion failed. Please try again.")
            else:
                print("\n[INFO] Product was NOT deleted. No changes made to inventory.")
                
        except ValueError:
            print("\n[X] Error: Please enter a valid product ID (numeric value).")
        except Exception as e:
            print(f"\n[X] Unexpected error: {str(e)}")
        
        input("\nPress Enter to continue...")

    # ========== Log Management ==========

    def logs_menu(self):
        """View logs (Admin only)."""
        if not self.auth.is_admin():
            print("\n[X] Admin privileges required to view logs.")
            input("\nPress Enter to continue...")
            return
        
        while True:
            self.clear_screen()
            self.print_header("SYSTEM LOGS (ADMIN ONLY)")
            print("\n1. View All Recent Logs")
            print("2. View Deletion Logs")
            print("3. View Logs by User")
            print("0. Back to Main Menu")
            print()
            
            choice = input("Select an option: ").strip()
            
            if choice == '1':
                self.view_all_logs()
            elif choice == '2':
                self.view_deletion_logs()
            elif choice == '3':
                self.view_logs_by_user()
            elif choice == '0':
                break
            else:
                print("Invalid option.")
                input("\nPress Enter to continue...")

    def view_all_logs(self):
        """View all recent logs."""
        self.clear_screen()
        self.print_header("ALL RECENT LOGS")
        
        logs = self.logger.get_recent_logs(50)
        self.logger.display_logs(logs)
        
        input("Press Enter to continue...")

    def view_deletion_logs(self):
        """View deletion logs specifically."""
        self.clear_screen()
        self.print_header("PRODUCT DELETION LOGS")
        
        deletion_logs = self.logger.get_deletion_logs(50)
        
        if not deletion_logs:
            print("\nNo deletion logs found.")
        else:
            print(f"\nShowing {len(deletion_logs)} deletion log(s):\n")
            print("=" * 100)
            print(f"{'Timestamp':<20} {'User':<15} {'Details':<60}")
            print("=" * 100)
            for log in deletion_logs:
                timestamp = log.get('timestamp', 'N/A')[:19]
                user = log.get('user', 'N/A')[:14]
                details = log.get('details', '')[:59]
                print(f"{timestamp:<20} {user:<15} {details:<60}")
            print("=" * 100)
        
        input("\nPress Enter to continue...")

    def view_logs_by_user(self):
        """View logs filtered by username."""
        self.clear_screen()
        self.print_header("LOGS BY USER")
        
        username = self.input_with_prompt("Enter username to filter")
        logs = self.logger.get_logs_by_user(username, 50)
        
        if not logs:
            print(f"\nNo logs found for user: {username}")
        else:
            print(f"\nShowing {len(logs)} log(s) for user '{username}':")
            self.logger.display_logs(logs)
        
        input("Press Enter to continue...")

    # ========== Backup & Restore ==========

    def backup_menu(self):
        """Backup and restore submenu (Admin only)."""
        if not self.auth.is_admin():
            print("\n[X] Admin privileges required for backup operations.")
            input("\nPress Enter to continue...")
            return
        
        while True:
            self.clear_screen()
            self.print_header("BACKUP & RESTORE (ADMIN ONLY)")
            print("\n1. Create Backup")
            print("2. Restore from Backup")
            print("3. List Available Backups")
            print("4. Delete Backup")
            print("0. Back to Main Menu")
            print()
            
            choice = input("Select an option: ").strip()
            
            if choice == '1':
                self.create_backup()
            elif choice == '2':
                self.restore_backup()
            elif choice == '3':
                self.list_backups()
            elif choice == '4':
                self.delete_backup()
            elif choice == '0':
                break
            else:
                print("Invalid option.")
                input("\nPress Enter to continue...")

    def create_backup(self):
        """Create database backup (INV-NF-004)."""
        self.clear_screen()
        self.print_header("CREATE BACKUP")
        
        user = self.auth.get_current_username()
        backup_path = self.backup_manager.create_backup(user)
        
        input("\nPress Enter to continue...")

    def restore_backup(self):
        """Restore from backup."""
        self.clear_screen()
        self.print_header("RESTORE FROM BACKUP")
        
        self.backup_manager.display_backups()
        
        backup_filename = self.input_with_prompt("Enter backup filename to restore")
        
        confirm = input("\n[!] This will replace the current database. Continue? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            user = self.auth.get_current_username()
            self.backup_manager.restore_backup(backup_filename, user)
        else:
            print("Restore cancelled.")
        
        input("\nPress Enter to continue...")

    def list_backups(self):
        """List available backups."""
        self.clear_screen()
        self.print_header("AVAILABLE BACKUPS")
        
        self.backup_manager.display_backups()
        
        input("Press Enter to continue...")

    def delete_backup(self):
        """Delete a backup file."""
        self.clear_screen()
        self.print_header("DELETE BACKUP")
        
        self.backup_manager.display_backups()
        
        backup_filename = self.input_with_prompt("Enter backup filename to delete")
        
        confirm = input(f"\nDelete {backup_filename}? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            user = self.auth.get_current_username()
            self.backup_manager.delete_backup(backup_filename, user)
        else:
            print("Deletion cancelled.")
        
        input("\nPress Enter to continue...")

    def show_help(self):
        """Display help information."""
        self.clear_screen()
        self.print_header("HELP")

        print("\nInventory Management System - User Guide")
        print("\n1. Product Management:")
        print("   - Add new products with SKU, name, price, category, and stock")
        print("   - View all products in a formatted table")
        print("   - Search products by name, SKU, or category")
        print("\nFor more information, please refer to the documentation.")

        input("\nPress Enter to continue...")

    # ========== Order Processing ==========

    def order_menu(self):
        """Display and handle order processing menu."""
        while True:
            self.clear_screen()
            self.print_header("ORDER PROCESSING")

            print("\n1. Create Sales Order")
            print("2. Create Purchase Order")
            print("3. View Sales Orders")
            print("4. View Purchase Orders")
            print("0. Back to Main Menu")
            print()

            choice = input("Select an option: ").strip()

            if choice == '1':
                self.create_sales_order()
            elif choice == '2':
                self.create_purchase_order()
            elif choice == '3':
                self.view_sales_orders()
            elif choice == '4':
                self.view_purchase_orders()
            elif choice == '0':
                break
            else:
                print("\n[!] Invalid option. Please try again.")
                input("\nPress Enter to continue...")

    def create_sales_order(self):
        """Create sales order (INV-F-010, INV-F-011)."""
        self.clear_screen()
        self.print_header("CREATE SALES ORDER")

        try:
            # Get product ID
            product_id_str = input("\nEnter Product ID: ").strip()
            if not product_id_str:
                print("\n[!] Product ID cannot be empty.")
                input("\nPress Enter to continue...")
                return

            try:
                product_id = int(product_id_str)
            except ValueError:
                print("\n[!] Product ID must be a number.")
                input("\nPress Enter to continue...")
                return

            # Get product details
            product = self.product_manager.get_product(product_id)
            if not product:
                print(f"\n[!] Product with ID {product_id} not found.")
                input("\nPress Enter to continue...")
                return

            # Display product information
            print(f"\nProduct: {product['name']}")
            print(f"SKU: {product['sku']}")
            print(f"Price: ${product['price']:.2f}")
            print(f"Available Stock: {product['stock']} units")

            # Get quantity
            quantity_str = input("\nEnter quantity to sell: ").strip()
            if not quantity_str:
                print("\n[!] Quantity cannot be empty.")
                input("\nPress Enter to continue...")
                return

            try:
                quantity = int(quantity_str)
            except ValueError:
                print("\n[!] Quantity must be a number.")
                input("\nPress Enter to continue...")
                return

            if quantity <= 0:
                print("\n[!] Quantity must be positive.")
                input("\nPress Enter to continue...")
                return

            # Check stock availability (INV-F-011)
            if quantity > product['stock']:
                print(f"\n[!] Insufficient stock. Available: {product['stock']}, Requested: {quantity}")
                input("\nPress Enter to continue...")
                return

            # Calculate total
            total_price = product['price'] * quantity

            # Confirm order
            print(f"\nOrder Summary:")
            print(f"Product: {product['name']}")
            print(f"Quantity: {quantity} units")
            print(f"Unit Price: ${product['price']:.2f}")
            print(f"Total Price: ${total_price:.2f}")

            confirm = input("\nConfirm order? (yes/no): ").strip().lower()
            if confirm not in ['yes', 'y']:
                print("\n[!] Order cancelled.")
                input("\nPress Enter to continue...")
                return

            # Create sales order
            user = self.auth.get_current_username() if self.auth.is_authenticated() else "guest"
            order_id = self.order_processor.create_sales_order(product_id, quantity, user)

            if order_id:
                new_stock = product['stock'] - quantity
                print(f"\n[✓] Sales order created successfully!")
                print(f"Order ID: {order_id}")
                print(f"Total: ${total_price:.2f}")
                print(f"Remaining stock: {new_stock} units")
            else:
                print("\n[!] Failed to create sales order. Insufficient stock.")

        except ValueError as e:
            print(f"\n[!] Error: {e}")
        except Exception as e:  # pylint: disable=broad-except
            print(f"\n[!] Unexpected error: {e}")

        input("\nPress Enter to continue...")

    def create_purchase_order(self):
        """Create purchase order (INV-F-012).

        Prompts for product ID, optional supplier ID, quantity and unit price.
        Calls OrderProcessor.create_purchase_order to record the order and update stock.
        """
        self.clear_screen()
        self.print_header("CREATE PURCHASE ORDER")

        try:
            # Product ID
            product_id_str = input("\nEnter Product ID: ").strip()
            if not product_id_str:
                print("\n[!] Product ID cannot be empty.")
                input("\nPress Enter to continue...")
                return

            try:
                product_id = int(product_id_str)
            except ValueError:
                print("\n[!] Product ID must be a number.")
                input("\nPress Enter to continue...")
                return

            product = self.product_manager.get_product(product_id)
            if not product:
                print(f"\n[!] Product with ID {product_id} not found.")
                input("\nPress Enter to continue...")
                return

            # Supplier ID (optional)
            supplier_id_str = input("Enter Supplier ID (optional, press Enter to skip): ").strip()
            supplier_id = None
            if supplier_id_str:
                try:
                    supplier_id = int(supplier_id_str)
                except ValueError:
                    print("\n[!] Supplier ID must be a number if provided. Using 'None'.")
                    supplier_id = None

            # Quantity
            quantity_str = input("Enter quantity to purchase: ").strip()
            if not quantity_str:
                print("\n[!] Quantity cannot be empty.")
                input("\nPress Enter to continue...")
                return

            try:
                quantity = int(quantity_str)
            except ValueError:
                print("\n[!] Quantity must be a number.")
                input("\nPress Enter to continue...")
                return

            if quantity <= 0:
                print("\n[!] Quantity must be positive.")
                input("\nPress Enter to continue...")
                return

            # Unit price
            unit_price_str = input("Enter unit price (e.g., 12.50): ").strip()
            if not unit_price_str:
                print("\n[!] Unit price cannot be empty.")
                input("\nPress Enter to continue...")
                return

            try:
                unit_price = float(unit_price_str)
            except ValueError:
                print("\n[!] Unit price must be a number.")
                input("\nPress Enter to continue...")
                return

            if unit_price < 0:
                print("\n[!] Unit price cannot be negative.")
                input("\nPress Enter to continue...")
                return

            total_price = unit_price * quantity

            # Confirm
            print(f"\nOrder Summary:")
            print(f"Product: {product['name']}")
            print(f"Quantity: {quantity} units")
            print(f"Unit Price: ${unit_price:.2f}")
            print(f"Total Price: ${total_price:.2f}")

            confirm = input("\nConfirm purchase order? (yes/no): ").strip().lower()
            if confirm not in ['yes', 'y']:
                print("\n[!] Purchase order cancelled.")
                input("\nPress Enter to continue...")
                return

            user = self.auth.get_current_username() if self.auth.is_authenticated() else "staff"
            order_id = self.order_processor.create_purchase_order(
                product_id, supplier_id, quantity, unit_price, user
            )

            if order_id:
                new_stock = product['stock'] + quantity
                print(f"\n[✓] Purchase order recorded successfully!")
                print(f"Order ID: {order_id}")
                print(f"Total: ${total_price:.2f}")
                print(f"New stock: {new_stock} units")
            else:
                print("\n[!] Failed to create purchase order.")

        except Exception as e:  # pylint: disable=broad-except
            print(f"\n[!] Unexpected error: {e}")

        input("\nPress Enter to continue...")

    def view_sales_orders(self):
        """View sales orders."""
        self.clear_screen()
        self.print_header("SALES ORDERS")

        orders = self.order_processor.get_sales_orders()
        self.order_processor.display_sales_orders(orders)

        input("\nPress Enter to continue...")

    def view_purchase_orders(self):
        """View purchase orders."""
        self.clear_screen()
        self.print_header("PURCHASE ORDERS")

        orders = self.order_processor.get_purchase_orders()
        self.order_processor.display_purchase_orders(orders)

        input("\nPress Enter to continue...")

    # ========== Reports & Analytics ==========

    def reports_menu(self):
        """Reports and analytics submenu."""
        while True:
            self.clear_screen()
            self.print_header("REPORTS & ANALYTICS")
            print("\n1. Generate Inventory Report")
            print("2. Low Stock Alert")
            print("0. Back to Main Menu")
            print()

            choice = input("Select an option: ").strip()

            if choice == '1':
                self.generate_inventory_report()
            elif choice == '2':
                self.show_low_stock()
            elif choice == '0':
                break
            else:
                print("\n[!] Invalid option. Please try again.")
                input("\nPress Enter to continue...")

    def generate_inventory_report(self):
        """Generate comprehensive inventory report (User Story)."""
        self.clear_screen()
        self.print_header("INVENTORY REPORT")

        print("\nGenerating inventory report...")

        try:
            # Get current user
            user = self.auth.get_current_username()

            # Generate report
            report = self.product_manager.generate_inventory_report(user)

            # Display report
            self.product_manager.display_inventory_report(report)

            # Ask if user wants to save report to file
            print("\n" + "="*100)
            save = input("\nWould you like to save this report to a file? (y/n): ").strip().lower()

            if save == 'y':
                self.save_inventory_report(report)

        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"\n[X] Error generating report: {str(e)}")

        input("\nPress Enter to continue...")

    def save_inventory_report(self, report: dict):
        """Save inventory report to a text file."""
        from datetime import datetime
        import os

        # Create reports directory if it doesn't exist
        reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
        os.makedirs(reports_dir, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"inventory_report_{timestamp}.txt"
        filepath = os.path.join(reports_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write("="*100 + "\n")
                file.write("  INVENTORY REPORT\n")
                file.write(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                file.write("="*100 + "\n\n")

                # Summary section
                file.write("=== SUMMARY ===\n")
                file.write(f"Total Products: {report['total_products']}\n")
                file.write(f"Total Stock Units: {report['total_stock']}\n")
                file.write(f"Total Inventory Value: ${report['total_inventory_value']:.2f}\n")
                file.write(f"Low Stock Items: {report['low_stock_count']}\n\n")

                # Category breakdown
                if report['category_breakdown']:
                    file.write("=== CATEGORY BREAKDOWN ===\n")
                    file.write(f"{'Category':<20} {'Products':<10} {'Stock':<10} {'Value':<15}\n")
                    file.write("-" * 55 + "\n")
                    for category, stats in sorted(report['category_breakdown'].items()):
                        file.write(f"{category:<20} {stats['count']:<10} "
                                  f"{stats['total_stock']:<10} ${stats['total_value']:<14.2f}\n")
                    file.write("\n")

                # Low stock items
                if report['low_stock_items']:
                    file.write("=== LOW STOCK ALERTS ===\n")
                    file.write(f"{'SKU':<12} {'Name':<30} {'Stock':<10} {'Status'}\n")
                    file.write("-" * 70 + "\n")
                    for item in report['low_stock_items']:
                        status = "CRITICAL" if item['stock'] == 0 else "LOW"
                        file.write(f"{item['sku']:<12} {item['name']:<30} "
                                  f"{item['stock']:<10} {status}\n")
                    file.write("\n")

                # All products
                file.write("=== DETAILED INVENTORY ===\n")
                file.write(f"{'ID':<5} {'SKU':<12} {'Name':<25} {'Category':<15} "
                          f"{'Price':<10} {'Stock':<8} {'Value':<12}\n")
                file.write("="*100 + "\n")
                for product in report['all_products']:
                    value = product['price'] * product['stock']
                    file.write(f"{str(product['id']):<5} {product['sku']:<12} "
                              f"{product['name']:<25} {product.get('category', ''):<15} "
                              f"${product['price']:<9.2f} {product['stock']:<8} "
                              f"${value:<11.2f}\n")

            print(f"\n[OK] Report saved successfully to: {filepath}")

        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"\n[X] Error saving report: {str(e)}")

    # ========== Application Control ==========

    def exit_application(self):
        """Exit the application."""
        self.clear_screen()
        print("\nThank you for using the Inventory Management System!")
        print("Goodbye!\n")
        self.running = False

    # ========== Supplier Management ==========

    def supplier_menu(self):
        """Supplier management submenu."""
        while True:
            self.clear_screen()
            self.print_header("SUPPLIER MANAGEMENT")
            print("\n1. Add Supplier")
            print("2. View All Suppliers")
            print("3. Search Suppliers")
            print("4. Update Supplier")
            print("0. Back to Main Menu")

            choice = input("\nEnter choice: ").strip()

            if choice == '1':
                self.add_supplier()
            elif choice == '2':
                self.view_suppliers()
            elif choice == '3':
                self.search_suppliers()
            elif choice == '4':
                self.update_supplier()
            elif choice == '0':
                break

    def view_suppliers(self):
        """View all suppliers (INV-F-021)."""
        self.clear_screen()
        self.print_header("ALL SUPPLIERS")

        suppliers = self.supplier_manager.get_all_suppliers()
        self.supplier_manager.display_suppliers(suppliers)

        input("Press Enter to continue...")

    def add_supplier(self):
        """Add new supplier (INV-F-020)."""
        self.clear_screen()
        self.print_header("ADD NEW SUPPLIER")

        try:
            name = self.input_with_prompt("Supplier Name")
            contact_person = self.input_with_prompt("Contact Person (optional)", required=False)
            email = self.input_with_prompt("Email (optional)", required=False)
            phone = self.input_with_prompt("Phone (optional)", required=False)
            address = self.input_with_prompt("Address (optional)", required=False)

            user = self.auth.get_current_username()
            supplier_id = self.supplier_manager.add_supplier(
                name, contact_person, email, phone, address, user
            )

            print(f"\n[OK] Supplier added successfully! ID: {supplier_id}")
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"\n[X] Error: {str(e)}")

        input("\nPress Enter to continue...")

    def search_suppliers(self):
        """Search suppliers (INV-F-021)."""
        self.clear_screen()
        self.print_header("SEARCH SUPPLIERS")

        search_term = self.input_with_prompt("Enter search term (name/contact/email)")
        suppliers = self.supplier_manager.search_suppliers(search_term)

        print(f"\nFound {len(suppliers)} supplier(s):")
        self.supplier_manager.display_suppliers(suppliers)

        input("Press Enter to continue...")

    def update_supplier(self):
        """Update supplier details."""
        self.clear_screen()
        self.print_header("UPDATE SUPPLIER")

        try:
            supplier_id = int(self.input_with_prompt("Supplier ID"))
            supplier = self.supplier_manager.get_supplier(supplier_id)

            if not supplier:
                print("\n[X] Supplier not found.")
                input("\nPress Enter to continue...")
                return

            print(f"\nCurrent details for: {supplier['name']}")
            print(f"Contact Person: {supplier['contact_person']}")
            print(f"Email: {supplier['email']}")
            print(f"Phone: {supplier['phone']}")
            print(f"Address: {supplier['address']}")

            print("\nEnter new values (press Enter to keep current):")

            updates = {}
            name = input(f"Name [{supplier['name']}]: ").strip()
            if name:
                updates['name'] = name

            contact = input(f"Contact Person [{supplier['contact_person']}]: ").strip()
            if contact:
                updates['contact_person'] = contact

            email_input = input(f"Email [{supplier['email']}]: ").strip()
            if email_input:
                updates['email'] = email_input

            phone = input(f"Phone [{supplier['phone']}]: ").strip()
            if phone:
                updates['phone'] = phone

            address = input(f"Address [{supplier['address']}]: ").strip()
            if address:
                updates['address'] = address

            if updates:
                user = self.auth.get_current_username()
                success = self.supplier_manager.update_supplier(supplier_id, user, **updates)
                if success:
                    print("\n[OK] Supplier updated successfully!")
                else:
                    print("\n[X] Failed to update supplier.")
            else:
                print("\n[!] No changes made.")

        except ValueError:
            print("\n[X] Invalid supplier ID.")
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"\n[X] Error: {str(e)}")

        input("\nPress Enter to continue...")

    # ========== Authentication ==========

    def auth_menu(self):
        """Authentication menu."""
        if self.auth.is_authenticated():
            # Logout
            username = self.auth.get_current_username()
            self.auth.logout()
            print(f"\n[OK] Logged out successfully. Goodbye, {username}!")
            input("\nPress Enter to continue...")
        else:
            # Login
            self.login()

    def login(self):
        """User login."""
        self.clear_screen()
        self.print_header("LOGIN")
        
        username = self.input_with_prompt("Username")
        password = self.input_with_prompt("Password")
        
        if self.auth.login(username, password):
            role = "Admin" if self.auth.is_admin() else "User"
            print(f"\n[OK] Login successful! Welcome, {username} ({role})")
        else:
            print("\n[X] Invalid username or password.")
        
        input("\nPress Enter to continue...")

    # ========== Help ==========

    def show_help(self):
        """Display help information."""
        self.clear_screen()
        self.print_header("HELP & INFORMATION")
        
        print("\nDefault Admin Credentials:")
        print("  Username: admin")
        print("  Password: admin123")
        
        print("\nKey Features:")
        print("  • Product Management: Add, view, search, update, delete products")
        print("  • Supplier Management: Manage supplier information")
        print("  • Order Processing: Create sales and purchase orders")
        print("  • Reports: View inventory, sales, and purchase reports")
        print("  • Backup/Restore: Create encrypted backups (Admin only)")
        print("  • Logging: All admin actions are logged")
        
        print("\nRequirements Met:")
        print("  [OK] INV-F-001 to INV-F-032: All functional requirements")
        print("  [OK] INV-NF-001 to INV-NF-005: All non-functional requirements")
        print("  [OK] PRJ-SEC-001 to PRJ-SEC-005: All security requirements")
        
        input("\n\nPress Enter to continue...")

    # ========== Exit ==========

    def exit_application(self):
        """Exit the application gracefully."""
        self.clear_screen()
        self.print_header("EXIT")
        
        if self.auth.is_authenticated():
            username = self.auth.get_current_username()
            self.auth.logout()
            print(f"\nLogging out {username}...")
        
        print("\nThank you for using the Inventory Management System!")
        print("Goodbye!\n")
        self.running = False


def main():
    """Main entry point for the CLI application."""
    try:
        cli = CLI()
        cli.main_menu()
    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user. Exiting...")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"\n\nFatal error: {str(e)}")
        print("Please contact support if this persists.")
    finally:
        sys.exit(0)


if __name__ == "__main__":
    main()
