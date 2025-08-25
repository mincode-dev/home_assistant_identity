from typing import Dict
from actor_controller.actor import ICActor
from identity.ic_identity import ICIdentity
from identity.ic_private_key import ICPrivateKey
from actor_controller.agent import ICAgent

class IdentityManager:
    
    def __init__(self):
        self._private_key = ICPrivateKey()
        self._identity = ICIdentity(self._private_key.private_key)
        self._actors : Dict[str, ICActor] = {}
        self._canisters : Dict[str, str] = {}
        self._host = "https://icp-api.io"
    
    @property
    def identity(self):
        return self._identity


    def add_canister(self, canister_id: str, canister_name: str):
        new_agent = ICAgent(self._identity.identity, self._host)
        new_actor = ICActor(new_agent, canister_id)
        self._canisters[canister_name] = canister_id
        self._actors[canister_id] = new_actor
        return True
    
    def call_canister_method(self, canister_name: str, method_name: str, args: list):
        if canister_name not in self._canisters:
            raise ValueError(f"Canister {canister_name} not found")
        return self._actors[self._canisters[canister_name]].call_method(method_name, args)
    
    def get_canister_id(self, canister_name: str):
        if canister_name not in self._canisters:
            raise ValueError(f"Canister {canister_name} not found")
        return self._canisters[canister_name]

    def get_canister_info(self, canister_name: str):
        if canister_name not in self._canisters:
            raise ValueError(f"Canister {canister_name} not found")
        return {
            'name': canister_name,
            'id': self._canisters[canister_name]
        }
    
    def list_canisters(self):
        return list(self._canisters.keys())

    def get_canister_actor(self, canister_name: str):
        if canister_name not in self._canisters:
            raise ValueError(f"Canister {canister_name} not found")
        return self._actors[self._canisters[canister_name]]

    def get_canister_methods(self, canister_name: str):
        if canister_name not in self._canisters:
            raise ValueError(f"Canister {canister_name} not found")
        return self._actors[self._canisters[canister_name]].get_methods()

    def regenerate_identity(self):
        self._private_key = ICPrivateKey(regenerate=True)
        self._identity = ICIdentity(self._private_key.private_key)
        self._actors = {}
        self._canisters = {}
        return self._identity