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
        self.mnemonic_file = os.path.join(data_path, "mnemonic.enc")
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
            
            # Validate mnemonic
            if not mnemo.check(mnemonic):
                raise ValueError("Generated mnemonic is invalid")
            
            # Create identity from mnemonic
            seed = mnemo.to_seed(mnemonic)
            self.identity = Identity.from_seed(seed[:32])
            
            # Save encrypted mnemonic
            self._save_mnemonic(mnemonic)
            
            # Save identity metadata
            identity_data = {
                "principal": str(self.identity.sender().principal),
                "public_key": self.identity.sender().public_key.hex(),
                "created_at": datetime.now().isoformat(),
                "network": self.network
            }
            
            with open(self.identity_file, 'w') as f:
                json.dump(identity_data, f, indent=2)
                
            logger.info(f"✅ Generated new ICP identity: {identity_data['principal']}")
            
        except Exception as e:
            logger.error(f"Failed to generate new identity: {e}")
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
                
            seed = mnemo.to_seed(mnemonic)
            self.identity = Identity.from_seed(seed[:32])
            
            # Verify loaded identity matches stored data
            if str(self.identity.sender().principal) != identity_data["principal"]:
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
            
            encrypted = box.encrypt(mnemonic.encode())
            
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
            
            logger.info(f"ICP agent configured for {self.network} network ({agent_url})")
            
        except Exception as e:
            logger.error(f"Failed to setup ICP agent: {e}")
            raise
        
    def get_principal(self):
        """Get principal ID as string"""
        if not self.identity:
            raise RuntimeError("Identity not initialized")
        return str(self.identity.sender().principal)
        
    def get_public_key_hex(self):
        """Get public key as hex string"""
        if not self.identity:
            raise RuntimeError("Identity not initialized")
        return self.identity.sender().public_key.hex()
        
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
            "agent_url": self.agent.url if self.agent else None,
            "identity_file": self.identity_file,
            "has_mnemonic": os.path.exists(self.mnemonic_file)
        } 