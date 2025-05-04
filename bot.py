import discord
from discord.ext import commands
import aiohttp
import json

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

# Intents setup
intents = discord.Intents.all()
intents.members = True  # To allow member join events

bot = commands.Bot(command_prefix=".", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}!")

@bot.event
async def on_member_join(member: discord.Member):
    user_id = str(member.id)
    url = f"https://fraudshield.codepulse69.space/info?userId={user_id}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()

                    # Log channel and role mention setup
                    log_channel = bot.get_channel(int(config["log_channel_id"]))
                    role_mention = f"<@&{config['alert_role_id']}>"
                    
                    # Get the scammer and dwc roles from config
                    scammer_role = discord.utils.get(member.guild.roles, id=int(config["scammer_role_id"]))
                    dwc_role = discord.utils.get(member.guild.roles, id=int(config["dwc_role_id"]))

                    # Get user status from FraudShield API response
                    status = data.get("status", "unknown").lower()
                    message = data.get("message", "No additional information.")

                    # Create the embed
                    embed = discord.Embed(
                        title="New User Joined",
                        description=f"**User:** {member.mention}\n**User ID:** `{member.id}`",
                        color=discord.Color.green() if status == "clear" else discord.Color.red(),
                        timestamp=discord.utils.utcnow()
                    )

                    if status != "clear":
                        # If marked as scammer or DWC
                        embed.color = discord.Color.red()
                        embed.title = "🚨 Marked User Detected"
                        embed.add_field(name="Mark Status", value=f"`{status}`", inline=True)
                        embed.add_field(name="Details", value=message, inline=False)

                        # Assign the appropriate role based on the status
                        if scammer_role:
                            if can_assign_role(member, scammer_role):
                                await member.add_roles(scammer_role)
                            else:
                                print(f"[ERROR] Cannot assign 'scammer' role to {member.mention}")
                        elif dwc_role:
                            if can_assign_role(member, dwc_role):
                                await member.add_roles(dwc_role)
                            else:
                                print(f"[ERROR] Cannot assign 'dwc' role to {member.mention}")

                        await log_channel.send(content=role_mention, embed=embed)
                    else:
                        # If user is clean
                        embed.add_field(name="Mark Status", value="`clear`", inline=True)
                        embed.add_field(name="Details", value=message, inline=False)
                        await log_channel.send(embed=embed)

                    # Add user avatar to the embed
                    embed.set_thumbnail(url=member.display_avatar.url)
                    embed.set_footer(text="FraudShield API Auto Check • Member Join")
                    
    except Exception as e:
        print(f"[ERROR] Failed to check user {member.id}: {e}")

def can_assign_role(member, role):
    """
    Checks if the bot can assign the role to the member.
    1. Bot must have the "Manage Roles" permission.
    2. Bot's highest role must be above the target role in the role hierarchy.
    """
    # Check if the bot has 'Manage Roles' permission
    if not member.guild.me.guild_permissions.manage_roles:
        print("[ERROR] Bot does not have 'Manage Roles' permission.")
        return False
    
    # Check if the role is above the bot's highest role in the role hierarchy
    if role.position >= member.guild.me.top_role.position:
        print(f"[ERROR] Bot's highest role is not above {role.name} role.")
        return False
    
    return True

# Start bot using token from config
bot.run(config["token"])
