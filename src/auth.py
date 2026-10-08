"""
Authentication Module
Handles user authentication and authorization.
Implements PRJ-SEC-001 (Password hashing with salted SHA-256).
Implements INV-NF-003 (Admin-only restricted functions).
"""

import hashlib
from typing import Optional, Dict
from .storage import StorageManager


class AuthManager:
    """Manages authentication operations."""

    # Salt for password hashing (PRJ-SEC-001)
    SALT = "ims_secure_salt_2025"

    def __init__(self, storage: StorageManager = None):
        """
        Initialize auth manager.
        
        Args:
            storage: StorageManager instance (optional, creates new if not provided)
        """
        self.storage = storage or StorageManager()
        self.current_user: Optional[Dict] = None

    def hash_password(self, password: str) -> str:
        """
        Hash password with salt using SHA-256 (PRJ-SEC-001).
        
        Args:
            password: Plain text password
            
        Returns:
            Hexadecimal hash string
        """
        salted_password = password + self.SALT
        return hashlib.sha256(salted_password.encode()).hexdigest()

    def verify_password(self, password: str, password_hash: str) -> bool:
        """
        Verify password against stored hash.
        
        Args:
            password: Plain text password to verify
            password_hash: Stored hash to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        return self.hash_password(password) == password_hash

    def login(self, username: str, password: str) -> bool:
        """
        Authenticate user and set current_user.
        
        Args:
            username: Username to authenticate
            password: Plain text password
            
        Returns:
            True if authentication successful, False otherwise
        """
        user = self.storage.get_user_by_username(username)
        
        if not user:
            return False
        
        if self.verify_password(password, user['password_hash']):
            self.current_user = user
            return True
        
        return False

    def logout(self):
        """Logout current user."""
        self.current_user = None

    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.current_user is not None

    def is_admin(self) -> bool:
        """
        Check if current user is admin (INV-NF-003).
        
        Returns:
            True if current user has admin role, False otherwise
        """
        if not self.current_user:
            return False
        return self.current_user.get('role') == 'admin'

    def get_current_username(self) -> str:
        """Get current user's username."""
        if self.current_user:
            return self.current_user.get('username', 'unknown')
        return 'anonymous'

    def register_user(self, username: str, password: str, role: str = 'user') -> bool:
        """
        Register new user.
        
        Args:
            username: Unique username
            password: Plain text password (will be hashed)
            role: User role ('user' or 'admin')
            
        Returns:
            True if registration successful, False if username exists
        """
        # Check if username already exists
        existing_user = self.storage.get_user_by_username(username)
        if existing_user:
            return False
        
        # Hash password and create user
        password_hash = self.hash_password(password)
        self.storage.add_user(username, password_hash, role)
        return True

    def require_admin(self):
        """
        Raise exception if current user is not admin.
        Used to protect admin-only operations (INV-NF-003).
        
        Raises:
            PermissionError: If user is not admin
        """
        if not self.is_admin():
            raise PermissionError("Admin privileges required for this operation")
