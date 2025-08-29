import asyncio
import logging
import signal
from .api.api import ApiServer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    api_server = ApiServer(host="0.0.0.0", port=8099)

    # Event we set when a shutdown signal arrives
    stop_event = asyncio.Event()

    # Register signal handlers (Unix). On Windows, SIGINT works; SIGTERM may not.
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            # Platform (e.g., Windows) might not support this signal
            pass

    await api_server.start()
    logger.info("API server started on port 8099")

    try:
        # Block here until a stop signal is received
        await stop_event.wait()
    finally:
        logger.info("Shutting down API server...")
        # Make sure your ApiServer has a proper async shutdown/close
        await api_server.stop()
        logger.info("Shutdown complete.")

    
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Fallback if signals aren’t registered
        pass
