"""
Database Models

Data models and validation for the Red Legion Bot database entities.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, Any, List
from enum import Enum

class EventStatus(Enum):
    """Mining event status enumeration."""
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class LoanStatus(Enum):
    """Loan status enumeration."""
    ACTIVE = "active"
    PAID = "paid"
    DEFAULTED = "defaulted"

class MaterialCategory(Enum):
    """Material category enumeration."""
    ORE = "ore"
    REFINED = "refined"
    COMPONENT = "component"
    COMMODITY = "commodity"

@dataclass
class Guild:
    """Represents a Discord guild/server."""
    guild_id: str
    name: str
    owner_id: Optional[str] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class User:
    """Represents a Discord user."""
    user_id: str
    username: str
    display_name: Optional[str] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class GuildMembership:
    """Represents a user's membership in a guild."""
    guild_id: int
    user_id: int
    is_org_member: bool = False
    join_date: Optional[datetime] = None

@dataclass
class MiningEvent:
    """Represents a mining event."""
    event_id: int
    guild_id: str
    name: str
    event_date: date
    location: str
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class MiningChannel:
    """Represents an approved mining voice channel."""
    id: Optional[int] = None
    guild_id: int = 0
    channel_id: int = 0
    channel_name: str = ""
    is_active: bool = True
    created_at: Optional[datetime] = None

@dataclass
class MiningParticipation:
    """Represents a user's participation in a mining event."""
    participation_id: int
    event_id: int
    user_id: str
    channel_id: str
    join_time: datetime
    leave_time: Optional[datetime] = None
    duration_minutes: int = 0
    is_valid: bool = True
    created_at: Optional[datetime] = None

@dataclass
class Material:
    """Represents a mining material."""
    id: Optional[int] = None
    name: str = ""
    category: MaterialCategory = MaterialCategory.ORE
    base_value_auec: Decimal = field(default_factory=lambda: Decimal('0.00'))
    current_market_value: Optional[Decimal] = None
    updated_at: Optional[datetime] = None

@dataclass
class MiningYield:
    """Represents material yield from a mining session."""
    id: Optional[int] = None
    participation_id: int = 0
    material_id: int = 0
    quantity_scu: Decimal = field(default_factory=lambda: Decimal('0.00'))
    estimated_value: Optional[Decimal] = None
    recorded_at: Optional[datetime] = None

@dataclass
class Loan:
    """Represents a loan in the organization."""
    id: Optional[int] = None
    guild_id: int = 0
    borrower_id: int = 0
    amount_auec: Decimal = field(default_factory=lambda: Decimal('0.00'))
    interest_rate: Decimal = field(default_factory=lambda: Decimal('0.0000'))
    status: LoanStatus = LoanStatus.ACTIVE
    issued_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    paid_date: Optional[datetime] = None

# Model registry for dynamic operations
MODEL_REGISTRY = {
    'guilds': Guild,
    'users': User,
    'guild_memberships': GuildMembership,
    'mining_events': MiningEvent,
    'mining_channels': MiningChannel,
    'mining_participation': MiningParticipation,
    'materials': Material,
    'mining_yields': MiningYield,
    'loans': Loan,
}
