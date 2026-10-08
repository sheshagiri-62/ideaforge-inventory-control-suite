"""
Unit tests for logger module.
Tests logging and audit trail functionality.
"""

import pytest
import tempfile
import os
from src.logger import LogManager
from src.storage import StorageManager


class TestLogger:
    """Test logger module."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.sqlite')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def logger(self, temp_db):
        """Create logger with temporary database."""
        storage = StorageManager(temp_db)
        return LogManager(storage)

    def test_logger_init(self, logger):
        """Test LogManager initialization."""
        assert logger.storage is not None

    def test_log_action(self, logger):
        """Test logging an action."""
        logger.log_action("testuser", "TEST_ACTION", "Test details")
        
        logs = logger.get_recent_logs(limit=1)
        assert len(logs) == 1
        assert logs[0]['user'] == "testuser"
        assert logs[0]['action'] == "TEST_ACTION"
        assert logs[0]['details'] == "Test details"

    def test_get_recent_logs(self, logger):
        """Test retrieving recent logs."""
        logger.log_action("user1", "ACTION1", "Details 1")
        logger.log_action("user2", "ACTION2", "Details 2")
        logger.log_action("user3", "ACTION3", "Details 3")
        
        logs = logger.get_recent_logs(limit=2)
        assert len(logs) == 2

    def test_get_logs_by_user(self, logger):
        """Test filtering logs by user."""
        logger.log_action("alice", "LOGIN", "Logged in")
        logger.log_action("bob", "LOGOUT", "Logged out")
        logger.log_action("alice", "ADD_PRODUCT", "Added product")
        
        alice_logs = logger.get_logs_by_user("alice")
        assert len(alice_logs) == 2
        assert all(log['user'] == "alice" for log in alice_logs)

    def test_get_logs_by_action(self, logger):
        """Test filtering logs by action."""
        logger.log_action("user1", "ADD_PRODUCT", "Added SKU001")
        logger.log_action("user2", "DELETE_PRODUCT", "Deleted SKU002")
        logger.log_action("user3", "ADD_PRODUCT", "Added SKU003")
        
        add_logs = logger.get_logs_by_action("ADD_PRODUCT")
        assert len(add_logs) == 2

    def test_format_log_entry(self, logger):
        """Test log entry formatting."""
        log = {
            'timestamp': '2025-10-31 12:00:00',
            'user': 'testuser',
            'action': 'TEST_ACTION',
            'details': 'Test details'
        }
        
        formatted = logger.format_log_entry(log)
        assert '2025-10-31 12:00:00' in formatted
        assert 'testuser' in formatted
        assert 'TEST_ACTION' in formatted
        assert 'Test details' in formatted

    def test_format_log_entry_without_details(self, logger):
        """Test log entry formatting without details."""
        log = {
            'timestamp': '2025-10-31 12:00:00',
            'user': 'testuser',
            'action': 'TEST_ACTION',
            'details': ''
        }
        
        formatted = logger.format_log_entry(log)
        assert '2025-10-31 12:00:00' in formatted
        assert 'testuser' in formatted
        assert 'TEST_ACTION' in formatted

    def test_display_logs_empty(self, logger, capsys):
        """Test displaying empty logs."""
        logger.display_logs([])
        captured = capsys.readouterr()
        assert "No logs found" in captured.out

    def test_display_logs_with_entries(self, logger, capsys):
        """Test displaying logs with entries."""
        logger.log_action("user1", "ACTION1", "Details 1")
        logs = logger.get_recent_logs(limit=5)

        logger.display_logs(logs)
        captured = capsys.readouterr()
        # Just check that the log entry details are displayed
        assert "user1" in captured.out
        assert "ACTION1" in captured.out

    # ========== Deletion Logging Tests ==========

    def test_get_deletion_logs(self, logger):
        """Test retrieving deletion logs specifically."""
        logger.log_action("admin", "ADD_PRODUCT", "Added product SKU001")
        logger.log_action("admin", "DELETE_PRODUCT", "Deleted product SKU001")
        logger.log_action("user", "UPDATE_PRODUCT", "Updated product SKU002")
        logger.log_action("admin", "DELETE_PRODUCT", "Deleted product SKU003")
        
        deletion_logs = logger.get_deletion_logs(limit=10)
        
        # Should have 2 deletion logs
        assert len(deletion_logs) == 2
        assert all(log['action'] == "DELETE_PRODUCT" for log in deletion_logs)

    def test_deletion_logs_empty(self, logger):
        """Test retrieving deletion logs when none exist."""
        logger.log_action("user", "ADD_PRODUCT", "Added product")
        logger.log_action("user", "UPDATE_PRODUCT", "Updated product")
        
        deletion_logs = logger.get_deletion_logs(limit=10)
        
        assert len(deletion_logs) == 0

    def test_deletion_logs_contain_required_info(self, logger):
        """Test that deletion logs contain all required information."""
        logger.log_action(
            "admin_user",
            "DELETE_PRODUCT",
            "Deleted product: Test Product (SKU: TEST001, ID: 42)"
        )
        
        deletion_logs = logger.get_deletion_logs(limit=1)
        
        assert len(deletion_logs) == 1
        log = deletion_logs[0]
        
        # Check required fields
        assert 'user' in log
        assert 'timestamp' in log
        assert 'action' in log
        assert 'details' in log
        
        # Check values
        assert log['user'] == "admin_user"
        assert log['action'] == "DELETE_PRODUCT"
        assert "Test Product" in log['details']
        assert "TEST001" in log['details']
        assert "42" in log['details']

    def test_deletion_logs_ordered_by_time(self, logger):
        """Test that deletion logs are ordered by most recent first."""
        logger.log_action("admin", "DELETE_PRODUCT", "Deleted product A")
        logger.log_action("admin", "DELETE_PRODUCT", "Deleted product B")
        logger.log_action("admin", "DELETE_PRODUCT", "Deleted product C")
        
        deletion_logs = logger.get_deletion_logs(limit=10)
        
        # Most recent should be first
        assert "product C" in deletion_logs[0]['details']
        assert "product B" in deletion_logs[1]['details']
        assert "product A" in deletion_logs[2]['details']

    def test_deletion_logs_limit_works(self, logger):
        """Test that limit parameter works for deletion logs."""
        # Add 5 deletion logs
        for i in range(5):
            logger.log_action("admin", "DELETE_PRODUCT", f"Deleted product {i}")
        
        deletion_logs = logger.get_deletion_logs(limit=3)
        
        assert len(deletion_logs) == 3

    def test_deletion_logs_show_different_users(self, logger):
        """Test that deletion logs can show different users who deleted products."""
        logger.log_action("admin1", "DELETE_PRODUCT", "Deleted product A")
        logger.log_action("admin2", "DELETE_PRODUCT", "Deleted product B")
        logger.log_action("manager", "DELETE_PRODUCT", "Deleted product C")
        
        deletion_logs = logger.get_deletion_logs(limit=10)
        
        users = [log['user'] for log in deletion_logs]
        assert "admin1" in users
        assert "admin2" in users
        assert "manager" in users
