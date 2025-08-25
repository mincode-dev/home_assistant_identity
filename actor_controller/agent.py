# Import IC libraries - fail if not available
from ic.client import Client
from ic.agent import Agent
from ic.identity import Identity


class ICAgent:
    """Real IC Agent for canister communication."""
    
    def __init__(self, identity: Identity, host: str = None, fetch=None):
        self.identity = identity
        self.host = host
        self.fetch = fetch
        self._invalidated = False
        self.client = Client(url=host)
        self.agent = Agent(identity, self.client)
        print(f"✅ Real IC agent created for {host}")
    
    async def fetch_root_key(self):
        """Fetch root key for local development."""
        if 'localhost' in self.host or '127.0.0.1' in self.host:
            await self.agent.fetch_root_key()
            print(f"✅ Fetched root key for local development")
    
    def replace_identity(self, new_identity):
        """Replace the current identity."""
        self.identity = new_identity
        self.agent = Agent(new_identity, self.client)

