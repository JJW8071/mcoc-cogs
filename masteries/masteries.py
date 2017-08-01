import discord
import re
import random
import os
from .utils.dataIO import dataIO
import datetime
from operator import itemgetter, attrgetter
from .utils import chat_formatting as chat
from cogs.utils import checks
from discord.ext import commands
from __main__ import send_cmd_help


COLORS = {'Offense': discord.Color.red(), 'Defense': discord.Color.blue(), 'Utility': discord.Color.green()}

class masteries:
    '''Mastery Tools for Marvel Contest of Champions'''

    def __init__(self, bot):
        self.bot = bot
        self.masteryJSON="data/masteries/masteries.json"
        self.MDATA = dataIO.load_json(self.masteryJSON)

    @commands.group(pass_context=True)
    async def masteries(self, ctx):
        if ctx.invoked_subcommand is None:
            try:
                await self.command_arg_help(ctx)
            except:
                await send_cmd_help(ctx)
            return

    @masteries.command(pass_context=True)
    async def listed(self, ctx):
        '''Just lists Masteries'''
        keys = self.MDATA.keys()
        offense = []
        defense = []
        utility = []
        embeds = []
        for key in keys:
            if 'Offense' in MDATA[key]:
                offense.append(key)
            elif 'Defense' in MDATA[key]:
                defense.append(key)
            else:
                utility.append(key)
        embeds.append(discord.Embed(color=COLORS['Offense'],title='Offense', description='\n'.join(offense)))
        embeds.append(discord.Embed(color=COLORS['Defense'],title='Defense', description='\n'.join(defense)))
        embeds.append(discord.Embed(color=COLORS['Utility'],title='Utility', description='\n'.join(utility)))
        for em in embeds:
            await self.bot.say(embed=em)



def setup(bot):
    bot.add_cog(masteries(bot))
