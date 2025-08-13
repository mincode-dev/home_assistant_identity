import os
import json
import logging
from typing import Dict, Any, Optional, List
from ic.agent import Agent
from ic.identity import Identity
from ic.candid import Types
from ic.canister import Canister

logger = logging.getLogger(__name__)

class ActorController:
    """
    Python equivalent of the TypeScript ActorController
    Handles canister authentication and method calls
    """
    
    def __init__(self, canister_id: str, network: str = "mainnet"):
        self._actor = None
        self._agent = None
        self._canister_id = canister_id
        self._network = network
        self._is_authenticated = False
        self._identity = None
        
        # Network configuration
        self._network_urls = {
            "mainnet": "https://ic0.app",
            "testnet": "https://testnet.ic0.app",
            "local": "http://localhost:4943"
        }
        
        self._host = self._network_urls.get(network, "https://ic0.app")
        self._is_production = network == "mainnet"
        
        logger.info(f"ActorController initialized for canister {canister_id} on {network}")
    
    def get_actor(self):
        """Get the canister actor instance"""
        return self._actor
    
    def get_agent(self):
        """Get the agent instance"""
        return self._agent
    
    def get_is_authenticated(self):
        """Check if authenticated"""
        return self._is_authenticated
    
    async def authenticate(self, identity: Identity):
        """Authenticate with the given identity"""
        try:
            logger.info(f"Authenticating with canister {self._canister_id}")
            await self._initialize(identity)
            self._is_authenticated = True
            logger.info("✅ Authentication successful")
            return True
        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            raise
    
    async def deauthenticate(self):
        """Deauthenticate and clear identity"""
        try:
            if self._agent:
                # Clear the identity (ic-py equivalent of invalidateIdentity)
                self._agent = None
            self._is_authenticated = False
            self._actor = None
            logger.info("✅ Deauthenticated successfully")
        except Exception as e:
            logger.error(f"❌ Deauthentication failed: {e}")
    
    async def _initialize(self, identity: Identity):
        """Initialize agent and actor with identity"""
        try:
            # Create agent with identity
            self._agent = Agent(identity, self._host)
            self._identity = identity
            
            # For local development, fetch root key
            if not self._is_production:
                # In ic-py, this might be handled automatically
                logger.info("Development mode: Using local network configuration")
            
            # Create actor (canister instance)
            self._actor = self._agent.canister(self._canister_id)
            
            logger.info(f"✅ Initialized actor for canister {self._canister_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize actor: {e}")
            raise
    
    async def call_method(self, method_name: str, args: List[Any] = None) -> Any:
        """
        Call a method on the authenticated canister
        
        Args:
            method_name: Name of the canister method to call
            args: Arguments to pass to the method
            
        Returns:
            Result from the canister method call
        """
        if not self._is_authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        if not self._actor:
            raise RuntimeError("Actor not initialized")
        
        try:
            logger.info(f"Calling method {method_name} on canister {self._canister_id}")
            
            # Call the canister method
            if args is None:
                args = []
            
            result = await self._actor.call(method_name, args)
            
            logger.info(f"✅ Method call successful: {method_name}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Method call failed {method_name}: {e}")
            raise
    
    async def query_method(self, method_name: str, args: List[Any] = None) -> Any:
        """
        Query a method on the authenticated canister (read-only)
        
        Args:
            method_name: Name of the canister method to query
            args: Arguments to pass to the method
            
        Returns:
            Result from the canister method query
        """
        if not self._is_authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        if not self._actor:
            raise RuntimeError("Actor not initialized")
        
        try:
            logger.info(f"Querying method {method_name} on canister {self._canister_id}")
            
            if args is None:
                args = []
            
            # For queries, we might use a different method in ic-py
            # This depends on the specific ic-py implementation
            result = await self._actor.query(method_name, args)
            
            logger.info(f"✅ Method query successful: {method_name}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Method query failed {method_name}: {e}")
            raise
    
    def get_canister_info(self) -> Dict[str, Any]:
        """Get information about the current canister configuration"""
        return {
            "canister_id": self._canister_id,
            "network": self._network,
            "host": self._host,
            "is_authenticated": self._is_authenticated,
            "is_production": self._is_production,
            "principal": str(self._identity.sender()) if self._identity else None
        }


class CanisterRegistry:
    """
    Registry to manage multiple canister controllers
    Similar to your multiple canister support in TypeScript
    """
    
    def __init__(self, network: str = "mainnet"):
        self.network = network
        self.controllers: Dict[str, ActorController] = {}
        logger.info(f"CanisterRegistry initialized for {network}")
    
    def register_canister(self, name: str, canister_id: str) -> ActorController:
        """Register a new canister controller"""
        controller = ActorController(canister_id, self.network)
        self.controllers[name] = controller
        logger.info(f"Registered canister {name}: {canister_id}")
        return controller
    
    def get_controller(self, name: str) -> Optional[ActorController]:
        """Get a canister controller by name"""
        return self.controllers.get(name)
    
    async def authenticate_all(self, identity: Identity):
        """Authenticate all registered controllers"""
        results = {}
        for name, controller in self.controllers.items():
            try:
                await controller.authenticate(identity)
                results[name] = True
                logger.info(f"✅ Authenticated with {name}")
            except Exception as e:
                results[name] = False
                logger.error(f"❌ Failed to authenticate with {name}: {e}")
        return results
    
    async def deauthenticate_all(self):
        """Deauthenticate all controllers"""
        for name, controller in self.controllers.items():
            try:
                await controller.deauthenticate()
                logger.info(f"✅ Deauthenticated from {name}")
            except Exception as e:
                logger.error(f"❌ Failed to deauthenticate from {name}: {e}")
    
    def list_canisters(self) -> List[Dict[str, Any]]:
        """List all registered canisters"""
        return [
            {
                "name": name,
                **controller.get_canister_info()
            }
            for name, controller in self.controllers.items()
        ]


def create_actor_controller(canister_id: str, network: str = "mainnet") -> ActorController:
    """
    Factory function to create an ActorController
    Python equivalent of your createActorController function
    """
    return ActorController(canister_id, network)


# Example usage patterns that mirror your TypeScript code:
"""
# Python equivalent of your TypeScript usage:

# 1. Create identity (already handled by ICPIdentityManager)
identity = icp_manager.identity

# 2. Create actor controller
actor_controller = create_actor_controller('your-canister-id', 'mainnet')

# 3. Authenticate
await actor_controller.authenticate(identity)

# 4. Call methods
login_result = await actor_controller.call_method('login')
if 'err' in login_result:
    register_result = await actor_controller.call_method('register', ['', '', '', ''])
else:
    # Already logged in
    pass

# 5. Query methods (read-only)
user_data = await actor_controller.query_method('getUserData')
"""