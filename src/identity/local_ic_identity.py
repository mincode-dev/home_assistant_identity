"""
Local IC Identity management with file-based mnemonic storage.

This module handles local identity persistence, closely mirroring 
the TypeScript LocalICIdentity implementation.
"""

import os
import asyncio
from pathlib import Path
from typing import Optional

from .ic_identity import ICIdentity, create_ic_identity, generate_mnemonic


class LocalICIdentity:
    """
    Local IC Identity with file-based mnemonic storage.
    
    Manages identity persistence by storing mnemonic phrases in local files,
    similar to the TypeScript implementation.
    """
    
    # Default path for mnemonic storage
    DEFAULT_MNEMONIC_PATH = os.path.join(
        os.path.dirname(__file__), "..", "data", "ic-identity.mne"
    )
    
    def __init__(self, mnemonic_path: Optional[str] = None):
        """
        Initialize LocalICIdentity.
        
        Args:
            mnemonic_path: Optional custom path for mnemonic file.
        """
        self.mnemonic_path = mnemonic_path or self.DEFAULT_MNEMONIC_PATH
        self._ic_identity: Optional[ICIdentity] = None
    
    @property
    def identity(self) -> Optional[object]:
        """Get the identity object (compatible with actor controller)."""
        return self._ic_identity.identity if self._ic_identity else None
    
    @property
    def ic_identity(self) -> Optional[ICIdentity]:
        """Get the IC identity instance."""
        return self._ic_identity
    
    async def initialize(self) -> None:
        """
        Initialize the local identity.
        
        Reads existing mnemonic from file or generates a new one.
        """
        mnemonic = self.read_mnemonic()
        
        if not mnemonic:
            # Generate new mnemonic and save it
            new_mnemonic = generate_mnemonic()
            self.write_mnemonic(new_mnemonic)
            mnemonic = self.read_mnemonic()
        
        if not mnemonic:
            self._ic_identity = None
            return
        
        # Create IC identity with the mnemonic
        self._ic_identity = await create_ic_identity(mnemonic)
    
    def read_mnemonic(self) -> Optional[str]:
        """
        Read mnemonic from file.
        
        Returns:
            Mnemonic string if file exists and is readable, None otherwise.
        """
        try:
            mnemonic_file = Path(self.mnemonic_path)
            if mnemonic_file.exists():
                with open(mnemonic_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    
                    # Skip empty files or files with only comments
                    if not content or content.startswith('#'):
                        return None
                    
                    # Filter out comment lines and get the first valid line
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            return line
                    
                    return None
            return None
        except Exception as error:
            print(f"Identity: Error reading mnemonic: {error}")
            return None
    
    def write_mnemonic(self, mnemonic: Optional[str] = None) -> bool:
        """
        Write mnemonic to file.
        
        Args:
            mnemonic: Mnemonic phrase to write. If None, does nothing.
        
        Returns:
            True if successful, False otherwise.
        """
        if not mnemonic:
            return False
        
        try:
            # Ensure directory exists
            mnemonic_file = Path(self.mnemonic_path)
            mnemonic_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write mnemonic to file
            with open(mnemonic_file, 'w', encoding='utf-8') as f:
                f.write(mnemonic)
            return True
        except Exception as error:
            print(f"Identity: Error writing mnemonic: {error}")
            return False
    
    def get_principal_id(self) -> Optional[str]:
        """Get the principal ID of the current identity."""
        if self._ic_identity:
            return self._ic_identity.principal_id
        return None
    
    def get_mnemonic(self) -> Optional[str]:
        """Get the mnemonic phrase of the current identity."""
        if self._ic_identity:
            return self._ic_identity.mnemonic
        return None


async def create_local_identity(mnemonic_path: Optional[str] = None) -> LocalICIdentity:
    """
    Create and initialize a LocalICIdentity.
    
    Args:
        mnemonic_path: Optional custom path for mnemonic file.
    
    Returns:
        Initialized LocalICIdentity instance.
    """
    local_identity = LocalICIdentity(mnemonic_path)
    await local_identity.initialize()
    return local_identity