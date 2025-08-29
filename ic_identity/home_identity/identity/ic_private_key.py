from typing import Optional
from .mnemonic import MnemonicManager
from bip32 import BIP32

class ICPrivateKey:
    """
    Internet Computer Identity management.
    
    Handles mnemonic generation, key derivation, and identity creation
    using BIP39/BIP32 standards with Secp256k1 keys.
    """
    
    def __init__(self, regenerate: bool = False):
        self._mnemonic_manager = MnemonicManager(regenerate=regenerate)
        self._mnemonic: Optional[str] = self._mnemonic_manager.mnemonic
        self._seed: Optional[bytes] = self._mnemonic_manager.seed
        self._private_key: Optional[bytes] = self._generate_private_key()
    
    @property
    def mnemonic(self) -> Optional[str]:
        """Get the mnemonic phrase."""
        return self._mnemonic

    @property
    def private_key(self) -> Optional[bytes]:
        """Get the private key."""
        return self._private_key

    
    def _generate_private_key(self) -> bytes:
        """
        Initialize the identity with a mnemonic.
        
        Args:
            mnemonic: Optional mnemonic phrase. If None, generates a new one.
        """
       
        # Derive key using BIP32 path m/44'/223'/0'/0/0 (IC standard)
        bip32 = BIP32.from_seed(self._seed)
        # IC uses coin type 223
        derived_key = bip32.get_privkey_from_path("m/44'/223'/0'/0/0")
        
        return derived_key