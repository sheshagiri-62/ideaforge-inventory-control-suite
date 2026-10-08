"""
Unit tests for order processor module.
Tests INV-F-010, INV-F-011, INV-F-012, INV-F-031.
"""

import pytest
import tempfile
import os
from src.order_processor import OrderProcessor
from src.storage import StorageManager
from src.logger import LogManager
from src.product_manager import ProductManager


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.sqlite')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def storage(temp_db):
    """Create test storage manager."""
    return StorageManager(temp_db)


@pytest.fixture
def logger(storage):
    """Create test logger."""
    return LogManager(storage)


@pytest.fixture
def product_manager(storage, logger):
    """Create test product manager."""
    return ProductManager(storage, logger)


@pytest.fixture
def order_processor(storage, logger, product_manager):
    """Create test order processor."""
    return OrderProcessor(storage, logger, product_manager)


@pytest.fixture
def sample_product(product_manager):
    """Create a sample product for testing."""
    product_id = product_manager.add_product(
        sku='TEST001',
        name='Test Product',
        category='Electronics',
        price=99.99,
        stock=100,
        user='testuser'
    )
    return product_id


# ========== Sales Order Tests (INV-F-010, INV-F-011) ==========

def test_create_sales_order_success(order_processor, sample_product, product_manager):
    """Test successful sales order creation (INV-F-010)."""
    # Create sales order
    order_id = order_processor.create_sales_order(sample_product, 10, 'testuser')

    # Verify order was created
    assert order_id is not None
    assert isinstance(order_id, int)

    # Verify stock was reduced
    product = product_manager.get_product(sample_product)
    assert product['stock'] == 90  # 100 - 10


def test_create_sales_order_insufficient_stock(order_processor, sample_product):
    """Test sales order creation with insufficient stock (INV-F-011)."""
    # Attempt to sell more than available
    order_id = order_processor.create_sales_order(sample_product, 150, 'testuser')

    # Verify order was not created
    assert order_id is None


def test_create_sales_order_exact_stock(order_processor, sample_product, product_manager):
    """Test sales order creation with exact available stock."""
    # Sell entire stock
    order_id = order_processor.create_sales_order(sample_product, 100, 'testuser')

    # Verify order was created
    assert order_id is not None

    # Verify stock is now zero
    product = product_manager.get_product(sample_product)
    assert product['stock'] == 0


def test_create_sales_order_invalid_quantity(order_processor, sample_product):
    """Test sales order creation with invalid quantity."""
    # Zero quantity
    with pytest.raises(ValueError, match="Quantity must be positive"):
        order_processor.create_sales_order(sample_product, 0, 'testuser')

    # Negative quantity
    with pytest.raises(ValueError, match="Quantity must be positive"):
        order_processor.create_sales_order(sample_product, -5, 'testuser')


def test_create_sales_order_product_not_found(order_processor):
    """Test sales order creation with non-existent product."""
    with pytest.raises(ValueError, match="Product with ID 99999 not found"):
        order_processor.create_sales_order(99999, 10, 'testuser')


def test_create_sales_order_multiple_orders(order_processor, sample_product, product_manager):
    """Test creating multiple sales orders for same product."""
    # Create first order
    order_id1 = order_processor.create_sales_order(sample_product, 20, 'testuser')
    assert order_id1 is not None

    # Verify stock after first order
    product = product_manager.get_product(sample_product)
    assert product['stock'] == 80

    # Create second order
    order_id2 = order_processor.create_sales_order(sample_product, 30, 'testuser')
    assert order_id2 is not None
    assert order_id2 != order_id1

    # Verify stock after second order
    product = product_manager.get_product(sample_product)
    assert product['stock'] == 50


def test_create_sales_order_logging(order_processor, sample_product, storage):
    """Test that sales order creation is logged."""
    # Create sales order
    order_id = order_processor.create_sales_order(sample_product, 10, 'testuser')

    # Verify log entry was created
    logs = storage.get_logs(limit=1)
    assert len(logs) > 0
    assert logs[0]['user'] == 'testuser'
    assert logs[0]['action'] == 'CREATE_SALES_ORDER'
    assert 'Test Product' in logs[0]['details']
    assert str(order_id) in logs[0]['details']


# ========== Purchase Order Tests (INV-F-012) ==========

def test_create_purchase_order_success(order_processor, sample_product, product_manager):
    """Test successful purchase order creation (INV-F-012)."""
    # Create purchase order
    order_id = order_processor.create_purchase_order(
        sample_product, 1, 50, 80.0, 'testuser'
    )

    # Verify order was created
    assert order_id is not None
    assert isinstance(order_id, int)

    # Verify stock was increased
    product = product_manager.get_product(sample_product)
    assert product['stock'] == 150  # 100 + 50


def test_create_purchase_order_invalid_quantity(order_processor, sample_product):
    """Test purchase order creation with invalid quantity."""
    # Zero quantity
    with pytest.raises(ValueError, match="Quantity must be positive"):
        order_processor.create_purchase_order(sample_product, 1, 0, 80.0, 'testuser')

    # Negative quantity
    with pytest.raises(ValueError, match="Quantity must be positive"):
        order_processor.create_purchase_order(sample_product, 1, -10, 80.0, 'testuser')


def test_create_purchase_order_invalid_price(order_processor, sample_product):
    """Test purchase order creation with invalid unit price."""
    # Negative price
    with pytest.raises(ValueError, match="Unit price cannot be negative"):
        order_processor.create_purchase_order(sample_product, 1, 50, -10.0, 'testuser')


def test_create_purchase_order_product_not_found(order_processor):
    """Test purchase order creation with non-existent product."""
    with pytest.raises(ValueError, match="Product with ID 99999 not found"):
        order_processor.create_purchase_order(99999, 1, 50, 80.0, 'testuser')


def test_create_purchase_order_logging(order_processor, sample_product, storage):
    """Test that purchase order creation is logged."""
    # Create purchase order
    order_id = order_processor.create_purchase_order(
        sample_product, 1, 50, 80.0, 'testuser'
    )

    # Verify log entry was created
    logs = storage.get_logs(limit=1)
    assert len(logs) > 0
    assert logs[0]['user'] == 'testuser'
    assert logs[0]['action'] == 'CREATE_PURCHASE_ORDER'
    assert 'Test Product' in logs[0]['details']
    assert str(order_id) in logs[0]['details']


# ========== Order Retrieval Tests (INV-F-031) ==========

def test_get_sales_orders_no_filter(order_processor, sample_product):
    """Test retrieving all sales orders without date filter."""
    # Create multiple sales orders
    order_processor.create_sales_order(sample_product, 10, 'testuser')
    order_processor.create_sales_order(sample_product, 20, 'testuser')

    # Retrieve all orders
    orders = order_processor.get_sales_orders()
    assert len(orders) >= 2


def test_get_sales_orders_with_date_filter(order_processor, sample_product):
    """Test retrieving sales orders with date filter."""
    from datetime import datetime, timedelta

    # Create sales order
    order_processor.create_sales_order(sample_product, 10, 'testuser')

    # Get today's date range
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    # Retrieve orders for today
    orders = order_processor.get_sales_orders(
        start_date=today.isoformat(),
        end_date=tomorrow.isoformat()
    )
    assert len(orders) >= 1


def test_get_purchase_orders_no_filter(order_processor, sample_product):
    """Test retrieving all purchase orders without date filter."""
    # Create multiple purchase orders
    order_processor.create_purchase_order(sample_product, 1, 50, 80.0, 'testuser')
    order_processor.create_purchase_order(sample_product, 1, 30, 75.0, 'testuser')

    # Retrieve all orders
    orders = order_processor.get_purchase_orders()
    assert len(orders) >= 2


def test_get_purchase_orders_with_date_filter(order_processor, sample_product):
    """Test retrieving purchase orders with date filter."""
    from datetime import datetime, timedelta

    # Create purchase order
    order_processor.create_purchase_order(sample_product, 1, 50, 80.0, 'testuser')

    # Get today's date range
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    # Retrieve orders for today
    orders = order_processor.get_purchase_orders(
        start_date=today.isoformat(),
        end_date=tomorrow.isoformat()
    )
    assert len(orders) >= 1


# ========== Integration Tests ==========

def test_sales_and_purchase_order_workflow(order_processor, sample_product, product_manager):
    """Test complete workflow of sales and purchase orders."""
    initial_stock = 100

    # Sell some units
    order_processor.create_sales_order(sample_product, 40, 'testuser')
    product = product_manager.get_product(sample_product)
    assert product['stock'] == 60  # 100 - 40

    # Purchase more units
    order_processor.create_purchase_order(sample_product, 1, 80, 90.0, 'testuser')
    product = product_manager.get_product(sample_product)
    assert product['stock'] == 140  # 60 + 80

    # Sell more units
    order_processor.create_sales_order(sample_product, 50, 'testuser')
    product = product_manager.get_product(sample_product)
    assert product['stock'] == 90  # 140 - 50


# ========== Report Tests ==========

def test_get_sales_report_empty(order_processor):
    """Test sales report with no orders."""
    from datetime import datetime, timedelta
    start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    end = datetime.now().strftime('%Y-%m-%d')
    
    report = order_processor.get_sales_report(start, end)
    
    assert report['total_orders'] == 0
    assert report['total_revenue'] == 0.0
    assert report['total_units'] == 0
    assert len(report['orders']) == 0


def test_get_sales_report_with_orders(order_processor, sample_product):
    """Test sales report with orders."""
    from datetime import datetime, timedelta
    
    # Create some sales orders
    order_processor.create_sales_order(sample_product, 10, 'user1')
    order_processor.create_sales_order(sample_product, 20, 'user2')
    
    start = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    end = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    report = order_processor.get_sales_report(start, end)
    
    assert report['total_orders'] == 2
    assert report['total_revenue'] > 2900.0  # Allow for floating point rounding
    assert report['total_units'] == 30
    assert len(report['orders']) == 2


def test_get_purchase_report_empty(order_processor):
    """Test purchase report with no orders."""
    from datetime import datetime, timedelta
    start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    end = datetime.now().strftime('%Y-%m-%d')
    
    report = order_processor.get_purchase_report(start, end)
    
    assert report['total_orders'] == 0
    assert report['total_cost'] == 0.0
    assert report['total_units'] == 0
    assert len(report['orders']) == 0


def test_get_purchase_report_with_orders(order_processor, sample_product):
    """Test purchase report with orders."""
    from datetime import datetime, timedelta
    
    # Create some purchase orders
    order_processor.create_purchase_order(sample_product, 1, 50, 80.0, 'user1')
    order_processor.create_purchase_order(sample_product, 1, 30, 85.0, 'user2')
    
    start = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    end = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    report = order_processor.get_purchase_report(start, end)
    
    assert report['total_orders'] == 2
    assert report['total_cost'] == 6550.0  # (50*80 + 30*85)
    assert report['total_units'] == 80
    assert len(report['orders']) == 2


def test_display_sales_orders(order_processor, sample_product, capsys):
    """Test display sales orders."""
    order_processor.create_sales_order(sample_product, 5, 'testuser')
    orders = order_processor.storage.get_sales_orders()
    
    order_processor.display_sales_orders(orders)
    captured = capsys.readouterr()
    
    # Check for order ID and price (product name might not be in display)
    assert "1" in captured.out  # Order ID
    assert "5" in captured.out  # Quantity
    assert "$" in captured.out  # Price indicator


def test_display_sales_orders_empty(order_processor, capsys):
    """Test display empty sales orders."""
    order_processor.display_sales_orders([])
    captured = capsys.readouterr()
    
    assert "No sales orders found" in captured.out


def test_display_purchase_orders(order_processor, sample_product, capsys):
    """Test display purchase orders."""
    order_processor.create_purchase_order(sample_product, 1, 10, 90.0, 'testuser')
    orders = order_processor.storage.get_purchase_orders()
    
    order_processor.display_purchase_orders(orders)
    captured = capsys.readouterr()
    
    # Check for order ID and prices
    assert "1" in captured.out  # Order ID
    assert "10" in captured.out  # Quantity
    assert "$90.00" in captured.out  # Unit price
    assert "$900.00" in captured.out  # Total price


def test_display_purchase_orders_empty(order_processor, capsys):
    """Test display empty purchase orders."""
    order_processor.display_purchase_orders([])
    captured = capsys.readouterr()
    
    assert "No purchase orders found" in captured.out


def test_sales_report_date_range_filtering(order_processor, sample_product):
    """Test sales report filters by date range correctly."""
    from datetime import datetime, timedelta
    
    # Create order
    order_processor.create_sales_order(sample_product, 10, 'user1')
    
    # Get report for future dates (should be empty)
    future_start = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
    future_end = (datetime.now() + timedelta(days=20)).strftime('%Y-%m-%d')
    
    report = order_processor.get_sales_report(future_start, future_end)
    assert report['total_orders'] == 0
    
    # Get report for past and present (should include order)
    past_start = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
    present_end = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    report = order_processor.get_sales_report(past_start, present_end)
    assert report['total_orders'] == 1


def test_purchase_report_date_range_filtering(order_processor, sample_product):
    """Test purchase report filters by date range correctly."""
    from datetime import datetime, timedelta
    
    # Create order
    order_processor.create_purchase_order(sample_product, 1, 10, 90.0, 'user1')
    
    # Get report for future dates (should be empty)
    future_start = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
    future_end = (datetime.now() + timedelta(days=20)).strftime('%Y-%m-%d')
    
    report = order_processor.get_purchase_report(future_start, future_end)
    assert report['total_orders'] == 0
    
    # Get report for past and present (should include order)
    past_start = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
    present_end = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    report = order_processor.get_purchase_report(past_start, present_end)
    assert report['total_orders'] == 1
