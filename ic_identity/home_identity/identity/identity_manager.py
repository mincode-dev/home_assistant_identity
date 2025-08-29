import json
import logging
import os
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Optional

from ..actor_controller.actor import ICActor
from ..actor_controller.agent import ICAgent
from .ic_identity import ICIdentity
from .ic_private_key import ICPrivateKey

logger = logging.getLogger(__name__)


class IdentityManager:
    """
    Manages the current IC identity, a registry of canisters (name -> id),
    and ICActor instances (keyed by canister_id).
    Persists the registry to DATA_DIR/canisters/canisters.json.
    """

    def __init__(self, *, host: str = "https://icp-api.io"):
        self._host = host

        # Identity (private key handling stays in your ICPrivateKey/ICIdentity classes)
        self._private_key = ICPrivateKey()
        self._identity = ICIdentity(self._private_key.private_key)

        # Runtime registries
        self._actors: Dict[str, ICActor] = {}    # canister_id -> ICActor
        self._canisters: Dict[str, str] = {}     # name -> canister_id

        # Persistence base (env DATA_DIR or project ./data)
        base_data_dir = os.getenv("DATA_DIR") or (Path(__file__).parent.parent / "data")
        self._data_dir = Path(base_data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)

        # Save registry specifically under data/canisters/canisters.json
        self._canisters_dir = self._data_dir / "canisters"
        self._canisters_dir.mkdir(parents=True, exist_ok=True)
        self._canisters_file = self._canisters_dir / "canisters.json"

        # Concurrency guard
        self._lock = RLock()

        self._load_canisters()

    @property
    def identity(self) -> ICIdentity:
        return self._identity

    # ---------- persistence ----------
    def _load_canisters(self) -> None:
        """Load canisters from persistent storage on startup."""
        if not self._canisters_file.exists():
            logger.debug("No canisters file at %s", self._canisters_file)
            return

        try:
            with open(self._canisters_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            can_map = data.get("canisters", {})
            if not isinstance(can_map, dict):
                logger.warning("Invalid canisters.json format; ignoring.")
                return

            bad_names = []
            for name, canister_id in can_map.items():
                try:
                    agent = ICAgent(self._identity.identity, self._host)
                    actor = ICActor(agent, canister_id)
                    self._actors[canister_id] = actor
                except Exception as e:
                    bad_names.append(name)
                    logger.warning("Failed to recreate actor for %s (%s): %s", name, canister_id, e)

            with self._lock:
                self._canisters = {n: c for n, c in can_map.items() if n not in bad_names}

            if bad_names:
                logger.info("Dropping invalid entries: %s", ", ".join(bad_names))
                self._save_canisters()

            logger.info("Loaded %d canister(s).", len(self._canisters))

        except Exception as e:
            logger.error("Failed to load canisters: %s", e)

    def _save_canisters(self) -> None:
        """Save canisters to persistent storage with an atomic replace."""
        try:
            payload = {
                "canisters": self._canisters,
                "last_updated": datetime.now().isoformat(),
                "version": "1.0",
            }

            # Create a temp file in the same directory, then atomically replace
            tmp_path = self._canisters_file.with_name(self._canisters_file.name + ".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)

            tmp_path.replace(self._canisters_file)
            logger.debug("Saved %d canister(s) to %s", len(self._canisters), self._canisters_file)

        except Exception as e:
            logger.error("Failed to save canisters: %s", e)

    # ---------- registry ops ----------
    def add_canister(self, canister_id: str, canister_name: Optional[str] = None) -> bool:
        """Register a canister and prepare its ICActor."""
        if not canister_id:
            raise ValueError("canister_id is required")

        name = (canister_name or canister_id).strip()

        agent = ICAgent(self._identity.identity, self._host)
        actor = ICActor(agent, canister_id)

        with self._lock:
            self._canisters[name] = canister_id
            self._actors[canister_id] = actor
            self._save_canisters()

        logger.info("Registered canister %s -> %s", name, canister_id)
        return True

    def delete_canister(self, canister_name: str) -> bool:
        """Remove a canister from the registry and drop its actor."""
        if not canister_name:
            raise ValueError("canister_name is required")

        with self._lock:
            if canister_name not in self._canisters:
                raise ValueError(f"Canister {canister_name} not found")

            canister_id = self._canisters.pop(canister_name)

            # Drop actor if no other name references the same id
            if canister_id not in self._canisters.values():
                self._actors.pop(canister_id, None)

            self._save_canisters()

        logger.info("Deleted canister %s", canister_name)
        return True

    async def call_canister_method(self, canister_name: str, method_name: str, args: Optional[list] = None) -> Any:
        """Call a canister method via its actor. Returns the decoded result."""
        if canister_name not in self._canisters:
            raise ValueError(f"Canister {canister_name} not found")

        canister_id = self._canisters[canister_name]
        actor = self._actors.get(canister_id)
        if actor is None:
            agent = ICAgent(self._identity.identity, self._host)
            actor = ICActor(agent, canister_id)
            self._actors[canister_id] = actor

        return await actor.call_method(method_name, args or [])

    def get_canister_id(self, canister_name: str) -> str:
        if canister_name not in self._canisters:
            raise ValueError(f"Canister {canister_name} not found")
        return self._canisters[canister_name]

    def get_canister_info(self, canister_name: str) -> Dict[str, str]:
        return {"name": canister_name, "id": self.get_canister_id(canister_name)}

    def list_canisters(self) -> list[str]:
        return list(self._canisters.keys())

    def get_canister_actor(self, canister_name: str) -> ICActor:
        canister_id = self.get_canister_id(canister_name)
        actor = self._actors.get(canister_id)
        if actor is None:
            agent = ICAgent(self._identity.identity, self._host)
            actor = ICActor(agent, canister_id)
            self._actors[canister_id] = actor
        return actor

    def get_canister_methods(self, canister_name: str) -> list[str]:
        return self.get_canister_actor(canister_name).get_methods()

    # ---------- identity rotation ----------
    def regenerate_identity(self) -> ICIdentity:
        """Replace the current identity and clear registry/actors."""
        self._private_key = ICPrivateKey(regenerate=True)
        self._identity = ICIdentity(self._private_key.private_key)

        with self._lock:
            self._actors.clear()
            self._canisters.clear()
            self._save_canisters()

        logger.info("Identity regenerated; registry cleared.")
        return self._identity
