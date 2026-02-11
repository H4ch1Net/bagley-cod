"""Main Discord bot file"""

import logging
import discord
from discord.ext import commands
from config.settings import DISCORD_BOT_TOKEN, COMMAND_PREFIX, LOG_FILE, LOG_LEVEL
from config.security import check_role, sanitize_input
from skills.lab_orchestrator import LabManager
from skills.challenge_manager import ChallengeManager
from skills.stats_manager import StatsManager
from skills.ai_integration import AIOrchestrator
from discord_bot.utils import rate_limiter

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents, help_command=None)

# Initialize managers
lab_manager = LabManager()
challenge_manager = ChallengeManager()
stats_manager = StatsManager()
ai_orchestrator = AIOrchestrator()

# Track unverified user warnings
warned_unverified = set()


@bot.event
async def on_ready():
    """Bot startup event"""
    logger.info(f'{bot.user} has connected to Discord!')
    logger.info(f'Connected to {len(bot.guilds)} guild(s)')

    # Set bot status
    await bot.change_presence(
        activity=discord.Game(name="!help for commands")
    )


@bot.command(name='start')
async def start_lab(ctx, *, lab_input: str):
    """Start a CTF lab

    Usage: !start <lab_type>
    Example: !start dvwa
    """
    username = ctx.author.name

    # Check role
    user_roles = [role.name for role in ctx.author.roles]
    if not check_role(user_roles):
        if ctx.author.id not in warned_unverified:
            await ctx.send(
                "👋 Hey! You need to be verified to use labs.\n"
                "Contact @officers to get the @verified-member role.\n"
                "This helps us keep the server secure!"
            )
            warned_unverified.add(ctx.author.id)

        logger.info(f"UNVERIFIED_ACCESS - User: {username} - Command: start {lab_input}")
        return

    # Check rate limit
    allowed, msg = rate_limiter.check_limit(username)
    if not allowed:
        await ctx.send(msg)
        return

    # Sanitize input
    is_valid, cleaned_input = sanitize_input(lab_input)
    if not is_valid:
        await ctx.send(f"❌ {cleaned_input}")
        logger.warning(f"BLOCKED_INPUT - User: {username} - Input: {lab_input}")
        return

    # Try direct parsing first (faster)
    lab_type = cleaned_input.lower().strip()

    # If not a direct match, try AI parsing
    if lab_type not in ['dvwa', 'webgoat', 'juice-shop', 'metasploitable']:
        result = ai_orchestrator.parse_command(cleaned_input)

        if 'error' in result:
            await ctx.send(f"❌ {result['error']}")
            return

        if result.get('action') != 'start':
            await ctx.send("❌ Unclear command. Use: `!start <lab_type>`")
            return

        lab_type = result.get('lab_type', '')

    # Create lab
    result_msg = lab_manager.create_lab(username, lab_type)

    # Record in stats
    if "started successfully" in result_msg:
        stats_manager.record_lab_start(username)

    # Send response
    await ctx.send(result_msg)

    # Send warning if present
    if msg:
        await ctx.send(msg)


@bot.command(name='stop')
async def stop_lab(ctx, lab_type: str):
    """Stop a running lab

    Usage: !stop <lab_type>
    Example: !stop dvwa
    """
    username = ctx.author.name

    # Check role
    user_roles = [role.name for role in ctx.author.roles]
    if not check_role(user_roles):
        return

    # Check rate limit
    allowed, msg = rate_limiter.check_limit(username)
    if not allowed:
        await ctx.send(msg)
        return

    result = lab_manager.stop_lab(username, lab_type.lower())
    await ctx.send(result)


@bot.command(name='delete')
async def delete_lab(ctx, lab_type: str):
    """Delete a lab (stop + remove)

    Usage: !delete <lab_type>
    Example: !delete dvwa
    """
    username = ctx.author.name

    # Check role
    user_roles = [role.name for role in ctx.author.roles]
    if not check_role(user_roles):
        return

    # Check rate limit
    allowed, msg = rate_limiter.check_limit(username)
    if not allowed:
        await ctx.send(msg)
        return

    result = lab_manager.delete_lab(username, lab_type.lower())
    await ctx.send(result)


@bot.command(name='status')
async def status(ctx):
    """Check your running labs

    Usage: !status
    """
    username = ctx.author.name

    # Check role
    user_roles = [role.name for role in ctx.author.roles]
    if not check_role(user_roles):
        return

    result = lab_manager.get_status(username)
    await ctx.send(result)


@bot.command(name='list')
async def list_labs(ctx):
    """List available lab types

    Usage: !list
    """
    result = lab_manager.list_available()
    await ctx.send(result)


@bot.command(name='categories')
async def categories(ctx):
    """List challenge categories

    Usage: !categories
    """
    cats = challenge_manager.list_categories()

    if not cats:
        await ctx.send("❌ No challenges loaded yet.")
        return

    msg = "📚 **Challenge Categories:**\n"
    msg += ", ".join(cats)
    msg += "\n\nUse `!challenges <category>` to see challenges"

    await ctx.send(msg)


@bot.command(name='challenges')
async def challenges(ctx, category: str):
    """List challenges in a category

    Usage: !challenges <category>
    Example: !challenges cryptography
    """
    result = challenge_manager.format_challenge_list(category)
    await ctx.send(result)


@bot.command(name='solve')
async def solve(ctx, challenge_id: str, *, flag: str):
    """Submit a flag for a challenge

    Usage: !solve <id> <flag>
    Example: !solve crypto-001 flag{answer}
    """
    username = ctx.author.name

    # Check role
    user_roles = [role.name for role in ctx.author.roles]
    if not check_role(user_roles):
        return

    # Check rate limit
    allowed, msg = rate_limiter.check_limit(username)
    if not allowed:
        await ctx.send(msg)
        return

    # Get challenge
    challenge = challenge_manager.get_challenge(challenge_id)

    if not challenge:
        await ctx.send(f"❌ Challenge not found: {challenge_id}")
        return

    # Check flag
    if challenge_manager.check_flag(challenge_id, flag):
        # Record solve
        points = challenge.get('points', 0)
        category = challenge.get('category', 'unknown')

        if stats_manager.record_solve(username, challenge_id, points, category):
            await ctx.send(
                f"✅ **Correct!** Flag accepted!\n"
                f"🎉 +{points} points"
            )
        else:
            await ctx.send("❌ You've already solved this challenge.")
    else:
        await ctx.send("❌ Incorrect flag. Try again!")


@bot.command(name='leaderboard')
async def leaderboard(ctx, limit: int = 10):
    """Show top players

    Usage: !leaderboard [limit]
    Example: !leaderboard 5
    """
    result = stats_manager.format_leaderboard(limit)
    await ctx.send(result)


@bot.command(name='stats')
async def stats(ctx, user: str = None):
    """Show user statistics

    Usage: !stats [username]
    Example: !stats
    Example: !stats alice
    """
    username = user or ctx.author.name
    result = stats_manager.format_user_stats(username)
    await ctx.send(result)


@bot.command(name='help')
async def help_command(ctx):
    """Show available commands

    Usage: !help
    """
    help_text = """
🤖 **Bagley Bot Commands**

**Lab Management:**
`!start <lab>` - Start a CTF lab
`!stop <lab>` - Stop a running lab
`!delete <lab>` - Delete a lab
`!status` - Check your active labs
`!list` - List available labs

**Challenges:**
`!categories` - List challenge categories
`!challenges <cat>` - List challenges in category
`!solve <id> <flag>` - Submit a flag

**Stats:**
`!leaderboard` - Top players
`!stats [user]` - User statistics

**Available Labs:**
- dvwa - Damn Vulnerable Web App
- webgoat - OWASP WebGoat
- juice-shop - OWASP Juice Shop
- metasploitable - Metasploitable 2

**Examples:**
`!start dvwa`
`!status`
`!challenges cryptography`
`!solve crypto-001 flag{answer}`
    """

    await ctx.send(help_text)


# Error handler
@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.CommandNotFound):
        # Try AI parsing for natural language
        user_input = ctx.message.content[1:]  # Remove prefix
        result = ai_orchestrator.parse_command(user_input)

        if 'error' not in result:
            # Redirect to appropriate command
            action = result.get('action')

            if action == 'start':
                await start_lab(ctx, lab_input=result.get('lab_type', ''))
            elif action == 'status':
                await status(ctx)
            elif action == 'list':
                await list_labs(ctx)
            else:
                await ctx.send("❌ Unknown command. Use `!help` for available commands.")
        else:
            await ctx.send("❌ Unknown command. Use `!help` for available commands.")

    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing argument. Use `!help` for usage.")

    else:
        logger.error(f"Command error: {error}")
        await ctx.send("❌ An error occurred. Contact admin if this persists.")


# Run bot
if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        logger.error("DISCORD_BOT_TOKEN not set in environment")
        exit(1)

    bot.run(DISCORD_BOT_TOKEN)
