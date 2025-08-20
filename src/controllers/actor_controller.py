"""
Actor Controller for Internet Computer canister interactions.

This module provides the main ActorController class that manages
communication with IC canisters, closely mirroring the TypeScript implementation.
"""

import os
import asyncio
from typing import Optional, Dict, Any, Union, List
from dotenv import load_dotenv

# Import IC libraries - fail if not available
from ic.client import Client
from ic.identity import Identity as ICPyIdentity
from ic.agent import Agent
from ic.canister import Canister

# Load environment variables
load_dotenv()


class ICAgent:
    """Real IC Agent for canister communication."""
    
    def __init__(self, identity=None, host: str = None, fetch=None):
        self.identity = identity
        self.host = host
        self.fetch = fetch
        self._invalidated = False
        
        if not identity or not hasattr(identity, '_private_key'):
            raise ValueError("Valid IC identity with private key required")
        
        # Create real IC agent
        self.client = Client(url=host)
        # Convert private key bytes to hex string if needed
        private_key = identity._private_key
        if isinstance(private_key, bytes):
            private_key = private_key.hex()
        ic_identity = ICPyIdentity(private_key)
        self.agent = Agent(ic_identity, self.client)
        print(f"✅ Real IC agent created for {host}")
    
    async def fetch_root_key(self):
        """Fetch root key for local development."""
        if 'localhost' in self.host or '127.0.0.1' in self.host:
            await self.agent.fetch_root_key()
            print(f"✅ Fetched root key for local development")
    
    def invalidate_identity(self):
        """Invalidate the current identity."""
        self._invalidated = True
        self.identity = None
    
    def replace_identity(self, new_identity):
        """Replace the current identity."""
        self.identity = new_identity
        if new_identity and hasattr(new_identity, '_private_key'):
            private_key = new_identity._private_key
            if isinstance(private_key, bytes):
                private_key = private_key.hex()
            ic_identity = ICPyIdentity(private_key)
            self.agent = Agent(ic_identity, self.client)


class ICActor:
    """Proper IC Actor using ic-py's Canister class with .did file."""
    
    def __init__(self, interface_factory, agent: ICAgent, canister_id: str):
        self.interface_factory = interface_factory
        self.agent = agent
        self.canister_id = canister_id
        print(f"✅ Real canister calls enabled for {canister_id}")
        
        # Load Candid interface from the .did file
        candid_interface = self._load_candid_interface()
        
        if not candid_interface:
            raise RuntimeError("Could not load Candid interface from .did file")
        
        # Create canister instance with Candid interface
        # This handles all encoding/decoding automatically!
        self.canister = Canister(
            agent=agent.agent,
            canister_id=canister_id,
            candid=candid_interface
        )
        
        print(f"🎯 Canister instance created with automatic Candid encoding/decoding")
    
    def _load_candid_interface(self) -> str:
        """Load the Candid interface from the local .did file."""
        try:
            # Path to the .did file in the data folder
            did_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'm_autonome_canister.did')
            
            with open(did_file_path, 'r') as f:
                candid_text = f.read()
            
            print(f"✅ Loaded Candid interface from {did_file_path} ({len(candid_text)} chars)")
            return candid_text
            
        except Exception as e:
            print(f"❌ Failed to load Candid interface: {e}")
            return ""
    
    async def _call_method(self, method_name: str, args: List[Any] = None):
        """Make canister call using proper Canister instance - NO MORE FIELD HASHES!"""
        try:
            print(f"🔄 Calling canister method: {method_name} with Candid auto-decoding")
            
            # Get the method from the canister instance
            method = getattr(self.canister, method_name)
            
            # Call the method - Canister instance handles all encoding/decoding!
            # Note: Canister methods are synchronous, not async
            if args:
                result = method(*args)
            else:
                result = method()
            
            print(f"✅ Canister call successful with automatic decoding")
            print(f"📊 Result type: {type(result)}")
            print(f"📊 Properly decoded result: {result}")
            return result
            
        except Exception as e:
            print(f"❌ Canister call failed: {e}")
            return {"status": "error", "message": str(e)}
    

    
    async def _query_method(self, method_name: str, args: List[Any] = None):
        """Make canister query using proper Canister instance - NO MORE FIELD HASHES!"""
        try:
            print(f"🔍 Querying canister method: {method_name} with Candid auto-decoding")
            
            # Get the method from the canister instance
            method = getattr(self.canister, method_name)
            
            # Call the method - Canister instance handles all encoding/decoding!
            # Note: Canister methods are synchronous, not async
            if args:
                result = method(*args)
            else:
                result = method()
            
            print(f"✅ Canister query successful with automatic decoding")
            print(f"📊 Query result type: {type(result)}")
            print(f"📊 Properly decoded query result: {result}")
            return result
            
        except Exception as e:
            print(f"❌ Canister query failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def login(self):
        """Real login method."""
        return await self._call_method("login", [])
    
    async def register(self, username: str, fullname: str, bio: str, avatar: str):
        """Real register method."""
        args = [username, fullname, bio, avatar]
        return await self._call_method("register", args)
    
    async def get_conversations(self):
        """Real get conversations method."""
        return await self._query_method("getConversations", [])


class AnonymousIdentity:
    """Anonymous identity for IC interactions."""
    
    def __init__(self):
        self.principal_id = "2vxsx-fae"  # Standard anonymous principal
    
    def get_principal(self):
        """Get the anonymous principal."""
        from ..identity.ic_identity import Principal
        return Principal(self.principal_id)


# Environment configuration
DEFAULT_HOST = os.getenv('DFX_HOST', 'https://ic0.app')
DEFAULT_NETWORK = os.getenv('DFX_NETWORK', 'ic')


class ActorController:
    """
    Main controller for IC canister interactions.
    
    Manages authentication, agent creation, and canister communication
    using real IC network calls only.
    """
    
    def __init__(self, canister_name: str = 'M_AUTONOME', fetch=None):
        """
        Initialize ActorController.
        
        Args:
            canister_name: Name of the canister to interact with
            fetch: Optional custom fetch function
        """
        canister_data = self._determine_canister_data(canister_name)
        self._canister_id = canister_data["canister_id"]
        self._interface_factory = canister_data["interface_factory"]
        
        self._actor: Optional[ICActor] = None
        self._agent: Optional[ICAgent] = None
        self._is_authenticated = False
        self._host = DEFAULT_HOST
        self._is_production_environment = os.getenv('NODE_ENV') == 'production'
    
    def get_actor(self) -> Optional[ICActor]:
        """Get the current actor instance."""
        return self._actor
    
    def get_agent(self) -> Optional[ICAgent]:
        """Get the current agent instance.""" 
        return self._agent
    
    def get_is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return self._is_authenticated
    
    async def authenticate(self, identity) -> None:
        """
        Authenticate with the provided identity.
        
        Args:
            identity: IC identity object
        """
        if not self._canister_id:
            raise RuntimeError("Canister ID not configured")
        
        print(f"🔐 Authenticating with canister: {self._canister_id}")
        print(f"🌐 Network: {self._host}")
        print(f"📡 Using real IC authentication")
        
        await self.initialize(identity)
        self._is_authenticated = True
        
        if hasattr(identity, 'get_principal'):
            principal = identity.get_principal()
            if principal:
                print(f"📋 Principal: {principal.to_text()}")
        
        # Authentication setup complete - actual verification happens on first canister call
        print(f"✅ Authentication setup complete (verification on first canister call)")
    
    async def deauthenticate(self) -> None:
        """Deauthenticate and clear session."""
        if self._agent:
            self._agent.invalidate_identity()
        self._is_authenticated = False
    
    async def set_anonymous_identity(self) -> None:
        """Set anonymous identity."""
        if self._agent:
            anonymous = AnonymousIdentity()
            self._agent.replace_identity(anonymous)
    
    async def initialize(self, identity=None, fetch=None) -> None:
        """
        Initialize the agent and actor.
        
        Args:
            identity: Optional identity for authentication
            fetch: Optional custom fetch function
        """
        # Create HTTP agent
        agent_options = {
            "identity": identity,
            "host": self._host
        }
        
        if fetch:
            agent_options["fetch"] = fetch
        
        self._agent = await self._create_agent(agent_options)
        
        # Create actor
        self._actor = ICActor(
            self._interface_factory,
            self._agent,
            self._canister_id
        )
        
        # Fetch root key for local development
        if not self._is_production_environment:
            await self._agent.fetch_root_key()
    
    async def _create_agent(self, options: Dict[str, Any]) -> ICAgent:
        """Create an HTTP agent with the given options."""
        return ICAgent(**options)
    
    def _determine_canister_data(self, canister_name: str) -> Dict[str, Any]:
        """
        Determine canister ID and interface factory based on name.
        
        Args:
            canister_name: Name of the canister
            
        Returns:
            Dictionary with canister_id and interface_factory
        """
        canister_id = os.getenv('M_AUTONOME_CANISTER')
        interface_factory = "m_autonome_canister_factory"  # Mock factory
        
        if 'BUSINESS' in canister_name:
            canister_id = os.getenv('M_BUSINESS_CANISTER')
            interface_factory = "m_business_canister_factory"
        elif 'POINT' in canister_name:
            canister_id = os.getenv('M_POINT_CANISTER')
            interface_factory = "m_point_canister_factory"
        
        return {
            "canister_id": canister_id,
            "interface_factory": interface_factory
        }
    
    # Convenience methods for common canister operations
    async def login(self):
        """Login to the canister."""
        if not self._actor:
            raise RuntimeError("Actor not initialized")
        return await self._actor.login()
    
    async def register(self, username: str, fullname: str, bio: str, avatar: str):
        """Register a new user."""
        if not self._actor:
            raise RuntimeError("Actor not initialized")
        return await self._actor.register(username, fullname, bio, avatar)
    
    async def get_conversations(self):
        """Get user conversations."""
        if not self._actor:
            raise RuntimeError("Actor not initialized")
        return await self._actor.get_conversations()


def create_actor_controller(
    canister_name: str = 'M_AUTONOME', 
    fetch_override=None
) -> ActorController:
    """
    Create a new ActorController instance.
    
    Args:
        canister_name: Name of the canister to interact with
        fetch_override: Optional custom fetch function
    
    Returns:
        New ActorController instance
    """
    return ActorController(canister_name, fetch_override)