import asyncio
import logging
import os
import re
from contextlib import closing

import discord
from discord.ext import commands
from dotenv import load_dotenv
from prometheus_client import Counter, Gauge, start_http_server, Summary
from unalix import clear_url

from database.guildsettings import (
    ensure_settings_table,
    get_automod_setting,
    set_automod_setting,
)
from database.util import get_dbcon

TRASH_EMOJI = '🗑️'

class ClearUrlsBot(commands.Bot):
    async def setup_hook(self):
        with closing(get_dbcon()) as con:
            ensure_settings_table(con)

        synced = await self.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
        
        self.loop.create_task(count_servers_members())

intents = discord.Intents.default()
intents.message_content = True
bot = ClearUrlsBot(command_prefix="/", intents=intents, activity=discord.Activity(type=discord.ActivityType.watching, name='for tracking links'));

logger = logging.getLogger(__name__)

process_message_time = Summary('process_message_time', 'Time spent processing message')
process_react_time = Summary('process_react_time', 'Time spent processing react')
messages = Counter('messages', 'Total number of messages processed')
cleaned_messages = Counter('cleaned_messages', 'Number of messages with tracking links cleaned')
deleted_messages = Counter('deleted_messages', 'Number of cleaned messages that were deleted with the trash react')
servers = Gauge('servers', 'Number of servers the bot is in')
members = Gauge('members', 'Combined member count of all servers the bot is in')

async def count_servers_members():
    while True:
        servers.set(len(bot.guilds))
        members.set(sum([guild.member_count for guild in bot.guilds]))
        await asyncio.sleep(60)

@process_message_time.time()
@bot.event
async def on_message(message: discord.Message):
    if message.flags.ephemeral:
        return
    messages.inc()
    permissions = message.channel.permissions_for(message.guild.me)
    can_add_reactions = (permissions.add_reactions 
                         and permissions.read_message_history 
                         and permissions.manage_messages)
    if message.author == bot.user:
        # Suppress embeds for bot messages if unable to suppress embeds for original message to avoid visual clutter
        if not permissions.manage_messages:
            await message.edit(suppress=True)
        # Add :wastebasket: emoji for easy deletion if necessary, but not for responses to slash commands (check for interaction metadata)
        message_is_command_response = message.interaction_metadata is not None
        if can_add_reactions and not message_is_command_response:
            await message.add_reaction(TRASH_EMOJI)
    # Though this else is not necessary since the bot should never send
    # links with tracking parameters, include it anyways to be safe
    # against infinite recursion
    else:
        # Extract links and clean
        urls = re.findall('(?P<url>https?://[^\s]+)', message.content)
        cleaned = []
        for url in urls:
            # Ignore trailing & in comparing, as these are not used for tracking
            # This is to fix a bug where right clicking on an image in the Discord *app* (not browser) > Copy Link on context menu would create a link ending in &
            # Pasting this link into Discord would then trigger the bot since the cleaned link removed the &, even though the image link didn't have tracking parameters
            if clear_url(url).strip('&') != url.strip('&'):
                cleaned.append(clear_url(url))

        if not cleaned:
            return
        
        with closing(get_dbcon()) as con:
            should_replace_message = get_automod_setting(con, message.guild.id)
        # there are two paths we can take in response
        # if the automod setting is disabled we simply add a new message with the links removed
        whats_this = f"([what's this?](<https://danielzting.github.io/clearurls-discord-bot#whats-this>))"
        if not should_replace_message:
            # Suppress embeds for original message to avoid visual clutter
            if permissions.manage_messages:
                await message.edit(suppress=True)
            # Send message and add reactions
            text = f"It appears that {message.author.mention} sent one or more links with tracking parameters. Below are the same links with with tracking parameters removed {whats_this}:\n\n{"\n".join(cleaned)}"
            await message.reply(text, silent=True)
        else:
            # if the automod setting is enabled we delete the offending message and repost the cleaned one
            cleaned_content = message.content
            for url in urls:
                cleaned_content = cleaned_content.replace(url, clear_url(url))
            text = f"It appears {message.author.mention} sent one or more links with tracking parameters, so I deleted the message. Here's the original message content with tracking parameters removed {whats_this}:\n\n{cleaned_content}"
            await message.reply(text, silent=True)
            await message.delete()
            deleted_messages.inc()

        cleaned_messages.inc()

@process_react_time.time()
@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    reaction_is_relevant =  payload.emoji.name == TRASH_EMOJI and payload.user_id != bot.user.id
    if not reaction_is_relevant:
        return

    channel = await bot.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    reacted_message_is_from_bot = message.author == bot.user
    if not reacted_message_is_from_bot:
        return
    
    permissions = message.channel.permissions_for(message.guild.me)
    if not permissions.manage_messages:
        return
    
    # we need to perform an "auth check" to make sure the user reacting to the bot message
    # is the same user that originally posted it. we only want to let the original author
    # delete their own messages. first we try to get their user ID via props on the message 
    # we also know that bot messages always mention the relevant user, so if that behavior
    # stays consistent we can just rely on the first mention 

    reacting_user = await bot.fetch_user(payload.user_id)
    authorized_user = None
    
    is_reply = message.reference is not None
    if is_reply:
        try:
            original_channel = await bot.fetch_channel(message.reference.channel_id)
            original_message = await original_channel.fetch_message(message.reference.message_id)
            authorized_user = original_message.author
        except (discord.NotFound, discord.Forbidden):
            pass
    if authorized_user is None and len(message.mentions) > 0:
        # as a fallback, get the original author from the mentions
        authorized_user = message.mentions[0]
    
    should_delete = authorized_user and reacting_user.id == authorized_user.id
    if should_delete:
        try:
            await message.delete()
            deleted_messages.inc()
            logger.info(f"Deleted message {message.id} via reaction by user {payload.user_id}")
        except discord.Forbidden:
            logger.exception(f"Missing permissions to delete message {message.id} in channel {channel.name}")
        except discord.HTTPException:
            logger.exception(f"Failed to delete message {message.id}")

@bot.tree.command(name="linkautomod", description="Enable or disable automatic delete/repost of messages with dirty links removed")
@commands.has_permissions(administrator=True)
@commands.guild_only()
async def set_automod_behavior(interaction: discord.Interaction, enabled: bool):
    """Enable or disable link automoderation for this server"""  
      
    try:
        with closing(get_dbcon()) as con:
            set_automod_setting(con, interaction.guild.id, enabled)
        status = "enabled" if enabled else "disabled"
        await interaction.response.send_message(f"✅ Link automod has been **{status}** for this server.")
        logger.info(f"set replace messages setting to {status} for {interaction.guild.id}")
        
    except Exception:
        await interaction.response.send_message(f"❌ An error occurred at the bot server. \n\n You can open a bug report [here](https://github.com/danielzting/clearurls-discord-bot/issues) 🪳", ephemeral=True)
        logger.exception("Error in linkautomod command")

if __name__ == '__main__':
    start_http_server(8000)
    load_dotenv()
    bot.run(os.environ['TOKEN'])
