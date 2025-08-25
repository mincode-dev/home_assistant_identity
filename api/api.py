import logging
from aiohttp import web

from api.controllers.canister_controller import CanisterController
from api.controllers.identity_controller import IdentityController
from identity.identity_manager import IdentityManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ApiServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.identity_manager = IdentityManager()
        self.identity_controller = IdentityController(self.identity_manager)
        self.canister_controller = CanisterController(self.identity_manager)

    async def start(self):
        self._setup_web_routes()
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()

    def _setup_web_routes(self):
        self.app.router.add_get('/', self._health_response)
        self.app.router.add_get('/api/v1/health', self._health_response)
        self.app.router.add_get('/api/v1/identity', self.identity_controller.get_identity)
        self.app.router.add_get('/api/v1/identity/regenerate', self.identity_controller.regenerate_identity)

        self.app.router.add_get('/api/v1/canisters', self.canister_controller.get_canisters)
        self.app.router.add_get('/api/v1/canisters/{canister_name}', self.canister_controller.get_canister)
        self.app.router.add_post('/api/v1/canisters/add', self.canister_controller.add_canister)
        self.app.router.add_post('/api/v1/canisters/call', self.canister_controller.call_canister)
        self.app.router.add_get('/api/v1/canisters/methods/{canister_name}', self.canister_controller.get_canister_methods)
        self.app.router.add_delete('/api/v1/canisters/delete/{canister_name}', self.canister_controller.delete_canister)

        self.app.middlewares.append(self.cors_middleware)
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

    @web.middleware
    async def cors_middleware(self,request, handler):
        # Handle preflight quickly
        if request.method == 'OPTIONS':
            resp = web.Response(status=204)
        else:
            resp = await handler(request)

        origin = request.headers.get('Origin', '*')
        req_hdrs = request.headers.get('Access-Control-Request-Headers', '*')

        resp.headers['Access-Control-Allow-Origin'] = origin  # or '*' if you prefer
        resp.headers['Vary'] = 'Origin'
        resp.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = req_hdrs
        resp.headers['Access-Control-Max-Age'] = '86400'
        return resp

    def _health_response(self, request: web.Request):
        return web.json_response({'status': 'up'}, status=200)
        

    async def stop(self):
        runner = web.AppRunner(self.app)
        await runner.cleanup()
        
        