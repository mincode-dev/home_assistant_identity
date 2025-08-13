import os
import json
import asyncio
import logging
import aiohttp.web
from aiohttp import web
from icp_identity import ICPIdentityManager
from ha_integration import HomeAssistantIntegration
from storage import IdentityStorage
from actor_controller import CanisterRegistry, create_actor_controller
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ICPIdentityAddon:
    def __init__(self):
        self.icp_manager = ICPIdentityManager(data_path="../test_data")
        self.ha_integration = HomeAssistantIntegration(self.icp_manager)
        self.storage = IdentityStorage(data_path="../test_data")
        self.canister_registry = CanisterRegistry()
        self.app = aiohttp.web.Application()
        
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
        
        # Canister interaction endpoints
        self.app.router.add_post('/canister/register', self._register_canister)
        self.app.router.add_post('/canister/call', self._call_canister_method)
        self.app.router.add_post('/canister/query', self._query_canister_method)
        self.app.router.add_get('/canister/list', self._list_canisters)
        self.app.router.add_post('/canister/authenticate', self._authenticate_canisters)
        
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
        """Enhanced web dashboard with error handling"""
        try:
            stats = self.storage.get_storage_stats()
            backups = self.storage.list_backups()
            identity_info = self.icp_manager.get_identity_info()
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>ICP Identity Manager</title>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; background: #f5f5f5; }}
                    .container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
                    .header {{ text-align: center; margin-bottom: 30px; padding: 30px; background: white; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .info-box {{ background: white; padding: 25px; border-radius: 12px; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .button {{ background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; margin: 8px; font-weight: 500; transition: all 0.2s; }}
                    .button:hover {{ background: #0056b3; transform: translateY(-1px); }}
                    .button.danger {{ background: #dc3545; }}
                    .button.danger:hover {{ background: #c82333; }}
                    .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin: 25px 0; }}
                    .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px; text-align: center; }}
                    .stat-card h4 {{ margin: 0 0 10px 0; font-size: 14px; opacity: 0.9; }}
                    .stat-card p {{ margin: 0; font-size: 24px; font-weight: bold; }}
                    .status-badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
                    .status-connected {{ background: #d4edda; color: #155724; }}
                    code {{ background: #f8f9fa; padding: 4px 8px; border-radius: 4px; font-family: 'Monaco', 'Consolas', monospace; font-size: 13px; }}
                    .network-info {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🏠 ICP Identity Manager</h1>
                        <p>Home Assistant Internet Computer Protocol Integration</p>
                        <div class="status-badge status-connected">Connected</div>
                    </div>
                    
                    <div class="info-box">
                        <h3>Identity Information</h3>
                        <p><strong>Principal:</strong> <code>{identity_info['principal']}</code></p>
                        <p><strong>Public Key:</strong> <code>{identity_info['public_key'][:32]}...</code></p>
                        <div class="network-info">
                            <strong>Network:</strong> {identity_info['network'].upper()} 
                            <small>({identity_info.get('agent_url', 'N/A')})</small>
                        </div>
                    </div>
                    
                    <div class="stats">
                        <div class="stat-card">
                            <h4>Backup Files</h4>
                            <p>{stats['backup_count']}</p>
                        </div>
                        <div class="stat-card">
                            <h4>Data Size</h4>
                            <p>{stats['data_size_mb']:.1f} MB</p>
                        </div>
                        <div class="stat-card">
                            <h4>Backup Size</h4>
                            <p>{stats['backup_size_mb']:.1f} MB</p>
                        </div>
                        <div class="stat-card">
                            <h4>Mnemonic Status</h4>
                            <p>{'✅ Stored' if identity_info['has_mnemonic'] else '❌ Missing'}</p>
                        </div>
                    </div>
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <button class="button" onclick="createBackup()">📦 Create Backup</button>
                        <button class="button" onclick="window.open('/stats', '_blank')">📊 View Stats</button>
                        <button class="button danger" onclick="regenerateIdentity()">🔄 Regenerate Identity</button>
                    </div>
                    
                    <div class="info-box">
                        <h3>Recent Backups</h3>
                        {'<p>No backups available</p>' if not backups else ''.join([f'<p>📁 {backup["created_at"][:19].replace("T", " ")}</p>' for backup in backups[:5]])}
                    </div>
                </div>
                
                <script>
                    async function regenerateIdentity() {{
                        if (confirm('⚠️ This will generate a new identity and cannot be undone.\\n\\nA backup will be created automatically.\\n\\nContinue?')) {{
                            try {{
                                const response = await fetch('/regenerate', {{method: 'POST'}});
                                if (response.ok) {{
                                    alert('✅ Identity regenerated successfully!\\nOld identity backed up automatically.');
                                    location.reload();
                                }} else {{
                                    const error = await response.text();
                                    alert('❌ Failed to regenerate identity: ' + error);
                                }}
                            }} catch (error) {{
                                alert('❌ Network error: ' + error.message);
                            }}
                        }}
                    }}
                    
                    async function createBackup() {{
                        try {{
                            const response = await fetch('/backup', {{method: 'POST'}});
                            if (response.ok) {{
                                alert('✅ Backup created successfully!');
                                location.reload();
                            }} else {{
                                const error = await response.text();
                                alert('❌ Failed to create backup: ' + error);
                            }}
                        }} catch (error) {{
                            alert('❌ Network error: ' + error.message);
                        }}
                    }}
                </script>
            </body>
            </html>
            """
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
    
    # Canister interaction methods
    async def _register_canister(self, request):
        """Register a new canister for interaction"""
        try:
            data = await request.json()
            name = data.get('name')
            canister_id = data.get('canister_id')
            
            if not name or not canister_id:
                return web.json_response(
                    {"error": "name and canister_id are required"}, 
                    status=400
                )
            
            # Register canister
            controller = self.canister_registry.register_canister(name, canister_id)
            
            return web.json_response({
                "success": True,
                "message": f"Canister {name} registered successfully",
                "canister_info": controller.get_canister_info()
            })
            
        except Exception as e:
            logger.error(f"Error registering canister: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def _authenticate_canisters(self, request):
        """Authenticate all registered canisters with current identity"""
        try:
            if not self.icp_manager.identity:
                return web.json_response(
                    {"error": "No identity available. Generate identity first."}, 
                    status=400
                )
            
            # Authenticate all canisters
            results = await self.canister_registry.authenticate_all(self.icp_manager.identity)
            
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            
            return web.json_response({
                "success": True,
                "message": f"Authentication completed: {success_count}/{total_count} successful",
                "results": results
            })
            
        except Exception as e:
            logger.error(f"Error authenticating canisters: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def _call_canister_method(self, request):
        """Call a method on a registered canister"""
        try:
            data = await request.json()
            canister_name = data.get('canister_name')
            method = data.get('method')
            args = data.get('args', [])
            
            if not canister_name or not method:
                return web.json_response(
                    {"error": "canister_name and method are required"}, 
                    status=400
                )
            
            # Get canister controller
            controller = self.canister_registry.get_controller(canister_name)
            if not controller:
                return web.json_response(
                    {"error": f"Canister {canister_name} not found. Register it first."}, 
                    status=404
                )
            
            # Call method
            result = await controller.call_method(method, args)
            
            return web.json_response({
                "success": True,
                "result": result,
                "canister_name": canister_name,
                "method": method,
                "args": args
            })
            
        except Exception as e:
            logger.error(f"Error calling canister method: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def _query_canister_method(self, request):
        """Query a method on a registered canister (read-only)"""
        try:
            data = await request.json()
            canister_name = data.get('canister_name')
            method = data.get('method')
            args = data.get('args', [])
            
            if not canister_name or not method:
                return web.json_response(
                    {"error": "canister_name and method are required"}, 
                    status=400
                )
            
            # Get canister controller
            controller = self.canister_registry.get_controller(canister_name)
            if not controller:
                return web.json_response(
                    {"error": f"Canister {canister_name} not found. Register it first."}, 
                    status=404
                )
            
            # Query method
            result = await controller.query_method(method, args)
            
            return web.json_response({
                "success": True,
                "result": result,
                "canister_name": canister_name,
                "method": method,
                "args": args
            })
            
        except Exception as e:
            logger.error(f"Error querying canister method: {e}")
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