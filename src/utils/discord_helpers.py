from discord import Embed
import discord.ext.commands as commands

async def send_embed(channel, title, description, color, timestamp=None):
    embed = Embed(title=title, description=description, color=color, timestamp=timestamp)
    await channel.send(embed=embed)

def has_org_role(member):
    """Check if member has OrgMember role."""
    ORG_MEMBER_ROLE_ID = 1143413611184795658
    return any(role.id == ORG_MEMBER_ROLE_ID for role in member.roles)

def has_admin_role(member):
    """Check if member has Admin role."""
    ADMIN_ROLE_ID = 814699701861220412
    return any(role.id == ADMIN_ROLE_ID for role in member.roles)

def has_org_leaders_role(member):
    """Check if member has OrgLeaders role."""
    ORG_LEADERS_ROLE_ID = 1130629722070585396
    return any(role.id == ORG_LEADERS_ROLE_ID for role in member.roles)

def can_manage_payroll(member):
    """Check if member can manage payroll (Admin or OrgLeaders)."""
    return has_admin_role(member) or has_org_leaders_role(member)