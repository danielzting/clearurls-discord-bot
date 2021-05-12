import os
import re
import discord
from dotenv import load_dotenv
from unalix import clear_url

class MyClient(discord.Client):
    async def on_message(self, message):
        urls = re.findall("(?P<url>https?://[^\s]+)", message.content)
        cleaned = []
        for url in urls:
            if clear_url(url) != url:
                cleaned.append(clear_url(url))
        if cleaned:
            await message.reply("It appears that you have sent one or more links with tracking parameters. Below are the same links with those fields removed:\n" + "\n".join(cleaned))

load_dotenv()
client = MyClient()
client.run(os.environ['TOKEN'])
