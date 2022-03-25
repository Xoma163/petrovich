import asyncio

import discord
from discord.ext import commands

from petrovich.settings import env


class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        super(DiscordBot, self).__init__(command_prefix='/', intents=intents)

    async def on_connect(self):
        print("start ds bot")

    async def on_message(self, message):
        if message.author == self.user:
            return
        print('ку я заебись 3')
        ctx = await self.get_context(message)
        await ctx.send(message.content)
        # await ctx.send(file=discord.File(_bytes, "E.png"))

    def run(self, *args, **kwargs):
        token = env.str("DISCORD_TOKEN")
        asyncio.get_event_loop().run_until_complete(super().run(token))
