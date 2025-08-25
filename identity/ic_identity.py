from ic.identity import Identity as ICPyIdentity
from ic.principal import Principal

class ICIdentity:
    """Internet Computer Identity."""
    
    def __init__(self, private_key: bytes):
        self._private_key = private_key
        self._identity = ICPyIdentity(private_key.hex())
        self._principal = Principal.self_authenticating(self._identity.der_pubkey)
    
    @property
    def principal(self):
        """Get the principal ID."""
        return self._principal.to_str()
    
    @property
    def public_key(self):
        """Get the public key."""
        return self._identity.pubkey
    
    @property
    def private_key(self):
        """Get the private key."""
        return self._private_key

    @property
    def identity(self):
        """Get the identity."""
        return self._identity

    def regenerate_identity(self, private_key: bytes):
        """Regenerate the identity."""
        self._private_key = private_key
        self._identity = ICPyIdentity(private_key)