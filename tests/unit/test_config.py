"""
Unit tests for config module.
Tests configuration management functionality.
"""

import pytest
import os
from src.config import ConfigManager, DB_PATH, BACKUP_PATH, REPORTS_PATH, LOW_STOCK_THRESHOLD


class TestConfig:
    """Test configuration module."""

    def test_config_constants(self):
        """Test that configuration constants are defined."""
        assert DB_PATH is not None
        assert BACKUP_PATH is not None
        assert REPORTS_PATH is not None
        assert LOW_STOCK_THRESHOLD == 5

    def test_config_manager_init(self):
        """Test ConfigManager initialization."""
        config = ConfigManager()
        
        assert config.db_path is not None
        assert config.backup_path is not None
        assert config.reports_path is not None
        assert config.low_stock_threshold == 5
        assert config.encryption_key is not None

    def test_config_manager_get_config(self):
        """Test getting configuration values."""
        config = ConfigManager()
        
        assert config.get_config('db_path') == config.db_path
        assert config.get_config('backup_path') == config.backup_path
        assert config.get_config('reports_path') == config.reports_path
        assert config.get_config('low_stock_threshold') == 5
        assert config.get_config('encryption_key') is not None
        assert config.get_config('nonexistent') is None

    def test_config_paths_exist(self):
        """Test that configuration creates necessary directories."""
        config = ConfigManager()
        
        # Paths should be strings
        assert isinstance(config.db_path, str)
        assert isinstance(config.backup_path, str)
        assert isinstance(config.reports_path, str)

    def test_config_encryption_key_format(self):
        """Test encryption key format."""
        config = ConfigManager()
        
        assert isinstance(config.encryption_key, bytes)
        assert len(config.encryption_key) > 0

    def test_config_threshold_value(self):
        """Test low stock threshold value."""
        config = ConfigManager()
        
        assert config.low_stock_threshold > 0
        assert isinstance(config.low_stock_threshold, int)

    def test_db_path_format(self):
        """Test database path format."""
        assert DB_PATH.endswith('.db') or DB_PATH.endswith('.sqlite')
        assert 'data' in DB_PATH or 'database' in DB_PATH.lower()

    def test_backup_path_format(self):
        """Test backup path format."""
        assert 'backup' in BACKUP_PATH.lower()

    def test_reports_path_format(self):
        """Test reports path format."""
        assert 'report' in REPORTS_PATH.lower()

    def test_config_manager_multiple_instances(self):
        """Test multiple ConfigManager instances have same config."""
        config1 = ConfigManager()
        config2 = ConfigManager()
        
        assert config1.db_path == config2.db_path
        assert config1.backup_path == config2.backup_path
        assert config1.low_stock_threshold == config2.low_stock_threshold
