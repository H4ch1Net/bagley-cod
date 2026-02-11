"""Discord command helpers and formatters

Re-exports bot commands for external use. The main command definitions
live in discord_bot.bot to keep the bot instance and decorators together.
"""

# Commands are defined directly in bot.py using @bot.command decorators.
# This module provides shared helper utilities for command implementations.

import discord
from typing import Optional


def create_embed(title: str, description: str, color: int = 0x00ff00) -> discord.Embed:
    """Create a standard embed for bot responses"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    return embed


def format_lab_info(lab_type: str, ip: str, port: int, uptime: str) -> str:
    """Format lab information for display"""
    return (
        f"**{lab_type.upper()}**\n"
        f"📍 IP: `{ip}:{port}`\n"
        f"⏱️ Uptime: {uptime}"
    )


def truncate_message(message: str, max_length: int = 2000) -> str:
    """Truncate message to Discord's character limit"""
    if len(message) <= max_length:
        return message
    return message[:max_length - 3] + "..."


def get_member_display_name(member: discord.Member) -> str:
    """Get the best display name for a member"""
    return member.display_name or member.name
