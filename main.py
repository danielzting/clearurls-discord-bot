import asyncio
import os
import re
import discord
from dotenv import load_dotenv
from unalix import clear_url
from prometheus_client import start_http_server, Summary, Counter, Gauge

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

process_message_time = Summary('process_message_time', 'Time spent processing message')
process_react_time = Summary('process_react_time', 'Time spent processing react')
messages = Counter('messages', 'Total number of messages processed')
cleaned_messages = Counter('cleaned_messages', 'Number of messages with tracking links cleaned')
deleted_messages = Counter('deleted_messages', 'Number of cleaned messages that were deleted with the trash react')
servers = Gauge('servers', 'Number of servers the bot is in')
members = Gauge('members', 'Combined member count of all servers the bot is in')

async def count_servers_members():
    while True:
        servers.set(len(client.guilds))
        members.set(sum([guild.member_count for guild in client.guilds]))
        await asyncio.sleep(60)

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='for tracking links'))
    asyncio.create_task(count_servers_members())

@process_message_time.time()
@client.event
async def on_message(message):
    messages.inc()
    if message.author == client.user:
        permissions = message.channel.permissions_for(message.guild.me)
        # Suppress embeds for bot messages to avoid visual clutter
        if permissions.manage_messages:
            await message.edit(suppress=True)
            # Add :wastebasket: emoji for easy deletion if necessary
            if permissions.add_reactions and permissions.read_message_history:
                await message.add_reaction('🗑')
    # Though this else is not necessary since the bot should never send
    # links with tracking parameters, include it anyways to be safe
    # against infinite recursion
    else:
        # Extract links and clean
        urls = re.findall('(?P<url>https?://[^\s]+)', message.content)
        cleaned = []
        for url in urls:
            # Ignore trailing &, /, ? in comparing, as these are not used for tracking
            if clear_url(url).strip('&/?') != url.strip('&/?'):
                cleaned.append(clear_url(url))

        # Send message and add reactions
        if cleaned:
            text = 'It appears that you have sent one or more links with tracking parameters. Below are the same links with those fields removed:\n' + '\n'.join(cleaned)
            await message.reply(text, mention_author=False)
            cleaned_messages.inc()

@process_react_time.time()
@client.event
async def on_raw_reaction_add(payload):
    # Delete messages if the original sender clicks the trash can react
    if payload.emoji.name != '🗑':
        return

    channel = await client.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    if message.reference is None or message.author != client.user:
        return

    original_channel = await client.fetch_channel(message.reference.channel_id)
    original_message = await original_channel.fetch_message(message.reference.message_id)
    user = await client.fetch_user(payload.user_id)
    permissions = message.channel.permissions_for(message.guild.me)

    if permissions.manage_messages and original_message.author == user:
        await message.delete()
        deleted_messages.inc()
    
if __name__ == '__main__':
    start_http_server(8000)
    load_dotenv()
    client.run(os.environ['TOKEN'])
