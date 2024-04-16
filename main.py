import discord
from discord.ext import commands
import os
import asyncio
import subprocess
import random
import traceback
from discord.ui import Button, View
import time
import sys
import datetime
import aiohttp
import pytz
import pymongo

bot = commands.Bot(command_prefix='.', intents=discord.Intents.all())

main_color = 0xE60000

# List of possible response messages
attack_responses = [
    "Ow! That hurt!",
    "You'll pay for that!",
    "Stop attacking me!",
    "I'm not afraid of you!",
    "You missed!",
    "Is that all you've got?",
    "I'll get you next time!",
    "That was weak!",
    "You call that an attack?",
    "Ha! That tickles!",
    "I'll remember this!",
    "You can't defeat me!",
    "Bring it on!",
    "You'll regret that!",
    "Try again!",
    "I've felt worse!",
    "You'll have to try harder than that!",
    "Nice try, but nope!",
    "Not even close!",
    "Pathetic!",
    "That really hurt!",
    "That was uncalled for!",
    "You are hurting me man!"
]

# Connect to MongoDB
mongo_client = pymongo.MongoClient(os.environ("db"))
db = mongo_client["Bot2-Data"]
collection = db["data"]

def restart_bot():
  os.execv(sys.executable, ['python'] + sys.argv)

@bot.event
async def on_ready():
    channel = bot.get_channel(1223964914960302141)
    await channel.send("👿 **ArolPlay Events** is now functioning! 👿")
    await bot.change_presence(activity=discord.Game(name="Roblox"), status=discord.Status.idle)
    print("The bot is now online.")

GITHUB_REPO_URL = 'https://github.com/imdakiki/ArolPlay-Events.git'

GIT_PULL_COMMAND = ['git', 'pull']

@bot.event
async def on_message(message):
    if message.channel.id == os.environ("gitchannel"):
        # Check if the message content indicates a new commit or merged PR
        if 'Commit' in message.content.lower() or 'Merged' in message.content.lower():
            # Execute git pull command
            await update_repository(message)

async def update_repository(message):
    try:
        # Execute git pull command
        result = subprocess.run(GIT_PULL_COMMAND, capture_output=True, text=True)
        if result.returncode == 0:
            await message.channel.send('Code pulled successfully!')
            restart_bot()
        else:
            await message.channel.send('Error pulling repo!')
            await message.channel.send(f'Error: {result.stderr}')
    except Exception as e:
        await message.channel.send(f'An error occurred: {str(e)}')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        ETA = int(time.time() + round(error.retry_after))
        embed = discord.Embed(description=f"🛑 This command is on cooldown, you can use it again <t:{ETA}:R>.", color=main_color)
        await ctx.send(ctx.message.author.mention, embed=embed)
        
@bot.command()
@commands.has_role("bot perms")
async def eval(ctx, *, code: str):
    """
    Evaluate and execute Python code.
    """
    try:
        # Execute the code
        exec(code)

        await ctx.send("Code executed successfully.")

    except Exception as e:
        # If an exception occurred, send the traceback
        await ctx.send(f'```py\n{traceback.format_exc()}\n```')

@bot.command()
async def uktime(ctx):
    try:
        # Set the timezone to UK
        uk_timezone = pytz.timezone('Europe/London')

        # Get the current time
        current_time = datetime.datetime.now(uk_timezone)

        # Format the time as a string
        time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")

        # Send the time as a message
        await ctx.send(f"The current time in the UK is: {time_str}")
    except Exception as e:
        await ctx.send(f'An error occurred: {e}')

@bot.command()
@commands.has_permissions(administrator=True)
async def load(ctx, boss_health: int):
    try:
        # Define role IDs for each group of roles to remove
        role_ids_to_remove_group1 = [1226156025606963341]  # Example role IDs for group 1
        role_ids_to_remove_group2 = [1229443766167928902]  # Example role IDs for group 2

        # Remove roles from all users for group 1
        for member in ctx.guild.members:
            roles_to_remove_group1 = [role for role in member.roles if role.id in role_ids_to_remove_group1]
            if roles_to_remove_group1:
                await member.remove_roles(*roles_to_remove_group1)
                print(f"Roles removed from {member} for group 1")

        # Remove roles from all users for group 2
        for member in ctx.guild.members:
            roles_to_remove_group2 = [role for role in member.roles if role.id in role_ids_to_remove_group2]
            if roles_to_remove_group2:
                await member.remove_roles(*roles_to_remove_group2)
                print(f"Roles removed from {member} for group 2")

        # Set event parameters in MongoDB
        collection.insert_one({
            "event_ended": False,
            "boss_health": boss_health,
            "rage_mode": False
        })

        await ctx.send("Event loaded successfully!\n> The last winner and all the Attendees have been reset!")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@bot.command()
async def ping(ctx):
    try:
        # Send the initial loading message
        loading_embed = discord.Embed(title="🔄 Loading...", color=discord.Color.blue())
        loading_message = await ctx.send(embed=loading_embed)

        # Start the timer for Discord API ping
        start_discord = time.monotonic()
        end_discord = time.monotonic()
        await asyncio.sleep(0.5)

        # Start the timer for MongoDB ping
        start_db = time.monotonic()
        await ctx.message.channel.typing()  # Simulate a database query
        _ = collection.find_one({})  # Access MongoDB
        end_db = time.monotonic()

        # Calculate the ping times
        discord_ping = (end_discord - start_discord) * 1000
        db_ping = (end_db - start_db) * 1000

        # Send the ping results
        result_embed = discord.Embed(title="🏓 Ping Results", color=discord.Color.blue())
        result_embed.add_field(name="🤖Bot Ping", value=f"{discord_ping:.2f}ms", inline=False)
        result_embed.add_field(name="🔑Database Ping", value=f"{db_ping:.2f}ms", inline=False)
        await loading_message.edit(embed=result_embed)
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@bot.command()
@commands.is_owner()
async def stabilize(ctx, attempts: int = 5):
    try:
        # Send requests to Discord API and MongoDB
        discord_pings = []
        db_pings = []
        async with ctx.typing():
            for _ in range(attempts):
                # Measure ping to Discord API
                start_discord = time.monotonic()
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://discord.com/api/v9/gateway") as response:
                        _ = await response.text()
                end_discord = time.monotonic()
                discord_pings.append((end_discord - start_discord) * 1000)

                # Measure ping to MongoDB
                start_db = time.monotonic()
                # Instead of accessing a specific key in the database, we'll just access the entire collection
                _ = collection.find_one({})
                end_db = time.monotonic()
                db_pings.append((end_db - start_db) * 1000)

                await asyncio.sleep(1)  # Delay between requests to simulate network activity

        # Calculate average and standard deviation of ping results for Discord API
        avg_discord_ping = sum(discord_pings) / len(discord_pings)
        std_dev_discord = (sum((ping - avg_discord_ping) ** 2 for ping in discord_pings) / len(discord_pings)) ** 0.5

        # Calculate average and standard deviation of ping results for MongoDB
        avg_db_ping = sum(db_pings) / len(db_pings)
        std_dev_db = (sum((ping - avg_db_ping) ** 2 for ping in db_pings) / len(db_pings)) ** 0.5

        # Analyze ping results
        if std_dev_discord < 10 and std_dev_db < 10:
            await ctx.send(f"The pings are already stable. Discord Ping: {avg_discord_ping:.2f}ms, MongoDB Ping: {avg_db_ping:.2f}ms")
        else:
            await ctx.send(f"Ping stabilization in progress. Discord Ping: {avg_discord_ping:.2f}ms (±{std_dev_discord:.2f}ms), MongoDB Ping: {avg_db_ping:.2f}ms (±{std_dev_db:.2f}ms)")

    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

# Define a global cooldown decorator
attack_cooldown = commands.CooldownMapping.from_cooldown(1, 10, commands.BucketType.user)

@bot.command()
async def attack(ctx):
    # Check if the event has ended
    if collection.find_one({"event_ended": True}):
        await ctx.reply("🛑 Sorry, the event has ended!")
        return

    # Check if the command is on cooldown
    retry_after = attack_cooldown.update_rate_limit(ctx)
    if retry_after:
        ETA = int(time.time() + round(retry_after))
        embed = discord.Embed(description=f"🛑 This command is on cooldown, you can use it again <t:{ETA}:R>.", color=main_color)
        await ctx.send(ctx.message.author.mention, embed=embed)
        return

    # Check if rage mode is activated (1-100 percent chance)
    if random.randint(1, 100) <= 5:  # Change 5 to the desired percentage chance (e.g., 5 for 5% chance)
        # Set rage mode to True in MongoDB
        collection.update_one({}, {"$set": {"rage_mode": True}})
        await ctx.send("👿 **RAGE MODE IS NOW ACTIVATED!** 👿\n> <@&1226156025606963341>")
        await asyncio.sleep(20)

        # Set rage mode back to False after the cooldown
        collection.update_one({}, {"$set": {"rage_mode": False}})
        await ctx.send("👿 **RAGE MODE IS NOW DEACTIVATED!** 👿\n> <@&1226156025606963341>")

    # Add role to the user
    role = discord.utils.get(ctx.guild.roles, id=int())
    await ctx.author.add_roles(role)

    # Check if rage mode is activated
    rage_mode = collection.find_one({}, {"rage_mode": 1})
    if rage_mode.get("rage_mode", False):
        await ctx.reply("👿 **RAGE MODE IS CURRENTLY ACTIVATED** 👿")
    else:
        # Subtract 50 from boss_health
        boss_health = collection.find_one({}, {"boss_health": 1})["boss_health"]
        collection.update_one({}, {"$set": {"boss_health": boss_health - 50}})

        # Select a random response from the list and send it
        await ctx.reply(random.choice(attack_responses) + "\n-50 Health")

    # Check if boss_health is <= 0
    if collection.find_one({}, {"boss_health": 1})["boss_health"] <= 0:
        collection.update_one({}, {"$set": {"event_ended": True}})
        embed = discord.Embed(title="🎉 ArolPlay Events Defeated! 🎉", description=f"The boss was defeated by {ctx.author.mention}! And thank you to everyone who Competed", color=discord.Color.yellow())
        await ctx.message.channel.typing()
        await asyncio.sleep(3)
        wrole = discord.utils.get(ctx.guild.roles, id=int(1229443766167928902))
        await ctx.author.add_roles(wrole)
        await ctx.send(role.mention, embed=embed)

@bot.command(aliases=["hp"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def health(ctx):
    try:
        boss_health = collection.find_one({}, {"boss_health": 1})["boss_health"]
        if boss_health > 0:
            embed = discord.Embed(title="❤ ArolPlay Events Health ❤", description=f"Supervisor has {boss_health} Health left until defeated", color=main_color)
            await ctx.send(f"{ctx.author.mention}", embed=embed)
        else:
            embed = discord.Embed(title="❤ ArolPlay Events Health ❤", description="Supervisor has been defeated!", color=main_color)
            await ctx.send(f"{ctx.author.mention}", embed=embed)
    except KeyError:
        await ctx.reply("🛑 ArolPlay Events health data not found.")

@bot.command()
async def test(ctx):
    await ctx.reply("test")

bot.run(os.environ("token"))
