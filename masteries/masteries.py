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

COLORS = {'Offense': discord.Color.red(), 'Defense': discord.Color.blue(), 'Utility': discord.Color.green()}

class masteries:
    '''Mastery Tools for Marvel Contest of Champions'''

    def __init__(self, bot):
        self.bot = bot
        self.masteriesJSON = "data/masteries/masteries.json"
        MASTERY = dataIO.load_json(self.masteriesJSON)

    @commands.group(pass_context=True)
    async def masteries(self, ctx):
        if ctx.invoked_subcommand is None:
            try:
                await self.command_arg_help(ctx)
            except:
                await send_cmd_help(ctx)
            return

    @masteries.command(pass_context=True)
    async def list(self, ctx):
        '''Just lists Masteries'''
        keys = MASTERY.keys()
        offense = []
        defense = []
        utility = []
        for key in keys:
            if key['category'] == 'Offense':
                offense.append(key)
            elif key['category'] == 'Defense':
                defense.append(key)
            else:
                utility.append(key)
        em=discord.Embed(title='Mastery List by Category', description='')
        em.add_field(name='Offense', value='\n'.join(offense))
        em.add_field(name='Defense', value='\n'.join(defense))
        em.add_field(name='Utility', value='\n'.join(utility))
        await self.bot.say(embed=em)



def setup(bot):
    bot.add_cog(masteries(bot))
