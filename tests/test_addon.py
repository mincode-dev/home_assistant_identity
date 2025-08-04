import pytest
import asyncio
import tempfile
import os
import json
from unittest.mock import Mock, patch, AsyncMock
import sys

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from icp_identity import ICPIdentityManager
from ha_integration import HomeAssistantIntegration
from storage import IdentityStorage
from config import ConfigManager, AddonConfig

class TestICPIdentityManager:
    """Test ICP Identity Manager functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = ICPIdentityManager(data_path=self.temp_dir)
        
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_data_directory_creation(self):
        """Test that data directory is created"""
        assert os.path.exists(self.temp_dir)
        
    def test_identity_files_path(self):
        """Test identity file paths are correct"""
        assert self.manager.identity_file.startswith(self.temp_dir)
        assert self.manager.mnemonic_file.startswith(self.temp_dir)
        
    def test_identity_not_exists_initially(self):
        """Test identity doesn't exist initially"""
        assert not self.manager._identity_exists()
        
    @patch('mnemonic.Mnemonic')
    @patch('ic.identity.Identity')
    def test_generate_new_identity(self, mock_identity, mock_mnemonic):
        """Test new identity generation"""
        # Mock mnemonic generation
        mock_mnemo_instance = Mock()
        mock_mnemo_instance.generate.return_value = "test mnemonic phrase"
        mock_mnemo_instance.check.return_value = True
        mock_mnemo_instance.to_seed.return_value = b'0' * 64
        mock_mnemonic.return_value = mock_mnemo_instance
        
        # Mock identity creation
        mock_identity_instance = Mock()
        mock_sender = Mock()
        mock_sender.principal = "test-principal-id"
        mock_sender.public_key = Mock()
        mock_sender.public_key.hex.return_value = "test-public-key-hex"
        mock_identity_instance.sender.return_value = mock_sender
        mock_identity.from_seed.return_value = mock_identity_instance
        
        # Test identity generation
        self.manager._generate_new_identity()
        
        # Verify mnemonic and identity files were created
        assert os.path.exists(self.manager.identity_file)
        assert os.path.exists(self.manager.mnemonic_file)
        
        # Verify identity file content
        with open(self.manager.identity_file, 'r') as f:
            identity_data = json.load(f)
            
        assert identity_data['principal'] == "test-principal-id"
        assert identity_data['public_key'] == "test-public-key-hex"
        assert 'created_at' in identity_data
        
    def test_get_principal_without_identity(self):
        """Test getting principal without initialized identity raises error"""
        with pytest.raises(RuntimeError):
            self.manager.get_principal()

class TestHomeAssistantIntegration:
    """Test Home Assistant integration functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_icp_manager = Mock()
        self.mock_icp_manager.get_identity_info.return_value = {
            "principal": "test-principal",
            "public_key": "test-public-key",
            "network": "testnet",
            "agent_url": "https://testnet.ic0.app",
            "has_mnemonic": True,
            "identity_file": "/test/path"
        }
        self.integration = HomeAssistantIntegration(self.mock_icp_manager)
        
    @patch.dict(os.environ, {'SUPERVISOR_TOKEN': 'test-token'})
    def test_supervisor_token_detection(self):
        """Test supervisor token is detected"""
        integration = HomeAssistantIntegration(self.mock_icp_manager)
        assert integration.supervisor_token == 'test-token'
        
    def test_no_supervisor_token_warning(self):
        """Test warning when no supervisor token"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('src.ha_integration.logger') as mock_logger:
                integration = HomeAssistantIntegration(self.mock_icp_manager)
                mock_logger.warning.assert_called_once()
                
    def test_integration_status(self):
        """Test integration status information"""
        status = self.integration.get_integration_status()
        assert 'supervisor_token_available' in status
        assert 'ha_api_url' in status
        assert 'integration_active' in status

class TestIdentityStorage:
    """Test identity storage functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = IdentityStorage(data_path=self.temp_dir)
        
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_backup_directory_creation(self):
        """Test backup directory is created"""
        assert os.path.exists(self.storage.backup_path)
        
    def test_no_backups_initially(self):
        """Test no backups exist initially"""
        backups = self.storage.list_backups()
        assert len(backups) == 0
        
    def test_get_storage_stats(self):
        """Test storage statistics"""
        stats = self.storage.get_storage_stats()
        assert 'data_path' in stats
        assert 'backup_count' in stats
        assert 'data_size_mb' in stats
        assert 'backup_size_mb' in stats

class TestConfigManager:
    """Test configuration management"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, 'options.json')
        self.config_manager = ConfigManager(config_path=self.config_file)
        
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_load_default_config(self):
        """Test loading default configuration when no file exists"""
        config = self.config_manager.load_config()
        assert config.network == "mainnet"
        assert config.log_level == "INFO"
        assert not config.generate_new_identity
        
    def test_load_custom_config(self):
        """Test loading custom configuration"""
        custom_config = {
            "network": "testnet",
            "log_level": "DEBUG",
            "backup_retention_days": 7
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(custom_config, f)
            
        config = self.config_manager.load_config()
        assert config.network == "testnet"
        assert config.log_level == "DEBUG"
        assert config.backup_retention_days == 7
        
    def test_invalid_network_validation(self):
        """Test validation of invalid network"""
        invalid_config = {"network": "invalid-network"}
        
        with open(self.config_file, 'w') as f:
            json.dump(invalid_config, f)
            
        with pytest.raises(ValueError, match="Invalid network"):
            self.config_manager.load_config()
            
    def test_invalid_log_level_validation(self):
        """Test validation of invalid log level"""
        invalid_config = {"log_level": "INVALID"}
        
        with open(self.config_file, 'w') as f:
            json.dump(invalid_config, f)
            
        with pytest.raises(ValueError, match="Invalid log_level"):
            self.config_manager.load_config()
            
    def test_network_config(self):
        """Test network configuration mapping"""
        config = self.config_manager.load_config()
        network_config = self.config_manager.get_network_config()
        
        assert 'network' in network_config
        assert 'agent_url' in network_config
        assert 'is_local' in network_config
        assert 'is_production' in network_config
        
    def test_environment_info(self):
        """Test environment information gathering"""
        env_info = self.config_manager.get_environment_info()
        
        assert 'addon_version' in env_info
        assert 'network' in env_info
        assert 'log_level' in env_info
        assert 'supervisor_token_available' in env_info

# Integration tests
class TestAddonIntegration:
    """Test addon integration functionality"""
    
    @pytest.mark.asyncio
    async def test_addon_startup_sequence(self):
        """Test the basic addon startup sequence"""
        # This would test the main startup flow
        # Implementation depends on mocking the full startup process
        pass
        
    def test_config_validation_flow(self):
        """Test configuration validation in startup flow"""
        # Test that invalid configurations are caught early
        pass

if __name__ == "__main__":
    # Run basic tests if called directly
    pytest.main([__file__, "-v"]) 