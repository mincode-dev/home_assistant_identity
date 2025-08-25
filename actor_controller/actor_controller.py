"""
Actor Controller for Internet Computer canister interactions.

This module provides the main ActorController class that manages
communication with IC canisters, closely mirroring the TypeScript implementation.
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Import IC libraries - fail if not available

# Load environment variables
load_dotenv()

# Environment configuration
DEFAULT_HOST = os.getenv('DFX_HOST', 'https://ic0.app')
DEFAULT_NETWORK = os.getenv('DFX_NETWORK', 'ic')


class ActorController:
    """
    Main controller for IC canister interactions.
    
    Manages authentication, agent creation, and canister communication
    using real IC network calls only.
    """
    
    def __init__(self, canister_name: str = 'M_AUTONOME', canister_id: str = None, fetch=None):
        """
        Initialize ActorController.
        
        Args:
            canister_name: Name of the canister to interact with
            fetch: Optional custom fetch function
        """
        
        self._canister_id = canister_id 
        self._canister_name = canister_name
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
            self._agent,
            self._canister_id
        )
        
        # Fetch root key for local development
        if not self._is_production_environment:
            await self._agent.fetch_root_key()
    
    async def _create_agent(self, options: Dict[str, Any]) -> ICAgent:
        """Create an HTTP agent with the given options."""
        return ICAgent(**options)
        

def create_actor_controller(
    canister_name: str = 'M_AUTONOME', 
    canister_id: str = None,
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
    return ActorController(canister_name, canister_id, fetch_override)