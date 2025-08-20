import os
import asyncio
import logging
import aiohttp
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class HomeAssistantIntegration:
    def __init__(self, icp_manager):
        self.icp_manager = icp_manager
        
        # Auto-detect HA environment and configure accordingly
        if os.environ.get('SUPERVISOR_TOKEN'):
            # Running as HA addon (Supervised/OS)
            self.ha_url = "http://supervisor/core/api"
            self.supervisor_token = os.environ.get('SUPERVISOR_TOKEN')
            logger.info("🏠 Detected Home Assistant addon environment")
        elif os.environ.get('HA_TOKEN'):
            # Running as external container with HA token
            self.ha_url = "http://localhost:8123/api"
            self.supervisor_token = os.environ.get('HA_TOKEN')
            logger.info("🐳 Detected external container with HA token")
        else:
            # Fallback - try to connect to local HA
            self.ha_url = "http://localhost:8123/api"
            self.supervisor_token = None
            logger.warning("⚠️  No HA token found - sensor creation will be skipped")
            logger.info("💡 For HA integration, provide SUPERVISOR_TOKEN (addon) or HA_TOKEN (external)")
        
        self.headers = {
            "Authorization": f"Bearer {self.supervisor_token}",
            "Content-Type": "application/json"
        } if self.supervisor_token else {}
        
    async def register_icp_sensors(self):
        """Register ICP identity as HA sensors with retry logic"""
        try:
            logger.info("Registering ICP sensors with Home Assistant...")
            
            # Get identity info
            identity_info = self.icp_manager.get_identity_info()
            
            # ICP Principal sensor
            await self._create_sensor_with_retry("sensor.icp_principal", {
                "name": "ICP Principal ID",
                "state": identity_info["principal"],
                "attributes": {
                    "friendly_name": "ICP Principal ID",
                    "icon": "mdi:account-key",
                    "public_key": identity_info["public_key"][:32] + "...",
                    "full_public_key": identity_info["public_key"],
                    "created_at": datetime.now().isoformat(),
                    "network": identity_info["network"],
                    "device_class": "none",
                    "unit_of_measurement": None
                }
            })
            
            # ICP Connection Status sensor
            connection_state = await self._test_icp_connection()
            await self._create_sensor_with_retry("sensor.icp_connection", {
                "name": "ICP Connection Status", 
                "state": connection_state,
                "attributes": {
                    "friendly_name": "ICP Network Status",
                    "icon": "mdi:network" if connection_state == "connected" else "mdi:network-off",
                    "network": identity_info["network"],
                    "agent_url": identity_info.get("agent_url", "N/A"),
                    "last_checked": datetime.now().isoformat(),
                    "device_class": "connectivity"
                }
            })
            
            # ICP Identity Info sensor
            await self._create_sensor_with_retry("sensor.icp_identity_info", {
                "name": "ICP Identity Info",
                "state": "initialized",
                "attributes": {
                    "friendly_name": "ICP Identity Information",
                    "icon": "mdi:information",
                    "principal": identity_info["principal"],
                    "network": identity_info["network"],
                    "has_mnemonic": identity_info["has_mnemonic"],
                    "identity_file_exists": os.path.exists(identity_info["identity_file"]),
                    "created_at": datetime.now().isoformat()
                }
            })
            
            logger.info("✅ All ICP sensors registered successfully with Home Assistant")
            
        except Exception as e:
            logger.error(f"Failed to register ICP sensors: {e}")
            raise
            
    async def _test_icp_connection(self):
        """Test ICP network connectivity"""
        try:
            if not self.icp_manager.agent:
                return "disconnected"
                
            # Simple connectivity test - this would be expanded based on ic-py capabilities
            # For now, just check if agent is initialized
            return "connected" if self.icp_manager.agent else "disconnected"
            
        except Exception as e:
            logger.warning(f"ICP connection test failed: {e}")
            return "error"
        
    async def _create_sensor_with_retry(self, entity_id, data, max_retries=3):
        """Create/update sensor with retry logic"""
        for attempt in range(max_retries):
            try:
                await self._create_sensor(entity_id, data)
                return
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {entity_id}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
        
    async def _create_sensor(self, entity_id, data):
        """Create/update sensor in Home Assistant"""
        if not self.supervisor_token:
            logger.warning(f"Cannot create sensor {entity_id}: No supervisor token")
            return
            
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = f"{self.ha_url}/states/{entity_id}"
                
                payload = {
                    "state": data["state"],
                    "attributes": data["attributes"]
                }
                
                async with session.post(url, headers=self.headers, json=payload) as resp:
                    if resp.status == 200:
                        logger.info(f"✅ Created/updated HA sensor: {entity_id}")
                    elif resp.status == 401:
                        logger.error(f"❌ Authentication failed for {entity_id} - check SUPERVISOR_TOKEN")
                        raise aiohttp.ClientResponseError(
                            request_info=resp.request_info,
                            history=resp.history,
                            status=resp.status,
                            message="Authentication failed"
                        )
                    else:
                        error_text = await resp.text()
                        logger.error(f"❌ Failed to create sensor {entity_id}: {resp.status} - {error_text}")
                        raise aiohttp.ClientResponseError(
                            request_info=resp.request_info,
                            history=resp.history,
                            status=resp.status,
                            message=error_text
                        )
                        
        except aiohttp.ClientError as e:
            logger.error(f"Network error creating sensor {entity_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating sensor {entity_id}: {e}")
            raise
                    
    async def update_sensor_states(self):
        """Update sensor states with current information"""
        try:
            logger.info("Updating ICP sensor states...")
            
            # Update connection status
            connection_state = await self._test_icp_connection()
            await self._create_sensor("sensor.icp_connection", {
                "name": "ICP Connection Status",
                "state": connection_state,
                "attributes": {
                    "friendly_name": "ICP Network Status",
                    "icon": "mdi:network" if connection_state == "connected" else "mdi:network-off",
                    "network": self.icp_manager.network,
                    "last_checked": datetime.now().isoformat(),
                    "device_class": "connectivity"
                }
            })
            
            logger.info("✅ Sensor states updated successfully")
            
        except Exception as e:
            logger.error(f"Failed to update sensor states: {e}")
            
    async def provide_icp_service(self):
        """Provide ICP service calls to other HA integrations"""
        # This could expose canister calls as HA services
        # Implementation would depend on specific Home Assistant service requirements
        logger.info("ICP service integration ready (expandable for future services)")
        pass
        
    async def notify_identity_change(self, old_principal=None, new_principal=None):
        """Notify Home Assistant of identity changes"""
        try:
            logger.info("Notifying Home Assistant of identity change...")
            
            # Re-register sensors with new identity
            await self.register_icp_sensors()
            
            # Could send notification to HA notification service
            if old_principal and new_principal:
                logger.info(f"Identity changed: {old_principal} → {new_principal}")
                
        except Exception as e:
            logger.error(f"Failed to notify identity change: {e}")
            
    def get_integration_status(self):
        """Get integration status information"""
        return {
            "supervisor_token_available": bool(self.supervisor_token),
            "ha_api_url": self.ha_url,
            "integration_active": bool(self.supervisor_token),
            "last_update": datetime.now().isoformat()
        } 