"""
IC Identity management using BIP39 mnemonics and Secp256k1 keys.

This module provides identity creation and management for Internet Computer
interactions, closely mirroring the TypeScript implementation.
"""

import os
import hashlib
from typing import Optional, Union
from mnemonic import Mnemonic
from bip32 import BIP32
from ecdsa import SigningKey, SECP256k1
from ecdsa.util import string_to_number, number_to_string
import asyncio


class Secp256k1KeyIdentity:
    """Secp256k1 key identity implementation for IC."""
    
    def __init__(self, private_key: bytes):
        """Initialize with private key bytes."""
        self._private_key = private_key
        self._signing_key = SigningKey.from_string(private_key, curve=SECP256k1)
        self._public_key = self._signing_key.get_verifying_key().to_string()
        self._principal_id = self._derive_principal_id()
    
    def _derive_principal_id(self) -> str:
        """Derive IC Principal ID from public key using proper IC algorithm."""
        import hashlib
        
        # Get compressed public key (33 bytes)
        verifying_key = self._signing_key.get_verifying_key()
        compressed_public_key = verifying_key.to_string("compressed")
        
        # DER-encode the public key
        der_prefix = bytes.fromhex("301e300c060a2b0601040183b8430101030e00")
        der_encoded = der_prefix + compressed_public_key
        
        # Hash with SHA224
        hash_result = hashlib.sha224(der_encoded).digest()
        
        # Add self-authenticating suffix (0x02)
        principal_bytes = hash_result + b'\x02'
        
        # Encode to IC principal format
        return self._encode_principal_ic_format(principal_bytes)
    
    def _encode_principal_ic_format(self, data: bytes) -> str:
        """Encode principal bytes to IC text format with CRC32 checksum."""
        import struct
        import zlib
        
        # Calculate CRC32 checksum
        crc = zlib.crc32(data) & 0xffffffff
        crc_bytes = struct.pack('<L', crc)
        
        # Combine data with checksum
        full_data = crc_bytes + data
        
        # Base32 encode with IC alphabet
        ic_alphabet = "abcdefghijklmnopqrstuvwxyz234567"
        
        # Convert to base32 using IC alphabet
        result = ""
        val = int.from_bytes(full_data, 'big')
        
        if val == 0:
            result = ic_alphabet[0]
        else:
            while val > 0:
                result = ic_alphabet[val % 32] + result
                val //= 32
        
        # Add separators every 5 characters for readability
        formatted = ""
        for i, char in enumerate(result):
            if i > 0 and i % 5 == 0:
                formatted += "-"
            formatted += char
        
        return formatted
    
    def get_principal(self) -> 'Principal':
        """Get the Principal object."""
        return Principal(self._principal_id)
    
    def sign(self, message: bytes) -> bytes:
        """Sign a message with the private key."""
        return self._signing_key.sign(message)


class Principal:
    """IC Principal representation."""
    
    def __init__(self, principal_id: str):
        self._id = principal_id
    
    def to_text(self) -> str:
        """Convert principal to text representation."""
        return self._id
    
    @classmethod
    def from_text(cls, text: str) -> 'Principal':
        """Create Principal from text representation."""
        return cls(text)


class ICIdentity:
    """
    Internet Computer Identity management.
    
    Handles mnemonic generation, key derivation, and identity creation
    using BIP39/BIP32 standards with Secp256k1 keys.
    """
    
    def __init__(self):
        self._mnemonic: Optional[str] = None
        self._private_key: Optional[bytes] = None
        self._public_key: Optional[bytes] = None
        self._identity: Optional[Secp256k1KeyIdentity] = None
        self._principal_id: Optional[str] = None
    
    @property
    def identity(self) -> Optional[Secp256k1KeyIdentity]:
        """Get the Secp256k1 identity."""
        return self._identity
    
    @property
    def mnemonic(self) -> Optional[str]:
        """Get the mnemonic phrase."""
        return self._mnemonic
    
    @property
    def principal_id(self) -> Optional[str]:
        """Get the principal ID."""
        return self._principal_id
    
    async def initialize(self, mnemonic: Optional[str] = None) -> None:
        """
        Initialize the identity with a mnemonic.
        
        Args:
            mnemonic: Optional mnemonic phrase. If None, generates a new one.
        """
        if mnemonic:
            self._mnemonic = mnemonic
        else:
            self._mnemonic = generate_mnemonic()
        
        # Convert mnemonic to seed
        mnemo = Mnemonic("english")
        if not mnemo.check(self._mnemonic):
            raise ValueError("Invalid mnemonic phrase")
        
        seed = mnemo.to_seed(self._mnemonic)
        
        # Derive key using BIP32 path m/44'/223'/0'/0/0 (IC standard)
        bip32 = BIP32.from_seed(seed)
        # IC uses coin type 223
        derived_key = bip32.get_privkey_from_path("m/44'/223'/0'/0/0")
        
        self._private_key = derived_key
        
        # Create identity
        self._identity = Secp256k1KeyIdentity(self._private_key)
        self._principal_id = self._identity.get_principal().to_text()
        
        # Extract public key
        self._public_key = self._identity._public_key


def generate_mnemonic() -> str:
    """Generate a new BIP39 mnemonic phrase."""
    mnemo = Mnemonic("english")
    return mnemo.generate(strength=128)  # 12 words


async def create_ic_identity(mnemonic: Optional[str] = None) -> ICIdentity:
    """
    Create and initialize an IC Identity.
    
    Args:
        mnemonic: Optional mnemonic phrase. If None, generates a new one.
    
    Returns:
        Initialized ICIdentity instance.
    """
    ic_identity = ICIdentity()
    await ic_identity.initialize(mnemonic)
    return ic_identity


async def create_ic_identity_serializable(mnemonic: Optional[str] = None) -> dict:
    """
    Create an IC identity and return serializable data.
    
    Args:
        mnemonic: Optional mnemonic phrase. If None, generates a new one.
    
    Returns:
        Dictionary with mnemonic and principal ID.
    """
    ic_identity = await create_ic_identity(mnemonic)
    return {
        "mnemonic": ic_identity.mnemonic,
        "principal_id": ic_identity.principal_id,
    }