"""
Discord Bot Web API for Red Legion

Provides HTTP endpoints that the web interface can use to trigger Discord bot actions.
This enables the web service to start/stop mining events with voice tracking.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from modules.mining.events import MiningEventManager
from modules.mining.participation import VoiceTracker
from config.settings import get_sunday_mining_channels

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app for bot API
bot_api = FastAPI(
    title="Red Legion Discord Bot API",
    description="HTTP API for triggering Discord bot actions from web interface",
    version="1.0.0"
)

# Global bot reference (will be set when bot starts)
discord_bot = None
event_manager = None
voice_tracker = None

class StartEventRequest(BaseModel):
    event_id: str
    event_name: str
    event_type: str = "mining"
    organizer_name: str
    organizer_id: Optional[str] = None
    guild_id: str = "814699481912049704"
    location: Optional[str] = None
    notes: Optional[str] = None

class EventResponse(BaseModel):
    success: bool
    message: str
    event_data: Optional[Dict[str, Any]] = None

def set_bot_instance(bot):
    """Set the Discord bot instance for API operations."""
    global discord_bot, event_manager, voice_tracker
    discord_bot = bot
    event_manager = MiningEventManager()
    voice_tracker = VoiceTracker(bot)
    logger.info("🤖 Discord bot instance set for web API")

@bot_api.get("/")
async def root():
    """Root endpoint for bot API."""
    return {
        "message": "Red Legion Discord Bot API", 
        "version": "1.0.0",
        "bot_connected": discord_bot is not None and not discord_bot.is_closed()
    }

@bot_api.post("/events/start", response_model=EventResponse)
async def start_event_with_voice_tracking(request: StartEventRequest):
    """Start a new event with Discord voice channel tracking."""
    if not discord_bot or discord_bot.is_closed():
        raise HTTPException(status_code=503, detail="Discord bot not connected")
    
    try:
        logger.info(f"🎯 Web API request to start {request.event_type} event: {request.event_id}")
        
        # Check if event already exists in database (created by web interface)
        existing_event = await event_manager.get_event(request.event_id)
        
        if not existing_event:
            # Create the event if it doesn't exist
            create_result = await event_manager.create_event(
                guild_id=request.guild_id,
                organizer_id=request.organizer_id or "web-api",
                organizer_name=request.organizer_name,
                location=request.location,
                notes=request.notes,
                event_id=request.event_id,  # Use the provided event_id
                event_type=request.event_type
            )
            
            if not create_result['success']:
                raise HTTPException(status_code=400, detail=f"Failed to create event: {create_result['error']}")
            
            event_data = create_result['event']
        else:
            event_data = existing_event
        
        # Start voice channel tracking
        guild_id_int = int(request.guild_id) if request.guild_id != "814699481912049704" else 814699481912049704  # Red Legion server ID
        channels = get_sunday_mining_channels(guild_id_int)
        
        if not channels:
            raise HTTPException(status_code=400, detail="No voice channels configured for this server")
        
        tracking_result = await voice_tracker.start_tracking(
            event_id=request.event_id,
            channels=channels
        )
        
        if not tracking_result['success']:
            # If voice tracking fails, still return success but with a warning
            logger.warning(f"Voice tracking failed for event {request.event_id}: {tracking_result['error']}")
            return EventResponse(
                success=True,
                message=f"Event {request.event_id} created but voice tracking failed: {tracking_result['error']}",
                event_data=event_data
            )
        
        # Try to join the dispatch/main channel to indicate active session
        try:
            dispatch_channel_id = channels.get('dispatch')
            if dispatch_channel_id:
                join_success = await voice_tracker.join_voice_channel(int(dispatch_channel_id))
                if join_success:
                    logger.info(f"✅ Bot joined dispatch channel for event {request.event_id}")
                else:
                    logger.warning(f"⚠️ Could not join dispatch channel for event {request.event_id}")
        except Exception as e:
            logger.warning(f"Error joining dispatch channel: {e}")
        
        return EventResponse(
            success=True,
            message=f"Successfully started {request.event_type} event with voice tracking",
            event_data=event_data
        )
        
    except Exception as e:
        logger.error(f"Error starting event via web API: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start event: {str(e)}")

@bot_api.post("/events/{event_id}/stop", response_model=EventResponse) 
async def stop_event_voice_tracking(event_id: str):
    """Stop voice tracking for an event."""
    if not discord_bot or discord_bot.is_closed():
        raise HTTPException(status_code=503, detail="Discord bot not connected")
    
    try:
        logger.info(f"🛑 Web API request to stop event: {event_id}")
        
        # Get the event
        event_data = await event_manager.get_event(event_id)
        if not event_data:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Stop voice tracking
        await voice_tracker.stop_tracking(event_id)
        
        # Leave dispatch channel
        try:
            guild_id_int = int(event_data.get('guild_id', '814699481912049704'))
            if guild_id_int == 814699481912049704:
                guild_id_int = 814699481912049704  # Red Legion server ID
                
            channels = get_sunday_mining_channels(guild_id_int)
            dispatch_channel_id = channels.get('dispatch')
            if dispatch_channel_id:
                await voice_tracker.leave_voice_channel(int(dispatch_channel_id))
        except Exception as e:
            logger.warning(f"Error leaving dispatch channel: {e}")
        
        # Close the event
        close_result = await event_manager.close_event(
            event_id=event_id,
            closed_by_id="web-api",
            closed_by_name="Web Interface"
        )
        
        if not close_result['success']:
            logger.warning(f"Event close failed: {close_result['error']}")
        
        return EventResponse(
            success=True,
            message=f"Successfully stopped event {event_id}",
            event_data=event_data
        )
        
    except Exception as e:
        logger.error(f"Error stopping event via web API: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop event: {str(e)}")

@bot_api.get("/bot/status")
async def get_bot_status():
    """Get Discord bot connection status."""
    if not discord_bot:
        return {"connected": False, "message": "Bot not initialized"}
    
    return {
        "connected": not discord_bot.is_closed(),
        "user": str(discord_bot.user) if discord_bot.user else None,
        "guilds": len(discord_bot.guilds) if not discord_bot.is_closed() else 0,
        "voice_connections": len(discord_bot.voice_clients) if not discord_bot.is_closed() else 0
    }

@bot_api.post("/test/voice/{channel_id}/join")
async def test_join_voice_channel(channel_id: str):
    """Test endpoint to join a voice channel."""
    if not discord_bot or discord_bot.is_closed():
        raise HTTPException(status_code=503, detail="Discord bot not connected")
    
    try:
        channel_id_int = int(channel_id)
        success = await voice_tracker.join_voice_channel(channel_id_int)
        
        if success:
            return {"success": True, "message": f"Successfully joined voice channel {channel_id}"}
        else:
            return {"success": False, "message": f"Failed to join voice channel {channel_id}"}
            
    except Exception as e:
        logger.error(f"Error joining voice channel {channel_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to join voice channel: {str(e)}")

@bot_api.post("/test/voice/{channel_id}/leave")
async def test_leave_voice_channel(channel_id: str):
    """Test endpoint to leave a voice channel."""
    if not discord_bot or discord_bot.is_closed():
        raise HTTPException(status_code=503, detail="Discord bot not connected")
    
    try:
        channel_id_int = int(channel_id)
        await voice_tracker.leave_voice_channel(channel_id_int)
        
        return {"success": True, "message": f"Successfully left voice channel {channel_id}"}
            
    except Exception as e:
        logger.error(f"Error leaving voice channel {channel_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to leave voice channel: {str(e)}")

# Export the FastAPI app
app = bot_api

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)