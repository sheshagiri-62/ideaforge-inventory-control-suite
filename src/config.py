"""
Configuration Module
Handles application configuration settings.
Provides centralized configuration for paths, thresholds, and security keys.
"""

import os
from pathlib import Path
from cryptography.fernet import Fernet

# Base directory (project root)
BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration
DB_PATH = os.path.join(BASE_DIR, "data", "database.sqlite")

# Backup configuration
BACKUP_PATH = os.path.join(BASE_DIR, "backups")

# Reports configuration
REPORTS_PATH = os.path.join(BASE_DIR, "reports")

# Low stock threshold (INV-F-032)
LOW_STOCK_THRESHOLD = 5

# Encryption key for backups (PRJ-SEC-002)
# In production, this should be stored securely (env variable, key vault)
# For this project, we generate/load a key file
KEY_FILE = os.path.join(BASE_DIR, "data", ".encryption_key")


def get_encryption_key():
    """
    Get or generate encryption key for backup encryption.
    Returns bytes key for Fernet encryption.
    """
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'rb') as f:
            return f.read()
    else:
        # Generate new key
        key = Fernet.generate_key()
        # Ensure data directory exists
        os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)
        with open(KEY_FILE, 'wb') as f:
            f.write(key)
        # Set restrictive permissions (PRJ-SEC-005)
        try:
            os.chmod(KEY_FILE, 0o600)  # Read/write for owner only
        except Exception:
            pass  # Windows may not support chmod
        return key


ENCRYPTION_KEY = get_encryption_key()


class ConfigManager:
    """Manages application configuration."""

    def __init__(self):
        """Initialize config manager."""
        self.db_path = DB_PATH
        self.backup_path = BACKUP_PATH
        self.reports_path = REPORTS_PATH
        self.low_stock_threshold = LOW_STOCK_THRESHOLD
        self.encryption_key = ENCRYPTION_KEY

    def get_config(self, key):
        """Get configuration value by key."""
        config_map = {
            'db_path': self.db_path,
            'backup_path': self.backup_path,
            'reports_path': self.reports_path,
            'low_stock_threshold': self.low_stock_threshold,
            'encryption_key': self.encryption_key
        }
        return config_map.get(key)
