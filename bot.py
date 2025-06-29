import discord
import os
from discord.ext import commands
import logging
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

# Check if token exists
if not token:
    print("Error: DISCORD_TOKEN not found in environment variables!")
    exit(1)

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='?', intents=intents)

@bot.event
async def on_ready():
    print(f'Successfully joined as {bot.user.name if bot.user else "Unknown"}')

@bot.event
async def on_member_join(member):
    await member.send(f"Welcome to the server, {member.name}! We're glad to have you here.")
        
       
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
async def timeout(ctx, member: discord.Member, duration: int = 15, *, reason=None):
    """Timeout a member for the specified duration in minutes"""
    if reason is None:
        reason = "No reason provided"
    
    try:
        # Check if the user can be timed out
        if member.guild_permissions.administrator or member == ctx.guild.owner:
            await ctx.send("❌ Cannot timeout administrators or server owners.")
            return
        
        # Apply timeout
        timeout_duration = timedelta(minutes=duration)
        await member.timeout(timeout_duration, reason=reason)
        
        # Create embed
        embed = discord.Embed(title="⏰ User Timed Out", color=discord.Color.orange())
        embed.add_field(name="User", value=f"{member.mention}", inline=False)
        embed.add_field(name="Duration", value=f"{duration} minutes", inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="By", value=f"{ctx.author.mention}", inline=False)
        embed.set_footer(text="Timeout executed successfully.")
        
        await ctx.send(embed=embed)
        
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
        await ctx.send("❌ Please mention a user to timeout. Example: `?timeout @user 15 reason`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Couldn't find that user or invalid duration.")

@bot.command()
async def test(ctx):
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

@bot.command()
async def testbadword(ctx):
    """Test the bad word detection (will trigger timeout)"""
    await ctx.send("Testing bad word detection...")
    # This will trigger the on_message event
    await ctx.send("fuck")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)



