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
    id: int
    name: str
    settings: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class User:
    """Represents a Discord user."""
    id: int
    username: str
    display_name: Optional[str] = None
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
    id: Optional[int] = None
    guild_id: int = 0
    event_date: Optional[date] = None
    event_time: Optional[datetime] = None
    event_name: str = "Sunday Mining"
    status: EventStatus = EventStatus.PLANNED
    total_participants: int = 0
    total_value_auec: Decimal = field(default_factory=lambda: Decimal('0.00'))
    payroll_processed: bool = False
    pdf_generated: bool = False
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
    id: Optional[int] = None
    event_id: int = 0
    user_id: int = 0
    channel_id: int = 0
    session_start: Optional[datetime] = None
    session_end: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    is_org_member: bool = False
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
