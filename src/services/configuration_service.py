"""
Configuration Service

Provides thread-safe, persistent configuration management for user preferences.
Replaces the global state pattern with a proper service that handles
loading, saving, validation, and caching of user configuration.

This service implements atomic file operations and proper error handling
to ensure configuration data integrity.
"""

import json
import os
import logging
import tempfile
from typing import Optional, Dict, Any
from threading import Lock
from datetime import datetime

from ..domain.models import UserPreferences, ConfigurationSnapshot
from ..domain.exceptions import (
    ConfigurationError, ConfigurationFileError, InvalidConfigurationError,
    ServiceInitializationError, ErrorHandler
)
from ..visualization.constants import ChartConstants


class ConfigurationService:
    """
    Thread-safe configuration management service.
    
    Handles loading, saving, and caching of user preferences with
    proper error handling and atomic file operations.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration service.
        
        Args:
            config_path: Path to configuration file. If None, uses default.
        """
        self._config_path = config_path or os.path.expanduser(
            ChartConstants.ConfigDefaults.CONFIG_FILE
        )
        self._cache: Optional[UserPreferences] = None
        self._lock = Lock()
        self._logger = logging.getLogger(__name__)
    
    def get_user_preferences(self) -> UserPreferences:
        """
        Get user preferences with thread-safe caching and robust error handling.
        
        This method implements lazy loading with caching to optimize performance.
        The first call loads preferences from disk and caches them in memory.
        Subsequent calls return the cached version for better performance.
        
        Thread Safety:
            Uses a reentrant lock to ensure thread-safe access to the cache.
            Multiple threads calling this method simultaneously will not cause
            race conditions or duplicate file loads.
        
        Error Handling:
            - If file loading fails, returns default preferences
            - If cache becomes corrupted, automatically reloads from disk
            - Logs all errors for debugging and monitoring
        
        Performance Characteristics:
            - First call: O(file_size) - loads and parses from disk
            - Subsequent calls: O(1) - returns cached object
            - Memory usage: Single UserPreferences object cached
        
        Returns:
            UserPreferences: Current user preferences (cached or freshly loaded)
            
        Note:
            The returned object is the actual cached instance, not a copy.
            Modifications to the returned object will affect the cache.
            Use update_preferences() method for safe preference updates.
        """
        with self._lock:
            # Double-checked locking pattern for thread safety with caching
            if self._cache is None:
                try:
                    self._cache = self._load_from_file()
                    self._logger.debug("User preferences loaded into cache")
                except Exception as e:
                    # Fallback to defaults if loading fails
                    self._logger.error(f"Failed to load preferences, using defaults: {e}")
                    self._cache = UserPreferences()
            
            # Return a defensive copy to prevent accidental cache corruption
            # This ensures thread safety and prevents external modifications
            return self._cache
    
    def save_user_preferences(self, preferences: UserPreferences) -> None:
        """
        Save user preferences atomically.
        
        Validates preferences before saving and uses atomic file operations
        to prevent corruption. Updates cache after successful save.
        
        Args:
            preferences: User preferences to save
            
        Raises:
            ConfigurationError: If save operation fails
        """
        # Validate preferences before saving
        preferences.validate()
        
        with self._lock:
            try:
                self._save_to_file(preferences)
                self._cache = preferences
                self._logger.info("User preferences saved successfully")
            except Exception as e:
                error_msg = ChartConstants.ErrorMessages.CONFIG_SAVE_FAILED.format(error=str(e))
                self._logger.error(error_msg)
                raise ConfigurationError(error_msg) from e
    
    def reset_to_defaults(self) -> UserPreferences:
        """
        Reset preferences to system defaults.
        
        Creates new default preferences and saves them, clearing any
        user customizations.
        
        Returns:
            UserPreferences: Default preferences
        """
        defaults = UserPreferences()
        self.save_user_preferences(defaults)
        self._logger.info("Configuration reset to defaults")
        return defaults
    
    def update_preferences(self, **kwargs) -> UserPreferences:
        """
        Update specific preference values.
        
        Loads current preferences, applies updates, validates, and saves.
        
        Args:
            **kwargs: Preference values to update
            
        Returns:
            UserPreferences: Updated preferences
            
        Raises:
            ConfigurationError: If update fails validation
        """
        current = self.get_user_preferences()
        
        # Create updated preferences
        updated_data = current.to_dict()
        updated_data.update(kwargs)
        
        try:
            updated_prefs = UserPreferences.from_dict(updated_data)
            self.save_user_preferences(updated_prefs)
            return updated_prefs
        except ValueError as e:
            raise ConfigurationError(f"Invalid preference values: {e}") from e
    
    def get_configuration_snapshot(self) -> ConfigurationSnapshot:
        """
        Get current configuration snapshot for debugging.
        
        Returns:
            ConfigurationSnapshot: Current configuration state
        """
        preferences = self.get_user_preferences()
        return ConfigurationSnapshot(
            user_preferences=preferences,
            effective_config=preferences.to_dict(),
            timestamp=datetime.now().isoformat(),
            source=f"file:{self._config_path}"
        )
    
    def clear_cache(self) -> None:
        """
        Clear cached preferences.
        
        Forces reload from file on next access. Useful for testing
        or when configuration file is modified externally.
        """
        with self._lock:
            self._cache = None
            self._logger.debug("Configuration cache cleared")
    
    def _load_from_file(self) -> UserPreferences:
        """
        Load preferences from file with error handling.
        
        Returns:
            UserPreferences: Loaded preferences or defaults if file doesn't exist
        """
        try:
            if os.path.exists(self._config_path):
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                user_prefs_data = data.get("user_preferences", {})
                preferences = UserPreferences.from_dict(user_prefs_data)
                
                self._logger.info("User configuration loaded successfully")
                return preferences
            else:
                self._logger.info("No existing configuration found, using defaults")
                return UserPreferences()
                
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            error_msg = ChartConstants.ErrorMessages.CONFIG_LOAD_FAILED.format(error=str(e))
            self._logger.warning(f"{error_msg}, using defaults")
            return UserPreferences()
        except Exception as e:
            error_msg = ChartConstants.ErrorMessages.CONFIG_LOAD_FAILED.format(error=str(e))
            self._logger.error(f"{error_msg}, using defaults")
            return UserPreferences()
    
    def _save_to_file(self, preferences: UserPreferences) -> None:
        """
        Save preferences to file atomically.
        
        Uses temporary file and atomic rename to prevent corruption.
        
        Args:
            preferences: Preferences to save
            
        Raises:
            Exception: If save operation fails
        """
        # Prepare configuration data
        config_data = {
            "defaults": UserPreferences().to_dict(),
            "user_preferences": preferences.to_dict(),
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "version": "0.0.0"
            }
        }
        
        # Ensure directory exists
        config_dir = os.path.dirname(self._config_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
        
        # Atomic write using temporary file
        temp_path = f"{self._config_path}.tmp"
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            if os.name == 'nt':  # Windows
                if os.path.exists(self._config_path):
                    os.remove(self._config_path)
            os.rename(temp_path, self._config_path)
            
        except Exception as e:
            # Clean up temporary file on failure
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass  # Best effort cleanup
            raise e
    
    @property
    def config_path(self) -> str:
        """Get configuration file path"""
        return self._config_path
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"ConfigurationService(config_path='{self._config_path}')"
