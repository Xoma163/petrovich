import discord
from discord.ext import commands


class DiscordClient(discord.Client):

    def __init__(self):
        super(DiscordClient, self).__init__()

        intents = discord.Intents.default()
        intents.members = True
        self.intents = intents
        self.bot = commands.Bot(command_prefix=commands.when_mentioned_or('XD '), intents=intents)

    async def on_ready(self):
        for guild in self.guilds:
            members = '\n - '.join([member.name for member in guild.members])
            print(f'Guild Members:\n - {members}')

    async def on_message(self, message):
        if message.author == self.user:
            return

        await message.channel.send("asd")
