import discord
import os
from discord.ext import commands
import logging
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='?', intents=intents)

@bot.event
async def on_ready():
    print(f'Successfully joined as {bot.user.name}')

@bot.event
async def on_member_join(member):
    await member.send(f"Welcome to the server, {member.name}! We're glad to have you here.")
        
       
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if "shit" in message.content.lower():
        await message.delete()
        await message.channel.send(f"{message.author.mention} Please refrain from using inappropriate language.")

    await bot.process_commands(message)

@bot.command()
async def hi(ctx):
    await ctx.send(f"HELLO {ctx.author.mention}! How are you doing?")


@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    # Default reason
    if reason is None:
        reason = "No reason provided"

    # Kick the member
    await member.kick(reason=reason)

    # Create an embed to show the kick information
    embed = discord.Embed(title=f"{member.mention} Kicked", color=discord.Color.blue())
    
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


    
bot.run(token, log_handler=handler, log_level=logging.DEBUG)



