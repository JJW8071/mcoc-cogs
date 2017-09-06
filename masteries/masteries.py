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
ALSCIENDE = 'https://alsciende.github.io/masteries/v10.0.1/#{}'
GS_BASE='https://sheets.googleapis.com/v4/spreadsheets/{}/values/{}?key=AIzaSyBugcjKbOABZEn-tBOxkj0O7j5WGyz80uA&majorDimension=ROWS'

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
    async def save(self, url):
        '''Submit Alsciend URL'''
        if url is not None:



    @masteries.command(pass_context=True)
    async def listed(self, ctx):
        '''Just lists Masteries'''
        keys = self.MDATA.keys()
        offense = []
        defense = []
        utility = []
        embeds = []
        for key in keys:
            if 'Offense' in self.MDATA[key]['category']:
                offense.append(key)
            elif 'Defense' in self.MDATA[key]['category']:
                defense.append(key)
            else:
                utility.append(key)
        embeds.append(discord.Embed(color=COLORS['Offense'],title='Offense', description='\n'.join(offense)))
        embeds.append(discord.Embed(color=COLORS['Defense'],title='Defense', description='\n'.join(defense)))
        embeds.append(discord.Embed(color=COLORS['Utility'],title='Utility', description='\n'.join(utility)))
        for em in embeds:
            await self.bot.say(embed=em)
    #
    # @masteries.command(pass_context=True)
    # async def cost(self, ctx, *, selected):
    #     await self.bot.say('looking up: ' + selected)
    #     if selected in MDATA.keys():
    #         effects =[]
    #         pibump =[]
    #         ucarbs =[]
    #         uclass =[]
    #         uunits =[]
    #         ustony =[]
    #         rgold =[]
    #         runit =[]
    #         ranks = MDATA[selected][ranks]
    #         for rank in ranks:
    #             ucarbs
    async def get_masteries(self, url, embed=None):
        # '''If Debug is sent, data will refresh'''
        # sheet = '1mEnMrBI5c8Tbszr0Zne6qHkW6WxZMXBOuZGe9XmrZm8'
        # range_headers = 'masteryjson!A1:R1'
        # range_body = 'masteryjson!A2:R'
        # foldername = 'synergies'
        # filename = 'synergies'
        # if champs[0].debug:
        #     head_url = GS_BASE.format(sheet,range_headers)
        #     body_url = GS_BASE.format(sheet,range_body)
        #     champ_synergies = await self.gs_to_json(head_url, body_url, foldername, filename)
        #     message = await self.bot.say('Collecting Synergy data ...')
        #     await self.bot.upload(self.shell_json.format(foldername,filename))
        # else:
        #     getfile = self.shell_json.format(foldername, filename)
        #     champ_synergies = dataIO.load_json(getfile)

        # GS_BASE='https://sheets.googleapis.com/v4/spreadsheets/1Apun0aUcr8HcrGmIODGJYhr-ZXBCE_lAR7EaFg_ZJDY/values/Synergies!A2:L1250?key=AIzaSyBugcjKbOABZEn-tBOxkj0O7j5WGyz80uA&majorDimension=ROWS'

    async def gs_to_json(self, head_url=None, body_url=None, foldername=None, filename=None, groupby_value=None):
        if head_url is not None:
            async with aiohttp.get(head_url) as response:
                try:
                    header_json = await response.json()
                except:
                    print('No header data found.')
                    return
            header_values = header_json['values']



def setup(bot):
    bot.add_cog(masteries(bot))
