"""
Python Actor Controller for Internet Computer

A Python implementation of the TypeScript Actor Controller system for 
interacting with Internet Computer (IC) canisters.
"""

__version__ = "1.0.0"
__author__ = "Python IC Team"

from .controllers.actor_controller import ActorController, create_actor_controller
from .identity.ic_identity import ICIdentity, create_ic_identity
from .identity.local_ic_identity import LocalICIdentity, create_local_identity

__all__ = [
    "ActorController",
    "create_actor_controller", 
    "ICIdentity",
    "create_ic_identity",
    "LocalICIdentity", 
    "create_local_identity"
]