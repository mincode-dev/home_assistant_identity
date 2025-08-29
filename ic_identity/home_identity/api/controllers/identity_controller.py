from aiohttp import web
from typing import Dict, Any
from ...identity.identity_manager import IdentityManager

class IdentityController:
    def __init__(self, identity_manager: IdentityManager):
        self.identity_manager = identity_manager
    
    async def get_identity(self, request: web.Request) -> web.Response:
        """Get current identity."""
        try:
            identity = self.identity_manager.identity
            return web.json_response({
                'status': 'success',
                'identity': {
                    'principal': identity.principal,
                    'public_key': identity.public_key,
                }
            })
        except Exception as e:
            return web.json_response({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    async def regenerate_identity(self, request: web.Request) -> web.Response:
        """Regenerate identity."""
        try:
            new_identity = self.identity_manager.regenerate_identity()
            return web.json_response({
                'status': 'success',
                'identity': {
                    'principal': new_identity.principal,
                    'public_key': new_identity.public_key,
                }
            })
        except Exception as e:
            return web.json_response({
                'status': 'error',
                'message': str(e)
            }, status=500)
