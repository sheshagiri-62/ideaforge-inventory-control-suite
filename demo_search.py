"""
Demo script for Search Products functionality
Shows how the search feature works in your IMS.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage import StorageManager
from src.product_manager import ProductManager
from src.logger import LogManager


def demo_search_products():
    """Demonstrate the search products functionality."""
    
    print("="*80)
    print("  SEARCH PRODUCTS - DEMO")
    print("="*80)
    print()
    
    # Create temporary storage
    import tempfile
    fd, db_path = tempfile.mkstemp(suffix='.sqlite')
    os.close(fd)
    
    try:
        # Initialize managers
        storage = StorageManager(db_path)
        logger = LogManager(storage)
        pm = ProductManager(storage, logger)
        
        # Add sample products
        print("1️⃣  Adding sample products...")
        pm.add_product("LAPTOP001", "Gaming Laptop", 1299.99, "Electronics", 10, "High-performance gaming")
        pm.add_product("LAPTOP002", "Business Laptop", 999.99, "Electronics", 15, "For professionals")
        pm.add_product("MOUSE001", "Wireless Mouse", 29.99, "Accessories", 50, "Ergonomic design")
        pm.add_product("CHAIR001", "Office Chair", 199.99, "Furniture", 20, "Comfortable seating")
        pm.add_product("DESK001", "Standing Desk", 399.99, "Furniture", 8, "Adjustable height")
        print("   ✅ Added 5 products\n")
        
        # Demo 1: Search by name
        print("2️⃣  DEMO: Search by NAME")
        print("   Search term: 'Laptop'")
        results = pm.search_products("Laptop")
        print(f"   Found {len(results)} results:")
        for p in results:
            print(f"     - {p['sku']}: {p['name']} (${p['price']:.2f})")
        print()
        
        # Demo 2: Search by SKU
        print("3️⃣  DEMO: Search by SKU")
        print("   Search term: 'MOUSE'")
        results = pm.search_products("MOUSE")
        print(f"   Found {len(results)} results:")
        for p in results:
            print(f"     - {p['sku']}: {p['name']} (${p['price']:.2f})")
        print()
        
        # Demo 3: Search by category
        print("4️⃣  DEMO: Search by CATEGORY")
        print("   Search term: 'Furniture'")
        results = pm.search_products("Furniture")
        print(f"   Found {len(results)} results:")
        for p in results:
            print(f"     - {p['sku']}: {p['name']} (${p['price']:.2f})")
        print()
        
        # Demo 4: Partial match
        print("5️⃣  DEMO: Partial match")
        print("   Search term: 'Office'")
        results = pm.search_products("Office")
        print(f"   Found {len(results)} results:")
        for p in results:
            print(f"     - {p['sku']}: {p['name']} (${p['price']:.2f})")
        print()
        
        # Demo 5: Case insensitive
        print("6️⃣  DEMO: Case-insensitive search")
        print("   Search term: 'laptop' (lowercase)")
        results = pm.search_products("laptop")
        print(f"   Found {len(results)} results:")
        for p in results:
            print(f"     - {p['sku']}: {p['name']} (${p['price']:.2f})")
        print()
        
        # Demo 6: No results
        print("7️⃣  DEMO: No results found")
        print("   Search term: 'Tablet'")
        results = pm.search_products("Tablet")
        print(f"   Found {len(results)} results")
        if len(results) == 0:
            print("     No products found matching 'Tablet'")
        print()
        
        print("="*80)
        print("✅ DEMO COMPLETED SUCCESSFULLY!")
        print("="*80)
        print()
        print("Key Features Demonstrated:")
        print("  ✅ Search by product name")
        print("  ✅ Search by SKU")
        print("  ✅ Search by category")
        print("  ✅ Partial text matching")
        print("  ✅ Case-insensitive search")
        print("  ✅ Handles no results gracefully")
        print()
        
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


if __name__ == "__main__":
    demo_search_products()
