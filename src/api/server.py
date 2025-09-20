"""
Bot API Server for Management Portal Integration

FastAPI server that runs alongside the Discord bot to provide API endpoints
for the Management Portal to control voice tracking and access bot data.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
import asyncio
import logging
from datetime import datetime
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.mining.events import MiningEventManager
from modules.mining.participation import VoiceTracker
from modules.payroll.processors.mining import MiningProcessor
from config.settings import get_sunday_mining_channels

logger = logging.getLogger(__name__)

# Pydantic models for API requests
class StartTrackingRequest(BaseModel):
    event_id: str = Field(..., description="Event ID to start tracking for")
    guild_id: int = Field(..., description="Discord guild ID")
    channels: Optional[Dict[str, str]] = Field(None, description="Channel configuration override")

class StopTrackingRequest(BaseModel):
    event_id: str = Field(..., description="Event ID to stop tracking for")

class PriceRefreshRequest(BaseModel):
    force_refresh: bool = Field(True, description="Force refresh from UEX API")

# Global references to bot components
bot_instance = None
voice_tracker = None
event_manager = None

class BotAPI:
    """API server for bot integration with Management Portal."""

    def __init__(self):
        self.app = FastAPI(
            title="Red Legion Bot API",
            description="API endpoints for Management Portal integration",
            version="1.0.0"
        )

        # Configure CORS for portal access
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Portal dev servers
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self._setup_routes()

    def _setup_routes(self):
        """Setup API routes."""

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "bot_connected": bot_instance is not None and bot_instance.is_ready(),
                "timestamp": datetime.now().isoformat()
            }

        @self.app.post("/events/{event_id}/start-tracking")
        async def start_voice_tracking(event_id: str, request: StartTrackingRequest):
            """Start voice channel tracking for an event."""
            try:
                if not voice_tracker:
                    raise HTTPException(status_code=503, detail="Voice tracker not available")

                # Get channel configuration
                channels = request.channels
                if not channels:
                    channels = get_sunday_mining_channels(request.guild_id)

                if not channels:
                    raise HTTPException(status_code=400, detail="No channels configured for tracking")

                # Start tracking
                result = await voice_tracker.start_tracking(event_id, channels)

                if not result['success']:
                    raise HTTPException(status_code=400, detail=result['error'])

                return {
                    "success": True,
                    "event_id": event_id,
                    "channels_tracked": len(channels),
                    "message": "Voice tracking started successfully"
                }

            except Exception as e:
                logger.error(f"Error starting voice tracking for {event_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/events/{event_id}/stop-tracking")
        async def stop_voice_tracking(event_id: str):
            """Stop voice channel tracking for an event."""
            try:
                if not voice_tracker:
                    raise HTTPException(status_code=503, detail="Voice tracker not available")

                await voice_tracker.stop_tracking(event_id)

                return {
                    "success": True,
                    "event_id": event_id,
                    "message": "Voice tracking stopped successfully"
                }

            except Exception as e:
                logger.error(f"Error stopping voice tracking for {event_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/events/{event_id}/participants")
        async def get_event_participants(event_id: str):
            """Get current participants for an event."""
            try:
                if not voice_tracker:
                    raise HTTPException(status_code=503, detail="Voice tracker not available")

                participants = await voice_tracker.get_current_participants(event_id)

                return {
                    "event_id": event_id,
                    "participants": participants,
                    "total_active": len(participants),
                    "timestamp": datetime.now().isoformat()
                }

            except Exception as e:
                logger.error(f"Error getting participants for {event_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/prices/current")
        async def get_current_prices(force_refresh: bool = False):
            """Get current UEX ore prices."""
            try:
                processor = MiningProcessor()
                prices = await processor.get_current_prices(refresh=force_refresh)

                if not prices:
                    raise HTTPException(status_code=503, detail="Unable to fetch ore prices")

                return {
                    "success": True,
                    "prices": prices,
                    "total_ores": len(prices),
                    "timestamp": datetime.now().isoformat(),
                    "cached": not force_refresh
                }

            except Exception as e:
                logger.error(f"Error fetching ore prices: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/prices/refresh")
        async def refresh_prices(background_tasks: BackgroundTasks):
            """Force refresh UEX ore prices."""
            try:
                # Run price refresh in background
                async def refresh_task():
                    processor = MiningProcessor()
                    await processor.get_current_prices(refresh=True)

                background_tasks.add_task(refresh_task)

                return {
                    "success": True,
                    "message": "Price refresh started in background",
                    "timestamp": datetime.now().isoformat()
                }

            except Exception as e:
                logger.error(f"Error refreshing prices: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/discord/channels/{guild_id}")
        async def get_discord_channels(guild_id: int):
            """Get Discord voice channels for a guild."""
            try:
                if not bot_instance:
                    raise HTTPException(status_code=503, detail="Bot instance not available")

                if not bot_instance.is_ready():
                    raise HTTPException(status_code=503, detail="Bot not ready")

                # Find the guild
                guild = bot_instance.get_guild(guild_id)
                if not guild:
                    raise HTTPException(status_code=404, detail=f"Guild {guild_id} not found")

                # Get voice channels
                voice_channels = []
                for channel in guild.voice_channels:
                    voice_channels.append({
                        "id": str(channel.id),
                        "name": channel.name,
                        "type": "voice",
                        "category": channel.category.name if channel.category else None,
                        "user_count": len(channel.members),
                        "position": channel.position
                    })

                # Sort by position
                voice_channels.sort(key=lambda x: x["position"])

                return {
                    "channels": voice_channels,
                    "guild_id": guild_id,
                    "guild_name": guild.name,
                    "total_channels": len(voice_channels),
                    "timestamp": datetime.now().isoformat()
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error fetching Discord channels for guild {guild_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/bot/status")
        async def get_bot_status():
            """Get detailed bot status information."""
            try:
                if not bot_instance:
                    return {"connected": False, "error": "Bot instance not available"}

                guild_count = len(bot_instance.guilds)
                latency = round(bot_instance.latency * 1000, 2)  # Convert to ms

                # Get voice client info
                voice_connections = []
                for guild in bot_instance.guilds:
                    if guild.voice_client:
                        voice_connections.append({
                            "guild_id": guild.id,
                            "guild_name": guild.name,
                            "channel_id": guild.voice_client.channel.id,
                            "channel_name": guild.voice_client.channel.name,
                            "connected": guild.voice_client.is_connected()
                        })

                return {
                    "connected": bot_instance.is_ready(),
                    "latency_ms": latency,
                    "guild_count": guild_count,
                    "voice_connections": voice_connections,
                    "user_id": bot_instance.user.id if bot_instance.user else None,
                    "username": bot_instance.user.name if bot_instance.user else None
                }

            except Exception as e:
                logger.error(f"Error getting bot status: {e}")
                return {"connected": False, "error": str(e)}

def initialize_api(bot, tracker=None, manager=None):
    """Initialize the API server with bot components."""
    global bot_instance, voice_tracker, event_manager
    bot_instance = bot
    voice_tracker = tracker
    event_manager = manager

    api = BotAPI()
    return api.app

async def start_api_server(app, host="0.0.0.0", port=8001):
    """Start the API server."""
    import uvicorn

    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info",
        loop="asyncio"
    )

    server = uvicorn.Server(config)

    try:
        logger.info(f"Starting Bot API server on {host}:{port}")
        await server.serve()
    except Exception as e:
        logger.error(f"Failed to start API server: {e}")
        raise