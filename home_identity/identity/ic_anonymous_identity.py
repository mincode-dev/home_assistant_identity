class AnonymousIdentity:
    """Anonymous identity for IC interactions."""
    
    def __init__(self):
        self.principal_id = "2vxsx-fae"  # Standard anonymous principal
    
    def get_principal(self):
        """Get the anonymous principal."""
        from ..identity.ic_identity import Principal
        return Principal(self.principal_id)
