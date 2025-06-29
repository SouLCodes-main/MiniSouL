import discord
import os
from discord.ext import commands
import logging
from dotenv import load_dotenv
from datetime import timedelta
from typing import Optional

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

# Check if token exists
if not token:
    print("Error: DISCORD_TOKEN not found in environment variables!")
    exit(1)

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='ms!', intents=intents)

@bot.event
async def on_ready():
    print(f'Successfully joined as {bot.user.name if bot.user else "Unknown"}')

@bot.event
async def on_member_join(member):
    await member.send(f"Welcome to the server, {member.name}! We're glad to have you here.")
        
# Bad language detection     
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    bad_words = ["fuck", "ass", "dick", "slut"]
    content_lower = message.content.lower()

    for word in bad_words:
        if word in content_lower:
            print(f"Bad word '{word}' detected in message from {message.author.name}")
            
            try:
                # Check if bot has permission to timeout members
                if not message.guild.me.guild_permissions.moderate_members:
                    print("Bot doesn't have moderate_members permission")
                    await message.channel.send("❌ I don't have permission to timeout members.")
                    return

                # Check if the user can be timed out (not an admin/owner)
                if message.author.guild_permissions.administrator or message.author == message.guild.owner:
                    print(f"User {message.author.name} is admin/owner, cannot timeout")
                    await message.channel.send("❌ Cannot timeout administrators or server owners.")
                    return

                print(f"Attempting to timeout {message.author.name}")
                
                # Delete the message first
                await message.delete()
                print("Message deleted successfully")

                # Apply timeout for 15 minutes (900 seconds)
                timeout_duration = timedelta(minutes=15)
                await message.author.timeout(timeout_duration, reason="Inappropriate language")
                print(f"Timeout applied successfully to {message.author.name}")

                # Create and send embed
                embed = discord.Embed(title="🚫 Inappropriate Language Detected", color=discord.Color.red())
                embed.add_field(name="User", value=f"{message.author.mention} has been timed out for 15 minutes.", inline=False)
                embed.add_field(name="Reason", value="Inappropriate language", inline=False)
                embed.add_field(name="Action", value="Message deleted and user timed out", inline=False)
                embed.set_footer(text="Moderation action executed successfully.")
                
                await message.channel.send(embed=embed)
                print("Embed sent successfully")

            except discord.Forbidden as e:
                print(f"Forbidden error: {e}")
                await message.channel.send("❌ I don't have permission to timeout this user.")
            except discord.HTTPException as e:
                print(f"HTTP error: {e}")
                await message.channel.send(f"❌ Failed to timeout the user: {str(e)}")
            except Exception as e:
                print(f"Unexpected error: {e}")
                await message.channel.send(f"❌ An error occurred: {str(e)}")

            break

    await bot.process_commands(message)
   

@bot.command()
async def hi(ctx):
    await ctx.send(f"Hello! {ctx.author.mention}! How are you doing?")


@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    # Default reason
    if reason is None:
        reason = "No reason provided"

    # Create an embed to show the kick information
    embed = discord.Embed(title=f"{member.mention} Kicked", color=discord.Color.blue())

    # Kick the member
    await member.kick(reason=reason)
    
    embed.add_field(name="By", value=f"{ctx.author.mention}", inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.set_footer(text="Kick executed successfully.")

    await ctx.send(embed=embed)

@kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to kick members.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Please mention a user to kick. Example: `?kick @user reason`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Couldn't find that user.")
    else:
        await ctx.send("⚠️ An error occurred while trying to kick the user.")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    if reason is None:
        reason = "No reason provided"

    embed = discord.Embed(title="Member Banned ☠️", color=discord.Color.blue())

    embed.add_field(name="User", value=f"{member.mention}", inline=False)
    embed.add_field(name="By", value=f"{ctx.author.mention}", inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.set_footer(text="Ban executed successfully.")

    await ctx.send(embed=embed)

    await member.ban(reason=reason)


@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to ban members.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Please mention a user to ban. Example: `?ban @user reason`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Couldn't find that user.")

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member):
    await ctx.guild.unban(discord.Object(id=member))
    await ctx.send(f"Unbanned {member}.")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member, duration: str, *, reason=None):
    """Timeout a member for the specified duration
    Format: ms!timeout @user <duration> <reason>
    Duration examples: 15m, 2h, 1d, 30 (defaults to minutes)
    """
    if reason is None:
        reason = "No reason provided"
    
    try:
        # Parse duration
        duration_lower = duration.lower().strip()
        timeout_minutes = 15  # default
        
        if duration_lower.endswith('m'):
            # Minutes
            timeout_minutes = int(duration_lower[:-1])
        elif duration_lower.endswith('h'):
            # Hours
            timeout_minutes = int(duration_lower[:-1]) * 60
        elif duration_lower.endswith('d'):
            # Days
            timeout_minutes = int(duration_lower[:-1]) * 1440  # 24 * 60
        else:
            # Default to minutes if no unit specified
            try:
                timeout_minutes = int(duration_lower)
            except ValueError:
                await ctx.send("❌ Invalid duration format. Use: `15m`, `2h`, `1d`, or `30` (minutes)")
                return
        
        # Validate duration limits
        if timeout_minutes < 1:
            await ctx.send("❌ Duration must be at least 1 minute.")
            return
        elif timeout_minutes > 40320:  # 28 days in minutes
            await ctx.send("❌ Duration cannot exceed 28 days.")
            return
        
        # Check if the user can be timed out
        if member.guild_permissions.administrator or member == ctx.guild.owner:
            await ctx.send("❌ Cannot timeout administrators or server owners.")
            return
        
        # Apply timeout
        timeout_duration = timedelta(minutes=timeout_minutes)
        await member.timeout(timeout_duration, reason=reason)
        
        # Format duration for display
        if timeout_minutes < 60:
            duration_display = f"{timeout_minutes} minute{'s' if timeout_minutes != 1 else ''}"
        elif timeout_minutes < 1440:
            hours = timeout_minutes // 60
            minutes = timeout_minutes % 60
            duration_display = f"{hours} hour{'s' if hours != 1 else ''}"
            if minutes > 0:
                duration_display += f" {minutes} minute{'s' if minutes != 1 else ''}"
        else:
            days = timeout_minutes // 1440
            hours = (timeout_minutes % 1440) // 60
            duration_display = f"{days} day{'s' if days != 1 else ''}"
            if hours > 0:
                duration_display += f" {hours} hour{'s' if hours != 1 else ''}"
        
        # Create embed
        embed = discord.Embed(title="⏰ User Timed Out", color=discord.Color.orange())
        embed.add_field(name="User", value=f"{member.mention}", inline=False)
        embed.add_field(name="Duration", value=duration_display, inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="By", value=f"{ctx.author.mention}", inline=False)
        embed.set_footer(text="Timeout executed successfully.")
        
        await ctx.send(embed=embed)
        
    except ValueError:
        await ctx.send("❌ Invalid duration format. Use: `15m`, `2h`, `1d`, or `30` (minutes)")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to timeout this user.")
    except discord.HTTPException as e:
        await ctx.send(f"❌ Failed to timeout the user: {str(e)}")
    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")

@timeout.error
async def timeout_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to timeout members.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Please mention a user and specify duration. Example: `ms!timeout @user 15m reason`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Couldn't find that user.")
    else:
        await ctx.send("❌ An error occurred while trying to timeout the user.")

@bot.command()
async def avatar(ctx, member: Optional[discord.Member] = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"{member.name}'s Avatar", color=discord.Color.blue())
    embed.set_image(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def removetimeout(ctx, member: Optional[discord.Member] = None):
    member = member or ctx.author
    await member.timeout(None)
    embed = discord.Embed(title="✅ Timeout Removed", color=discord.Color.green())
    embed.add_field(name="User", value=f"{member.mention} timeout has been removed.", inline=False)
    embed.add_field(name="By", value=f"{ctx.author.mention}", inline=False)
    embed.set_footer(text="Timeout removed successfully.")

    await ctx.send(embed=embed)

@bot.command()
async def serverinfo(ctx):
    """Display information about the server"""
    guild = ctx.guild
    
    # Get member counts
    total_members = guild.member_count
    bot_count = len([member for member in guild.members if member.bot])
    human_count = total_members - bot_count
    
    # Get channel counts
    text_channels = len(guild.text_channels)
    voice_channels = len(guild.voice_channels)
    categories = len(guild.categories)
    
    # Get role count
    role_count = len(guild.roles)
    
    # Get boost info
    boost_level = guild.premium_tier
    boost_count = guild.premium_subscription_count
    
    # Create embed
    embed = discord.Embed(title=f"📊 {guild.name} Server Information", color=discord.Color.blue())
    
    # Server basic info
    embed.add_field(name="🆔 Server ID", value=guild.id, inline=True)
    embed.add_field(name="👑 Owner", value=guild.owner.mention, inline=True)
    embed.add_field(name="📅 Created", value=guild.created_at.strftime("%B %d, %Y"), inline=True)
    
    # Member info
    embed.add_field(name="👥 Total Members", value=f"{total_members:,}", inline=True)
    embed.add_field(name="👤 Humans", value=f"{human_count:,}", inline=True)
    embed.add_field(name="🤖 Bots", value=f"{bot_count:,}", inline=True)
    
    # Channel info
    embed.add_field(name="💬 Text Channels", value=text_channels, inline=True)
    embed.add_field(name="🔊 Voice Channels", value=voice_channels, inline=True)
    embed.add_field(name="📁 Categories", value=categories, inline=True)
    
    # Other info
    embed.add_field(name="🎭 Roles", value=role_count, inline=True)
    embed.add_field(name="🚀 Boost Level", value=f"Level {boost_level}", inline=True)
    embed.add_field(name="⭐ Boosts", value=boost_count, inline=True)
    
    # Server features
    if guild.features:
        features = [feature.replace('_', ' ').title() for feature in guild.features]
        embed.add_field(name="✨ Features", value=", ".join(features[:5]), inline=False)
    
    # Server description
    if guild.description:
        embed.add_field(name="📝 Description", value=guild.description[:1024], inline=False)
    
    # Set thumbnail
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    embed.set_footer(text=f"Requested by {ctx.author.name}")
    
    await ctx.send(embed=embed)

@bot.command()
async def botperms(ctx):
    """Test command to check bot permissions and functionality"""
    embed = discord.Embed(title="🤖 Bot Status Check", color=discord.Color.blue())
    
    # Check bot permissions
    bot_member = ctx.guild.me
    permissions = bot_member.guild_permissions
    
    embed.add_field(name="Bot Name", value=bot_member.name, inline=True)
    embed.add_field(name="Bot ID", value=bot_member.id, inline=True)
    embed.add_field(name="", value="", inline=True)  # Empty line
    
    # Permission checks
    embed.add_field(name="Moderate Members", value="✅" if permissions.moderate_members else "❌", inline=True)
    embed.add_field(name="Manage Messages", value="✅" if permissions.manage_messages else "❌", inline=True)
    embed.add_field(name="Send Messages", value="✅" if permissions.send_messages else "❌", inline=True)
    
    embed.add_field(name="Kick Members", value="✅" if permissions.kick_members else "❌", inline=True)
    embed.add_field(name="Ban Members", value="✅" if permissions.ban_members else "❌", inline=True)
    embed.add_field(name="Embed Links", value="✅" if permissions.embed_links else "❌", inline=True)
    
    embed.set_footer(text="Use ?test to check bot status")
    
    await ctx.send(embed=embed)



bot.run(token, log_handler=handler, log_level=logging.DEBUG)



