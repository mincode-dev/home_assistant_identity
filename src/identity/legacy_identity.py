import os
import json
import logging
from datetime import datetime
from ic.identity import Identity
from ic.agent import Agent
from ic.client import Client
from mnemonic import Mnemonic
import nacl.secret
import nacl.utils

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ICPIdentityManager:
    def __init__(self, data_path="/data"):
        self.data_path = data_path
        self.identity_file = os.path.join(data_path, "icp_identity.json")
        self.mnemonic_file = os.path.join(data_path, "mnemonic.mne")
        self.identity = None
        self.agent = None
        self.network = "mainnet"  # Default to mainnet
        
        # Ensure data directory exists
        os.makedirs(data_path, exist_ok=True)
        
    def initialize(self, generate_new=False, network="mainnet"):
        """Initialize or create ICP identity"""
        try:
            self.network = network
            logger.info(f"Initializing ICP identity (network: {network})")
            
            if generate_new or not self._identity_exists():
                self._generate_new_identity()
            else:
                self._load_existing_identity()
                
            self._setup_agent()
            logger.info("ICP identity initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ICP identity: {e}")
            raise
        
    def _identity_exists(self):
        """Check if identity files exist"""
        return os.path.exists(self.identity_file) and os.path.exists(self.mnemonic_file)
        
    def _generate_new_identity(self):
        """Generate new ICP identity with mnemonic"""
        try:
            logger.info("Generating new ICP identity...")
            
            # Generate mnemonic (like your BIP39 approach)
            mnemo = Mnemonic("english")
            mnemonic = mnemo.generate(strength=128)
            logger.info("✅ Mnemonic generated successfully")
            
            # Validate mnemonic
            if not mnemo.check(mnemonic):
                raise ValueError("Generated mnemonic is invalid")
            logger.info("✅ Mnemonic validated successfully")
            
            # Create identity from mnemonic STRING (not seed bytes)
            logger.info(f"✅ Mnemonic string: {mnemonic[:20]}...")
            
            try:
                # Pass the mnemonic STRING to ic-py, not the seed bytes
                self.identity = Identity.from_seed(mnemonic)  # Pass mnemonic string!
                logger.info("✅ Identity created from mnemonic successfully")
            except Exception as e:
                logger.error(f"❌ Error creating identity from mnemonic: {e}")
                raise
            
            # Save encrypted mnemonic
            self._save_mnemonic(mnemonic)
            logger.info("✅ Mnemonic saved successfully")
            
            # Now try to access identity properties
            try:
                principal_obj = self.identity.sender()
                logger.info(f"✅ Principal object obtained: {type(principal_obj)}")
                
                principal_str = str(principal_obj)
                logger.info(f"✅ Principal string: {principal_str}")
                
                # Get public key - it's available as .pubkey attribute (already hex string)
                public_key_hex = self.identity.pubkey
                logger.info(f"✅ Public key hex: {public_key_hex}")
                
            except Exception as e:
                logger.error(f"❌ Error accessing identity properties: {e}")
                raise
            
            # Save identity metadata
            identity_data = {
                "principal": principal_str,
                "public_key": public_key_hex,
                "created_at": datetime.now().isoformat(),
                "network": self.network
            }
            
            try:
                with open(self.identity_file, 'w', encoding='utf-8') as f:
                    json.dump(identity_data, f, indent=2, ensure_ascii=False)
                logger.info("✅ Identity file saved successfully")
            except Exception as e:
                logger.error(f"❌ Error saving identity file: {e}")
                raise
                
            logger.info(f"✅ Generated new ICP identity: {identity_data['principal']}")
            
        except Exception as e:
            logger.error(f"Failed to generate new identity: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
        
    def _load_existing_identity(self):
        """Load existing identity from storage"""
        try:
            logger.info("Loading existing ICP identity...")
            
            # Validate identity file exists and is readable
            if not os.path.exists(self.identity_file):
                raise FileNotFoundError(f"Identity file not found: {self.identity_file}")
                
            # Load and validate identity metadata
            with open(self.identity_file, 'r') as f:
                identity_data = json.load(f)
                
            required_fields = ["principal", "public_key", "created_at"]
            for field in required_fields:
                if field not in identity_data:
                    raise ValueError(f"Invalid identity file: missing field '{field}'")
            
            # Load mnemonic and recreate identity
            mnemonic = self._load_mnemonic()
            
            mnemo = Mnemonic("english")
            if not mnemo.check(mnemonic):
                raise ValueError("Stored mnemonic is invalid")
                
            # Use mnemonic string directly
            self.identity = Identity.from_seed(mnemonic)
            
            # Verify loaded identity matches stored data
            if str(self.identity.sender()) != identity_data["principal"]:
                raise ValueError("Identity verification failed: principal mismatch")
            
            logger.info(f"✅ Loaded existing ICP identity: {self.get_principal()}")
            
        except Exception as e:
            logger.error(f"Failed to load existing identity: {e}")
            raise
        
    def _save_mnemonic(self, mnemonic):
        """Save encrypted mnemonic"""
        try:
            # Generate random encryption key
            key = nacl.utils.random(nacl.secret.SecretBox.KEY_SIZE)
            box = nacl.secret.SecretBox(key)
            
            # Explicitly encode as UTF-8
            encrypted = box.encrypt(mnemonic.encode('utf-8'))
            
            with open(self.mnemonic_file, 'wb') as f:
                f.write(key + encrypted)
                
            # Set restrictive permissions
            os.chmod(self.mnemonic_file, 0o600)
            logger.info("Mnemonic saved and encrypted successfully")
            
        except Exception as e:
            logger.error(f"Failed to save mnemonic: {e}")
            raise
            
    def _load_mnemonic(self):
        """Load and decrypt mnemonic"""
        try:
            if not os.path.exists(self.mnemonic_file):
                raise FileNotFoundError(f"Mnemonic file not found: {self.mnemonic_file}")
                
            with open(self.mnemonic_file, 'rb') as f:
                data = f.read()
                
            if len(data) < nacl.secret.SecretBox.KEY_SIZE:
                raise ValueError("Invalid mnemonic file: too short")
                
            key = data[:nacl.secret.SecretBox.KEY_SIZE]
            encrypted = data[nacl.secret.SecretBox.KEY_SIZE:]
            
            box = nacl.secret.SecretBox(key)
            decrypted = box.decrypt(encrypted)
            
            return decrypted.decode()
            
        except Exception as e:
            logger.error(f"Failed to load mnemonic: {e}")
            raise
        
    def _setup_agent(self):
        """Setup ICP agent with configurable network"""
        try:
            # Configure network endpoint
            network_urls = {
                "mainnet": "https://ic0.app",
                "testnet": "https://testnet.ic0.app", 
                "local": "http://localhost:4943"
            }
            
            agent_url = network_urls.get(self.network, "https://ic0.app")
            self.agent = Agent(self.identity, agent_url)
            
            # Store the URL for later reference since Agent might not expose it
            self.agent_url = agent_url
            
            logger.info(f"ICP agent configured for {self.network} network ({agent_url})")
            
        except Exception as e:
            logger.error(f"Failed to setup ICP agent: {e}")
            raise
        
    def get_principal(self):
        """Get principal ID as string"""
        if not self.identity:
            raise RuntimeError("Identity not initialized")
        return str(self.identity.sender())  # sender() IS the principal
        
    def get_public_key_hex(self):
        """Get public key as hex string"""
        if not self.identity:
            raise RuntimeError("Identity not initialized")
        return self.identity.pubkey  # It's already a hex string!
        
    async def call_canister(self, canister_id, method, args=None):
        """Call canister method with proper error handling"""
        try:
            if not self.agent:
                raise RuntimeError("Agent not initialized")
                
            logger.info(f"Calling canister {canister_id}.{method}")
            canister = self.agent.canister(canister_id)
            result = await canister.call(method, args or [])
            
            logger.info(f"Canister call successful: {canister_id}.{method}")
            return result
            
        except Exception as e:
            logger.error(f"Canister call failed {canister_id}.{method}: {e}")
            raise
            
    def get_identity_info(self):
        """Get comprehensive identity information"""
        if not self.identity:
            raise RuntimeError("Identity not initialized")
            
        return {
            "principal": self.get_principal(),
            "public_key": self.get_public_key_hex(),
            "network": self.network,
            "agent_url": getattr(self.agent, 'url', None) if self.agent else None,
            "identity_file": self.identity_file,
            "has_mnemonic": os.path.exists(self.mnemonic_file)
        } 