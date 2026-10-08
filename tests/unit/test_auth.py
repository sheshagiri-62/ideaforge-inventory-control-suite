"""
Unit tests for authentication module.
Tests PRJ-SEC-001 (password hashing).
"""

import pytest
import tempfile
import os
from src.auth import AuthManager
from src.storage import StorageManager


class TestAuthManager:
    """Test authentication manager."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.sqlite')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def auth_manager(self, temp_db):
        """Create auth manager with temporary database."""
        storage = StorageManager(temp_db)
        return AuthManager(storage)

    def test_hash_password(self, auth_manager):
        """Test password hashing (PRJ-SEC-001)."""
        password = "test123"
        hashed = auth_manager.hash_password(password)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != password
        assert len(hashed) == 64  # SHA-256 produces 64 hex characters

    def test_hash_password_consistency(self, auth_manager):
        """Test that same password produces same hash."""
        password = "test123"
        hash1 = auth_manager.hash_password(password)
        hash2 = auth_manager.hash_password(password)
        
        assert hash1 == hash2

    def test_verify_password_correct(self, auth_manager):
        """Test password verification with correct password."""
        password = "test123"
        hashed = auth_manager.hash_password(password)
        
        assert auth_manager.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self, auth_manager):
        """Test password verification with incorrect password."""
        password = "test123"
        wrong_password = "wrong456"
        hashed = auth_manager.hash_password(password)
        
        assert auth_manager.verify_password(wrong_password, hashed) is False

    def test_login_success(self, auth_manager):
        """Test successful login with admin credentials."""
        # Default admin user: username=admin, password=admin123
        success = auth_manager.login("admin", "admin123")
        
        assert success is True
        assert auth_manager.is_authenticated() is True
        assert auth_manager.get_current_username() == "admin"

    def test_login_failure_wrong_password(self, auth_manager):
        """Test login failure with wrong password."""
        success = auth_manager.login("admin", "wrongpassword")
        
        assert success is False
        assert auth_manager.is_authenticated() is False

    def test_login_failure_wrong_username(self, auth_manager):
        """Test login failure with non-existent username."""
        success = auth_manager.login("nonexistent", "password")
        
        assert success is False
        assert auth_manager.is_authenticated() is False

    def test_logout(self, auth_manager):
        """Test logout functionality."""
        auth_manager.login("admin", "admin123")
        assert auth_manager.is_authenticated() is True
        
        auth_manager.logout()
        assert auth_manager.is_authenticated() is False
        assert auth_manager.current_user is None

    def test_is_admin_true(self, auth_manager):
        """Test is_admin returns True for admin user (INV-NF-003)."""
        auth_manager.login("admin", "admin123")
        
        assert auth_manager.is_admin() is True

    def test_is_admin_false_not_authenticated(self, auth_manager):
        """Test is_admin returns False when not authenticated."""
        assert auth_manager.is_admin() is False

    def test_register_user_success(self, auth_manager):
        """Test user registration."""
        success = auth_manager.register_user("newuser", "password123", "user")
        
        assert success is True
        
        # Verify user can login
        login_success = auth_manager.login("newuser", "password123")
        assert login_success is True

    def test_register_user_duplicate_username(self, auth_manager):
        """Test registration fails for duplicate username."""
        auth_manager.register_user("testuser", "password123")
        
        # Try to register same username again
        success = auth_manager.register_user("testuser", "password456")
        
        assert success is False

    def test_require_admin_success(self, auth_manager):
        """Test require_admin succeeds for admin user."""
        auth_manager.login("admin", "admin123")
        
        try:
            auth_manager.require_admin()
        except PermissionError:
            pytest.fail("require_admin raised PermissionError for admin user")

    def test_require_admin_failure(self, auth_manager):
        """Test require_admin raises PermissionError for non-admin."""
        auth_manager.register_user("regular", "password123", "user")
        auth_manager.login("regular", "password123")
        
        with pytest.raises(PermissionError):
            auth_manager.require_admin()

    def test_get_current_username_authenticated(self, auth_manager):
        """Test get_current_username when authenticated."""
        auth_manager.login("admin", "admin123")
        
        assert auth_manager.get_current_username() == "admin"

    def test_get_current_username_not_authenticated(self, auth_manager):
        """Test get_current_username when not authenticated."""
        assert auth_manager.get_current_username() == "anonymous"
        username = auth_manager.get_current_username()
        
        assert username == "anonymous"

    def test_get_current_username_when_logged_in(self, auth_manager):
        """Test getting current username when logged in."""
        # Login with admin credentials
        auth_manager.login("admin", "admin123")
        
        username = auth_manager.get_current_username()
        
        assert username == "admin"

    def test_auth_manager_with_none_storage(self):
        """Test AuthManager can be initialized with None storage."""
        # AuthManager now creates a StorageManager if None is passed
        auth_manager = AuthManager(None)
        
        assert auth_manager.storage is not None
        assert auth_manager.current_user is None

    def test_current_user_can_be_set(self, auth_manager):
        """Test that current_user can be set via login."""
        assert auth_manager.current_user is None
        
        # Login with admin credentials
        auth_manager.login("admin", "admin123")
        
        assert auth_manager.current_user is not None
        assert auth_manager.is_authenticated() is True

    def test_current_user_can_be_cleared(self, auth_manager):
        """Test that current_user can be cleared via logout."""
        auth_manager.login("admin", "admin123")
        assert auth_manager.is_authenticated() is True
        
        auth_manager.logout()
        
        assert auth_manager.current_user is None
        assert auth_manager.is_authenticated() is False

    def test_multiple_username_changes(self, auth_manager):
        """Test changing username multiple times via login."""
        # Create a second user
        auth_manager.register_user("user1", "password123", "user")
        auth_manager.login("user1", "password123")
        assert auth_manager.get_current_username() == "user1"
        
        # Logout and login as different user
        auth_manager.logout()
        auth_manager.register_user("user2", "password456", "user")
        auth_manager.login("user2", "password456")
        assert auth_manager.get_current_username() == "user2"
        
        auth_manager.current_user = None
        assert auth_manager.get_current_username() == "anonymous"
