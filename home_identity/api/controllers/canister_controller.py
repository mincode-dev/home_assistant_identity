from aiohttp import web
from typing import Dict, Any

from identity.identity_manager import IdentityManager

class CanisterController:
    def __init__(self, identity_manager: IdentityManager):
        self.identity_manager = identity_manager
    
    async def get_canisters(self, request: web.Request) -> web.Response:
        """Get all canisters."""
        try:
            canisters = self.identity_manager.list_canisters()
            return web.json_response({
                'status': 'success',
                'canisters': canisters
            })
        except Exception as e:
            return web.json_response({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    async def get_canister(self, request: web.Request) -> web.Response:
        """Get a canister."""
        try:
            canister_name = request.match_info['canister_name']
            canister_info = self.identity_manager.get_canister_info(canister_name)
            return web.json_response({
                'status': 'success',
                'canister': canister_info
            })
        except Exception as e:
            return web.json_response({
                'status': 'error',
                'message': str(e)
            }, status=500)

    async def add_canister(self, request: web.Request) -> web.Response:
        """Add a new canister."""
        try:
            data = await request.json()
            canister_id = data.get('canister_id')
            canister_name = data.get('canister_name')
            if not canister_id:
                return web.json_response({
                    'status': 'error',
                    'message': 'canister_id is required'
                }, status=400)
            
            result = self.identity_manager.add_canister(canister_id, canister_name)
            return web.json_response({
                'status': 'success',
                'result': result
            }, status=201)
        except Exception as e:
            return web.json_response({
                'status': 'error',
                'message': str(e)
            }, status=500) 

    async def call_canister(self, request: web.Request) -> web.Response:
        """Call a canister."""
        try:
            data = await request.json()
            canister_name = data.get('canister_name')
            method_name = data.get('method_name')
            args = data.get('args')
            print(f"Calling canister {canister_name} method {method_name} with args {args}")
        except Exception as e:
            return web.json_response({
                'status': 'error',
                'message': str(e)
            }, status=500)
        
        result = await self.identity_manager.call_canister_method(canister_name, method_name, args)
        return web.json_response({
            'status': 'success',
            'result': result
        }, status=200)

    async def delete_canister(self, request: web.Request) -> web.Response:
        """Delete a canister."""
        try:
            canister_name = request.match_info['canister_name']
            self.identity_manager.delete_canister(canister_name)
            return web.json_response({
                'status': 'success'
            }, status=200)
        except Exception as e:
            return web.json_response({
                'status': 'error',
                'message': str(e)
            }, status=500)

    async def get_canister_methods(self, request: web.Request) -> web.Response:
        """Get the methods of a canister."""
        try:
            canister_name = request.match_info['canister_name']
            methods = self.identity_manager.get_canister_methods(canister_name)
            return web.json_response({
                'status': 'success',
                'methods': methods
            }, status=200)
        except Exception as e:
            return web.json_response({
                'status': 'error',
                'message': str(e)
            }, status=500)


    
