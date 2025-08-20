"""
Canister Registry - Manages registered canisters and their metadata.

This module handles persistent storage of canister configurations and
provides the foundation for dynamic endpoint generation.
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime

class CanisterRegistry:
    """Registry for managing canister configurations and metadata."""
    
    def __init__(self, data_path: str = "/data"):
        self.data_path = data_path
        self.registry_file = os.path.join(data_path, "canisters.json")
        self._ensure_data_directory()
    
    def _ensure_data_directory(self):
        """Ensure the data directory exists."""
        os.makedirs(self.data_path, exist_ok=True)
    
    def load_canisters(self) -> Dict[str, Dict]:
        """Load all registered canisters from storage."""
        if not os.path.exists(self.registry_file):
            return {}
        
        try:
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def save_canisters(self, canisters: Dict[str, Dict]):
        """Save canisters to persistent storage."""
        with open(self.registry_file, 'w') as f:
            json.dump(canisters, f, indent=2)
    
    def add_canister(self, canister_id: str, name: str = None, network: str = "mainnet") -> bool:
        """Add a new canister to the registry."""
        canisters = self.load_canisters()
        
        if canister_id in canisters:
            return False  # Already exists
        
        canisters[canister_id] = {
            "name": name or f"canister_{canister_id[:8]}",
            "network": network,
            "added_at": datetime.now().isoformat(),
            "last_used": None,
            "methods": []  # Will be populated from .did file
        }
        
        self.save_canisters(canisters)
        return True
    
    def remove_canister(self, canister_id: str) -> bool:
        """Remove a canister from the registry."""
        canisters = self.load_canisters()
        
        if canister_id not in canisters:
            return False
        
        del canisters[canister_id]
        self.save_canisters(canisters)
        return True
    
    def get_canister(self, canister_id: str) -> Optional[Dict]:
        """Get information about a specific canister."""
        canisters = self.load_canisters()
        return canisters.get(canister_id)
    
    def list_canisters(self) -> List[Dict]:
        """List all registered canisters."""
        canisters = self.load_canisters()
        result = []
        
        for canister_id, info in canisters.items():
            result.append({
                "id": canister_id,
                **info
            })
        
        return result
    
    def update_canister_usage(self, canister_id: str):
        """Update the last used timestamp for a canister."""
        canisters = self.load_canisters()
        
        if canister_id in canisters:
            canisters[canister_id]["last_used"] = datetime.now().isoformat()
            self.save_canisters(canisters)
    
    def update_canister_methods(self, canister_id: str, methods: List[str]):
        """Update the available methods for a canister."""
        canisters = self.load_canisters()
        
        if canister_id in canisters:
            canisters[canister_id]["methods"] = methods
            self.save_canisters(canisters)