import os
from pathlib import Path
from typing import Optional
from mnemonic import Mnemonic

class MnemonicManager:

    DEFAULT_MNEMONIC_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "identity", "ic-identity.mne")

    def __init__(self, mnemonic_path: str = DEFAULT_MNEMONIC_PATH, regenerate: bool = False):
        self._mnemonic_path = mnemonic_path
        self._mnemonic = self._read_mnemonic()
        
        if not self._mnemonic or regenerate:
            self._mnemonic = self._generate_mnemonic()
            self._write_mnemonic(self._mnemonic)
        self._seed = self._generate_seed()

    @property
    def mnemonic(self) -> str:
        """Get the mnemonic phrase."""
        return self._mnemonic

    @property
    def seed(self) -> bytes:
        """Get the seed."""
        return self._seed

    def _generate_mnemonic(self) -> str:
        """Generate a new BIP39 mnemonic phrase."""
        mnemo = Mnemonic("english")
        mnemonic_phrase = mnemo.generate(strength=128)  # 12 words
        if not mnemo.check(mnemonic_phrase):
            raise ValueError("Invalid mnemonic phrase")
        return mnemonic_phrase  # 12 words
    
    def _generate_seed(self) -> bytes:
        """Generate a new BIP39 seed."""
        mnemo = Mnemonic("english")
        seed = mnemo.to_seed(self._mnemonic)
        return seed

    def _read_mnemonic(self) -> Optional[str]:
        """
        Read mnemonic from file.
        
        Returns:
            Mnemonic string if file exists and is readable, None otherwise.
        """
        try:
            mnemonic_file = Path(self._mnemonic_path)
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
        
    def _write_mnemonic(self, mnemonic: Optional[str] = None) -> bool:
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
            mnemonic_file = Path(self._mnemonic_path)
            mnemonic_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write mnemonic to file
            with open(mnemonic_file, 'w', encoding='utf-8') as f:
                f.write(mnemonic)
            return True
        except Exception as error:
            print(f"Identity: Error writing mnemonic: {error}")
            return False

