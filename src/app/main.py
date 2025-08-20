import os
import json
import asyncio
import logging
import aiohttp.web
from aiohttp import web
from identity.legacy_identity import ICPIdentityManager
from integrations.home_assistant import HomeAssistantIntegration
from core.storage import IdentityStorage
from core.canister_registry import CanisterRegistry
from controllers.actor_controller import ActorController, create_actor_controller
from identity.local_ic_identity import LocalICIdentity
from utils.candid_parser import CandidParser
from datetime import datetime
from .dashboard_template import generate_dashboard_html

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ICPIdentityAddon:
    def __init__(self):
        self.icp_manager = ICPIdentityManager(data_path="/data")
        self.ha_integration = HomeAssistantIntegration(self.icp_manager)
        self.storage = IdentityStorage(data_path="/data")
        self.canister_registry = CanisterRegistry(data_path="/data")
        # New actor controller for canister interactions
        self.actor_controller = None
        self.local_identity = None
        self.app = aiohttp.web.Application()
        
        # Dynamic canister endpoints will be added here
        self.canister_routes = {}
        
    async def start(self):
        """Start the addon with comprehensive error handling"""
        try:
            logger.info("🚀 Starting ICP Identity Addon...")
            
            # Load and validate configuration
            options = self._get_addon_options()
            self._validate_options(options)
            
            # Initialize ICP identity with network configuration
            network = options.get('network', 'mainnet')
            generate_new = options.get('generate_new_identity', False)
            
            self.icp_manager.initialize(generate_new=generate_new, network=network)
            
            # Initialize new actor controller with environment setup
            await self._setup_actor_controller(options, network)
            
            # Ensure identity is ready for canister binding
            await self._ensure_identity_ready()
            
            # Register with Home Assistant
            await self.ha_integration.register_icp_sensors()
            
            # Start web interface
            self._setup_web_routes()
            runner = aiohttp.web.AppRunner(self.app)
            await runner.setup()
            
            site = aiohttp.web.TCPSite(runner, '0.0.0.0', 8099)
            await site.start()
            
            logger.info("✅ ICP Identity Addon started successfully")
            logger.info(f"📝 Principal: {self.icp_manager.get_principal()}")
            logger.info(f"🌐 Web UI: http://homeassistant.local:8099")
            logger.info(f"🔗 Network: {network}")
            
            # Keep running
            await self._run_forever()
            
        except Exception as e:
            logger.error(f"Failed to start addon: {e}")
            raise
        
    def _get_addon_options(self):
        """Get addon configuration options with error handling"""
        try:
            options_file = '/data/options.json'
            if os.path.exists(options_file):
                with open(options_file, 'r') as f:
                    options = json.load(f)
                logger.info(f"Loaded addon options: {list(options.keys())}")
                return options
            else:
                logger.warning("No options.json found, using defaults")
                return {}
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in options.json: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error reading addon options: {e}")
            return {}
            
    def _validate_options(self, options):
        """Validate addon configuration options"""
        valid_networks = ['local', 'testnet', 'mainnet']
        network = options.get('network', 'mainnet')
        
        if network not in valid_networks:
            raise ValueError(f"Invalid network '{network}'. Must be one of: {valid_networks}")
            
        logger.info(f"Configuration validated successfully (network: {network})")
    
    async def _setup_actor_controller(self, options, network):
        """Setup the new actor controller with proper identity and environment"""
        try:
            logger.info("🎯 Setting up new actor controller...")
            
            # Setup environment variables for the actor controller
            self._setup_environment_variables(options, network)
            
            # Initialize local identity 
            self.local_identity = LocalICIdentity()
            await self.local_identity.initialize()
            
            if not self.local_identity.identity:
                logger.error("Failed to initialize local identity")
                return
                
            logger.info(f"✅ Local identity initialized: {self.local_identity.get_principal_id()}")
            
            # Create actor controller for M_AUTONOME canister
            self.actor_controller = create_actor_controller('M_AUTONOME')
            
            # Authenticate with the local identity
            await self.actor_controller.authenticate(self.local_identity.identity)
            
            logger.info("✅ Actor controller setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup actor controller: {e}")
            # Don't fail startup, just log the error
    
    def _setup_environment_variables(self, options, network):
        """Setup environment variables required by the actor controller"""
        # Set network configuration
        if network == 'mainnet':
            os.environ['DFX_HOST'] = 'https://ic0.app'
            os.environ['DFX_NETWORK'] = 'ic'
            os.environ['NODE_ENV'] = 'production'
        elif network == 'local':
            os.environ['DFX_HOST'] = 'http://localhost:4943'
            os.environ['DFX_NETWORK'] = 'local'
            os.environ['NODE_ENV'] = 'development'
        else:  # testnet
            os.environ['DFX_HOST'] = 'https://testnet.ic0.app'
            os.environ['DFX_NETWORK'] = 'testnet'
            os.environ['NODE_ENV'] = 'development'
        
        # Set canister IDs from options
        if 'm_autonome_canister' in options:
            os.environ['M_AUTONOME_CANISTER'] = options['m_autonome_canister']
        if 'm_business_canister' in options:
            os.environ['M_BUSINESS_CANISTER'] = options['m_business_canister']
        if 'm_point_canister' in options:
            os.environ['M_POINT_CANISTER'] = options['m_point_canister']
        if 'icp_ledger_canister' in options:
            os.environ['ICP_LEDGER_CANISTER'] = options['icp_ledger_canister']
        
        logger.info(f"Environment setup: {os.environ.get('DFX_HOST')}, M_AUTONOME: {os.environ.get('M_AUTONOME_CANISTER', 'Not set')}")
    
    async def _ensure_identity_ready(self):
        """Ensure local identity is created and ready for canister binding."""
        try:
            if not self.local_identity or not self.local_identity.identity:
                logger.info("🔐 Creating local identity for canister binding...")
                self.local_identity = LocalICIdentity()
                await self.local_identity.initialize()
                
                if self.local_identity.identity:
                    logger.info(f"✅ Identity ready: {self.local_identity.get_principal_id()}")
                else:
                    logger.error("❌ Failed to create local identity")
            else:
                logger.info(f"✅ Identity already ready: {self.local_identity.get_principal_id()}")
                
        except Exception as e:
            logger.error(f"Failed to ensure identity ready: {e}")
            
    def _setup_web_routes(self):
        """Setup web interface routes with error handling"""
        self.app.router.add_get('/', self._web_dashboard)
        self.app.router.add_get('/identity', self._get_identity_info)
        self.app.router.add_post('/regenerate', self._regenerate_identity)
        self.app.router.add_get('/backups', self._list_backups)
        self.app.router.add_post('/backup', self._create_backup)
        self.app.router.add_get('/stats', self._get_stats)
        self.app.router.add_get('/status', self._get_status)
        self.app.router.add_get('/health', self._health_check)
        
        # Canister management endpoints
        self.app.router.add_get('/canisters/list', self._list_canisters)
        self.app.router.add_post('/canisters/add', self._add_canister)
        self.app.router.add_delete('/canisters/{canister_id}', self._remove_canister)
        self.app.router.add_get('/canisters/{canister_id}', self._get_canister_info)
        
        # Setup dynamic canister method routes
        self._setup_dynamic_canister_routes()
        
        # Add error handling middleware
        self.app.middlewares.append(self._error_middleware)
        
    @web.middleware
    async def _error_middleware(self, request, handler):
        """Global error handling middleware"""
        try:
            return await handler(request)
        except Exception as e:
            logger.error(f"Request error: {e}")
            return web.json_response(
                {"error": str(e), "status": "error"}, 
                status=500
            )
        
    async def _web_dashboard(self, request):
        """Enhanced web dashboard with canister management"""
        try:
            stats = self.storage.get_storage_stats()
            backups = self.storage.list_backups()
            identity_info = self.icp_manager.get_identity_info()
            canisters = self.canister_registry.list_canisters()
            actor_principal = self.local_identity.get_principal_id() if self.local_identity else None
            
            html = generate_dashboard_html(identity_info, stats, backups, canisters, actor_principal)
            return aiohttp.web.Response(text=html, content_type='text/html')

            
        except Exception as e:
            logger.error(f"Error rendering dashboard: {e}")
            return web.Response(text=f"Dashboard Error: {e}", status=500)
        
    async def _get_identity_info(self, request):
        """API endpoint for identity info"""
        try:
            identity_info = self.icp_manager.get_identity_info()
            return aiohttp.web.json_response(identity_info)
        except Exception as e:
            logger.error(f"Error getting identity info: {e}")
            return web.json_response({"error": str(e)}, status=500)
        
    async def _regenerate_identity(self, request):
        """Regenerate identity with backup"""
        try:
            logger.info("Starting identity regeneration...")
            
            # Create backup before regenerating
            backup_path = self.storage.create_backup(
                self.icp_manager.identity_file,
                self.icp_manager.mnemonic_file
            )
            
            # Get current options for network config
            options = self._get_addon_options()
            network = options.get('network', 'mainnet')
            
            # Regenerate identity
            self.icp_manager.initialize(generate_new=True, network=network)
            await self.ha_integration.register_icp_sensors()
            
            logger.info("Identity regeneration completed successfully")
            return aiohttp.web.json_response({
                "status": "regenerated",
                "backup_path": backup_path,
                "new_principal": self.icp_manager.get_principal()
            })
            
        except Exception as e:
            logger.error(f"Error regenerating identity: {e}")
            return web.json_response({"error": str(e)}, status=500)
        
    async def _list_backups(self, request):
        """List all backups"""
        try:
            backups = self.storage.list_backups()
            return aiohttp.web.json_response({"backups": backups})
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return web.json_response({"error": str(e)}, status=500)
        
    async def _create_backup(self, request):
        """Create a backup"""
        try:
            backup_path = self.storage.create_backup(
                self.icp_manager.identity_file,
                self.icp_manager.mnemonic_file
            )
            return aiohttp.web.json_response({"backup_path": backup_path})
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return web.json_response({"error": str(e)}, status=500)
        
    async def _get_stats(self, request):
        """Get storage statistics"""
        try:
            stats = self.storage.get_storage_stats()
            identity_info = self.icp_manager.get_identity_info()
            
            combined_stats = {**stats, **identity_info}
            return aiohttp.web.json_response(combined_stats)
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def _get_status(self, request):
        """Get comprehensive status for Home Assistant integration"""
        try:
            logger.info("📡 Status endpoint called")
            
            # Get identity information
            identity_info = self.icp_manager.get_identity_info()
            logger.debug(f"Identity info: {identity_info}")
            
            # Get storage stats
            storage_stats = self.storage.get_storage_stats()
            logger.debug(f"Storage stats: {storage_stats}")
            
            # Get creation timestamp safely
            created_at = "Unknown"
            try:
                identity_file = storage_stats.get('identity_file', '/data/icp_identity.json')
                if identity_file and os.path.exists(identity_file):
                    created_timestamp = os.path.getctime(identity_file)
                    created_at = datetime.fromtimestamp(created_timestamp).strftime("%B %d, %Y at %I:%M:%S %p")
            except Exception as ts_error:
                logger.debug(f"Timestamp error: {ts_error}")
                created_at = "Unknown"
            
            # Safe public key handling
            public_key = identity_info.get('public_key', '')
            public_key_short = 'unknown'
            if public_key and len(public_key) > 32:
                public_key_short = f"{public_key[:32]}..."
            elif public_key:
                public_key_short = public_key
            
            # Build comprehensive status
            status = {
                # Connection and state
                "connection_status": "connected" if self.icp_manager.identity and self.icp_manager.agent else "disconnected",
                
                # Identity information
                "principal": identity_info.get('principal', 'unknown'),
                "public_key": public_key or 'unknown',
                "public_key_short": public_key_short,
                
                # Network and configuration
                "network": identity_info.get('network', 'mainnet'),
                "agent_url": identity_info.get('agent_url', None),
                
                # Security and backup
                "has_mnemonic": storage_stats.get('has_mnemonic', False),
                "identity_file_exists": bool(storage_stats.get('identity_file')) and os.path.exists(storage_stats.get('identity_file', '')),
                
                # Timestamps and metadata
                "created_at": created_at,
                "last_updated": datetime.now().isoformat(),
                
                # Status indicators for automation
                "automation_ready": True,
                "entity_status": "active"
            }
            
            logger.info("✅ Status endpoint returning data")
            return aiohttp.web.json_response(status)
            
        except Exception as e:
            logger.error(f"❌ Error getting status: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return aiohttp.web.json_response({
                "connection_status": "error",
                "error": str(e)
            }, status=500)
            
    async def _health_check(self, request):
        """Health check endpoint"""
        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "identity_initialized": self.icp_manager.identity is not None,
                "agent_initialized": self.icp_manager.agent is not None,
                "principal": self.icp_manager.get_principal() if self.icp_manager.identity else None
            }
            return aiohttp.web.json_response(health_status)
        except Exception as e:
            return web.json_response({
                "status": "unhealthy", 
                "error": str(e)
            }, status=500)
        
    async def _run_forever(self):
        """Keep addon running with periodic maintenance"""
        maintenance_counter = 0
        
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                maintenance_counter += 1
                
                # Perform maintenance every 10 minutes
                if maintenance_counter >= 10:
                    logger.info("Performing periodic maintenance...")
                    self.storage.cleanup_old_backups()
                    maintenance_counter = 0
                    
            except Exception as e:
                logger.error(f"Error in maintenance loop: {e}")
                await asyncio.sleep(60)
    
    def _setup_dynamic_canister_routes(self):
        """Setup dynamic routes for all registered canisters."""
        canisters = self.canister_registry.list_canisters()
        
        for canister in canisters:
            canister_id = canister["id"]
            self._add_canister_routes(canister_id)
    
    def _add_canister_routes(self, canister_id: str):
        """Add dynamic routes for a specific canister based on its .did file."""
        try:
            # Load and parse the .did file
            did_file_path = f"data/m_autonome_canister.did"  # For now, use the main .did file
            
            if os.path.exists(did_file_path):
                with open(did_file_path, 'r') as f:
                    did_content = f.read()
                
                methods = CandidParser.parse_did_file(did_content)
                
                # Add routes for each method
                for method in methods:
                    method_name = method["name"]
                    http_method = method["http_method"]
                    route_path = f'/canisters/{canister_id}/{method_name}'
                    
                    # Create handler for this specific method
                    handler = self._create_canister_method_handler(canister_id, method_name, method["is_query"])
                    
                    if http_method == "GET":
                        self.app.router.add_get(route_path, handler)
                    else:
                        self.app.router.add_post(route_path, handler)
                    
                    logger.info(f"✅ Added route: {http_method} {route_path}")
                
                # Update registry with available methods
                method_names = [m["name"] for m in methods]
                self.canister_registry.update_canister_methods(canister_id, method_names)
                
        except Exception as e:
            logger.error(f"Failed to add routes for canister {canister_id}: {e}")
    
    def _create_canister_method_handler(self, canister_id: str, method_name: str, is_query: bool):
        """Create a dynamic handler for a canister method."""
        async def handler(request):
            try:
                # Update usage tracking
                self.canister_registry.update_canister_usage(canister_id)
                
                # Ensure we have an actor controller for this canister
                if not self.actor_controller:
                    # Set environment and create controller
                    os.environ['M_AUTONOME_CANISTER'] = canister_id
                    self.actor_controller = create_actor_controller('M_AUTONOME')
                    
                    if self.local_identity and self.local_identity.identity:
                        await self.actor_controller.authenticate(self.local_identity.identity)
                
                if not self.actor_controller.get_is_authenticated():
                    return web.json_response(
                        {"error": f"Not authenticated with canister {canister_id}"}, 
                        status=401
                    )
                
                # Get arguments from request
                if request.method == "POST":
                    try:
                        data = await request.json()
                        args = data.get('args', [])
                    except:
                        args = []
                else:
                    # GET request - args from query parameters
                    args = []
                
                # Call the method
                if method_name == 'login':
                    result = await self.actor_controller.login()
                elif method_name == 'register' and len(args) >= 4:
                    result = await self.actor_controller.register(args[0], args[1], args[2], args[3])
                elif method_name == 'getConversations':
                    result = await self.actor_controller.get_conversations()
                else:
                    # Generic method call
                    actor = self.actor_controller.get_actor()
                    if not actor:
                        return web.json_response({"error": "Actor not available"}, status=500)
                    
                    if is_query:
                        result = await actor._query_method(method_name, args)
                    else:
                        result = await actor._call_method(method_name, args)
                
                return web.json_response({
                    "success": True,
                    "canister_id": canister_id,
                    "method": method_name,
                    "result": result,
                    "is_query": is_query
                })
                
            except Exception as e:
                logger.error(f"Error calling {method_name} on {canister_id}: {e}")
                return web.json_response({"error": str(e)}, status=500)
        
        return handler
    
    async def _auto_authenticate_canister(self, canister_id: str) -> bool:
        """Automatically authenticate with a canister when it's added."""
        try:
            logger.info(f"🔐 Auto-authenticating with canister {canister_id}...")
            
            if not self.local_identity or not self.local_identity.identity:
                logger.error("No local identity available for authentication")
                return False
            
            # Set environment for this canister
            os.environ['M_AUTONOME_CANISTER'] = canister_id
            
            # Create new actor controller for this canister
            if self.actor_controller:
                await self.actor_controller.deauthenticate()
            
            self.actor_controller = create_actor_controller('M_AUTONOME')
            
            # Authenticate with the canister
            await self.actor_controller.authenticate(self.local_identity.identity)
            
            if self.actor_controller.get_is_authenticated():
                logger.info(f"✅ Successfully authenticated with canister {canister_id}")
                return True
            else:
                logger.warning(f"⚠️ Authentication with canister {canister_id} failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Auto-authentication failed for {canister_id}: {e}")
            return False

    # Canister management methods
    async def _add_canister(self, request):
        """Add a new canister to the registry."""
        try:
            data = await request.json()
            canister_id = data.get('canister_id')
            name = data.get('name')
            network = data.get('network', 'mainnet')
            
            if not canister_id:
                return web.json_response(
                    {"error": "canister_id is required"}, 
                    status=400
                )
            
            # Add to registry
            success = self.canister_registry.add_canister(canister_id, name, network)
            
            if not success:
                return web.json_response(
                    {"error": f"Canister {canister_id} already exists"}, 
                    status=409
                )
            
            # Add dynamic routes for this canister
            self._add_canister_routes(canister_id)
            
            # Automatically authenticate with the canister
            auth_success = await self._auto_authenticate_canister(canister_id)
            
            return web.json_response({
                "success": True,
                "message": f"Canister {canister_id} added successfully",
                "canister_id": canister_id,
                "name": name,
                "network": network,
                "authenticated": auth_success,
                "principal": self.local_identity.get_principal_id() if self.local_identity else None
            })
            
        except Exception as e:
            logger.error(f"Error adding canister: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def _remove_canister(self, request):
        """Remove a canister from the registry."""
        try:
            canister_id = request.match_info['canister_id']
            
            success = self.canister_registry.remove_canister(canister_id)
            
            if not success:
                return web.json_response(
                    {"error": f"Canister {canister_id} not found"}, 
                    status=404
                )
            
            # TODO: Remove dynamic routes (requires route cleanup)
            
            return web.json_response({
                "success": True,
                "message": f"Canister {canister_id} removed successfully"
            })
            
        except Exception as e:
            logger.error(f"Error removing canister: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def _get_canister_info(self, request):
        """Get information about a specific canister."""
        try:
            canister_id = request.match_info['canister_id']
            
            canister_info = self.canister_registry.get_canister(canister_id)
            
            if not canister_info:
                return web.json_response(
                    {"error": f"Canister {canister_id} not found"}, 
                    status=404
                )
            
            return web.json_response({
                "success": True,
                "canister": {
                    "id": canister_id,
                    **canister_info
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting canister info: {e}")
            return web.json_response({"error": str(e)}, status=500)
    

    
    async def _list_canisters(self, request):
        """List all registered canisters"""
        try:
            canisters = self.canister_registry.list_canisters()
            
            return web.json_response({
                "success": True,
                "canisters": canisters,
                "count": len(canisters)
            })
            
        except Exception as e:
            logger.error(f"Error listing canisters: {e}")
            return web.json_response({"error": str(e)}, status=500)

if __name__ == "__main__":
    try:
        addon = ICPIdentityAddon()
        asyncio.run(addon.start())
    except KeyboardInterrupt:
        logger.info("Addon stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        exit(1) 