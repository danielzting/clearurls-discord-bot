import os
import re
import discord
from dotenv import load_dotenv
from unalix import clear_url

class MyClient(discord.Client):
    async def on_message(self, message):
        # Sanity check for safety to prevent infinite recursion
        if message.author == client.user:
            return

        # Extract links and clean
        urls = re.findall('(?P<url>https?://[^\s]+)', message.content)
        cleaned = []
        for url in urls:
            if clear_url(url) != url:
                cleaned.append(clear_url(url))

        # Send message and add reactions
        if cleaned:
            text = 'It appears that you have sent one or more links with tracking parameters. Below are the same links with those fields removed:\n' + '\n'.join(cleaned)
            reply = await message.reply(text, mention_author=False)
            await reply.edit(suppress=True)
            await reply.add_reaction('🗑')

    async def on_reaction_add(self, reaction, user):
        # Get author of original message
        channel = client.get_channel(reaction.message.reference.channel_id)
        original = await channel.fetch_message(reaction.message.reference.message_id)
        # Delete message if original author clicked on trash reaction
        if reaction.message.author == client.user and user == original.author and reaction.emoji == '🗑':
            await reaction.message.delete()

load_dotenv()
client = MyClient()
client.run(os.environ['TOKEN'])
