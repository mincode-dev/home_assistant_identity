import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AddonConfig:
    """Configuration settings for the ICP Identity addon"""
    network: str = "mainnet"
    generate_new_identity: bool = False
    canister_endpoints: list = None
    backup_retention_days: int = 30
    log_level: str = "INFO"
    auto_backup_before_regenerate: bool = True
    web_interface_enabled: bool = True
    
    def __post_init__(self):
        if self.canister_endpoints is None:
            self.canister_endpoints = []

class ConfigManager:
    """Manages addon configuration with validation and defaults"""
    
    VALID_NETWORKS = ["mainnet", "testnet", "local"]
    VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR"]
    
    def __init__(self, config_path="/data/options.json"):
        self.config_path = config_path
        self._config = None
        
    def load_config(self) -> AddonConfig:
        """Load and validate configuration from options.json"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    raw_config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
            else:
                logger.warning(f"Configuration file not found: {self.config_path}, using defaults")
                raw_config = {}
                
            # Create config with defaults
            config = AddonConfig(
                network=raw_config.get('network', 'mainnet'),
                generate_new_identity=raw_config.get('generate_new_identity', False),
                canister_endpoints=raw_config.get('canister_endpoints', []),
                backup_retention_days=raw_config.get('backup_retention_days', 30),
                log_level=raw_config.get('log_level', 'INFO'),
                auto_backup_before_regenerate=raw_config.get('auto_backup_before_regenerate', True),
                web_interface_enabled=raw_config.get('web_interface_enabled', True)
            )
            
            # Validate configuration
            self._validate_config(config)
            
            self._config = config
            logger.info(f"Configuration loaded successfully: network={config.network}, log_level={config.log_level}")
            return config
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise ValueError(f"Configuration file contains invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
            
    def _validate_config(self, config: AddonConfig):
        """Validate configuration values"""
        errors = []
        
        # Validate network
        if config.network not in self.VALID_NETWORKS:
            errors.append(f"Invalid network '{config.network}'. Must be one of: {self.VALID_NETWORKS}")
            
        # Validate log level
        if config.log_level not in self.VALID_LOG_LEVELS:
            errors.append(f"Invalid log_level '{config.log_level}'. Must be one of: {self.VALID_LOG_LEVELS}")
            
        # Validate backup retention
        if not 1 <= config.backup_retention_days <= 365:
            errors.append(f"backup_retention_days must be between 1 and 365, got {config.backup_retention_days}")
            
        # Validate canister endpoints format
        if config.canister_endpoints:
            for endpoint in config.canister_endpoints:
                if not isinstance(endpoint, str) or not endpoint.strip():
                    errors.append(f"Invalid canister endpoint: {endpoint}")
                    
        if errors:
            raise ValueError("Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors))
            
    def get_config(self) -> AddonConfig:
        """Get current configuration, loading if necessary"""
        if self._config is None:
            self._config = self.load_config()
        return self._config
        
    def get_network_config(self) -> Dict[str, str]:
        """Get network-specific configuration"""
        config = self.get_config()
        
        network_urls = {
            "mainnet": "https://ic0.app",
            "testnet": "https://testnet.ic0.app",
            "local": "http://localhost:4943"
        }
        
        return {
            "network": config.network,
            "agent_url": network_urls[config.network],
            "is_local": config.network == "local",
            "is_production": config.network == "mainnet"
        }
        
    def setup_logging(self):
        """Setup logging based on configuration"""
        config = self.get_config()
        
        log_level = getattr(logging, config.log_level, logging.INFO)
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            force=True  # Override any existing configuration
        )
        
        logger.info(f"Logging configured: level={config.log_level}")
        
    def get_environment_info(self) -> Dict[str, Any]:
        """Get environment and configuration information"""
        config = self.get_config()
        
        return {
            "addon_version": "1.0.0",
            "config_path": self.config_path,
            "network": config.network,
            "log_level": config.log_level,
            "web_interface_enabled": config.web_interface_enabled,
            "auto_backup_enabled": config.auto_backup_before_regenerate,
            "backup_retention_days": config.backup_retention_days,
            "canister_endpoints_count": len(config.canister_endpoints),
            "supervisor_token_available": bool(os.environ.get('SUPERVISOR_TOKEN')),
            "data_directory": "/data",
            "python_version": os.sys.version,
            "environment_variables": {
                "SUPERVISOR_TOKEN": "***" if os.environ.get('SUPERVISOR_TOKEN') else None,
                "LOG_LEVEL": os.environ.get('LOG_LEVEL', 'Not set')
            }
        } 