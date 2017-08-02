import discord
from discord.ext import commands
from .utils.dataIO import dataIO
from .utils.dataIO import fileIO
from .utils import checks
import time
import os
import csv
import requests
import re

class ClanMod:

    def __init__(self, bot):
        self.bot = bot
        self.data_dir = 'data/clanmod/users/{}/'
        self.champs_file = self.data_dir + 'champs.json'
        self.champ_re = re.compile(r'champions(?: \(\d+\))?.csv')

    @commands.command(no_pm=True, pass_context=True)
    @checks.mod_or_permissions(manage_nicknames=True, aliases=['clan_assign', 'clan'])
    async def assign_clan(self, ctx, user : discord.Member, *, clanname=""):
        """Change user's nickname to match his clan

        Leaving the nickname empty will remove it."""
        nickname = '[{}] {}'.format(clanname.strip(), user.name)
        if clanname == "":
            nickname = None
        try:
            await self.bot.change_nickname(user, nickname)
            await self.bot.say("Done.")
        except discord.Forbidden:
            await self.bot.say("I cannot do that, I lack the "
                "\"Manage Nicknames\" permission.")

def setup(bot):
    n = ClanMod(bot)
    bot.add_cog(n)
