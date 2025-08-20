"""
Core Module

Contains core functionality including configuration management and storage utilities.
"""

from .config import ConfigManager, AddonConfig
from .storage import IdentityStorage
from .canister_registry import CanisterRegistry

__all__ = ['ConfigManager', 'AddonConfig', 'IdentityStorage', 'CanisterRegistry']