import os
import json
import shutil
from datetime import datetime
from typing import Dict, Optional

class IdentityStorage:
    def __init__(self, data_path="/data"):
        self.data_path = data_path
        self.backup_path = os.path.join(data_path, "backups")
        self.config_file = os.path.join(data_path, "storage_config.json")
        
        # Ensure backup directory exists
        os.makedirs(self.backup_path, exist_ok=True)
        
    def create_backup(self, identity_file: str, mnemonic_file: str) -> str:
        """Create a backup of identity files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(self.backup_path, f"identity_backup_{timestamp}")
        
        os.makedirs(backup_dir, exist_ok=True)
        
        # Copy identity files to backup
        if os.path.exists(identity_file):
            shutil.copy2(identity_file, os.path.join(backup_dir, "icp_identity.json"))
        
        if os.path.exists(mnemonic_file):
            shutil.copy2(mnemonic_file, os.path.join(backup_dir, "mnemonic.enc"))
            
        # Create backup metadata
        backup_info = {
            "created_at": datetime.now().isoformat(),
            "files": ["icp_identity.json", "mnemonic.enc"],
            "backup_path": backup_dir
        }
        
        with open(os.path.join(backup_dir, "backup_info.json"), 'w') as f:
            json.dump(backup_info, f, indent=2)
            
        print(f"✅ Created backup: {backup_dir}")
        return backup_dir
        
    def list_backups(self) -> list:
        """List all available backups"""
        backups = []
        
        if not os.path.exists(self.backup_path):
            return backups
            
        for item in os.listdir(self.backup_path):
            backup_dir = os.path.join(self.backup_path, item)
            backup_info_file = os.path.join(backup_dir, "backup_info.json")
            
            if os.path.isdir(backup_dir) and os.path.exists(backup_info_file):
                try:
                    with open(backup_info_file, 'r') as f:
                        backup_info = json.load(f)
                    backups.append(backup_info)
                except json.JSONDecodeError:
                    continue
                    
        return sorted(backups, key=lambda x: x["created_at"], reverse=True)
        
    def restore_backup(self, backup_path: str, target_identity_file: str, target_mnemonic_file: str) -> bool:
        """Restore identity from backup"""
        try:
            backup_identity = os.path.join(backup_path, "icp_identity.json")
            backup_mnemonic = os.path.join(backup_path, "mnemonic.enc")
            
            if os.path.exists(backup_identity):
                shutil.copy2(backup_identity, target_identity_file)
                
            if os.path.exists(backup_mnemonic):
                shutil.copy2(backup_mnemonic, target_mnemonic_file)
                
            print(f"✅ Restored identity from backup: {backup_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to restore backup: {e}")
            return False
            
    def cleanup_old_backups(self, keep_count: int = 5):
        """Remove old backups, keeping only the most recent ones"""
        backups = self.list_backups()
        
        if len(backups) <= keep_count:
            return
            
        # Remove oldest backups
        for backup in backups[keep_count:]:
            backup_dir = backup["backup_path"]
            try:
                shutil.rmtree(backup_dir)
                print(f"🗑️  Removed old backup: {backup_dir}")
            except Exception as e:
                print(f"❌ Failed to remove backup {backup_dir}: {e}")
                
    def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        stats = {
            "data_path": self.data_path,
            "backup_count": len(self.list_backups()),
            "data_size_mb": 0,
            "backup_size_mb": 0
        }
        
        # Calculate data directory size
        if os.path.exists(self.data_path):
            stats["data_size_mb"] = self._get_directory_size(self.data_path) / (1024 * 1024)
            
        # Calculate backup directory size
        if os.path.exists(self.backup_path):
            stats["backup_size_mb"] = self._get_directory_size(self.backup_path) / (1024 * 1024)
            
        return stats
        
    def _get_directory_size(self, path: str) -> int:
        """Calculate total size of directory in bytes"""
        total_size = 0
        
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
                    
        return total_size 