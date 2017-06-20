import discord
import re
import csv
import random
import os
from discord.ext import commands

class MCOCOrders:
    '''Tools for Marvel Contest of Champions'''

    def __init__(self, bot):
        self.bot = bot
        self.data_dir = 'data/mcocOrders/servers/{}/'


    def _create_server(self, server):
        if not os.path.exists(self.server.format(server.id)):
            if not os.path.exists(self.data_dir.format(server.id)):
                os.makedirs(self.data_dir.format(server.id))
            orders_data = {
                'user': None,
                'aw' : None,
                'aq1': {'tier1':None,'tier2':None},
                'aq2': {'tier1':None,'tier2':None,'tier3':None},
                'aq3': {'tier1':None,'tier2':None,'tier3':None},
                'aq4': {'tier1':None,'tier2':None,'tier3':None},
                'aq5': {'tier1':None,'tier2':None,'tier3':None},
                'aq6': {'tier1':None,'tier2':None,'tier3':None},
            }
            self.save_champ_data(user, data)


    @commands.group(pass_context=True, aliases=('order',))
    async def orders(self, ctx):
        server = ctx.message.server
        if ctx.invoked_subcommand is None:
            if not os.path.exists(self.server.format(server.id)):
                _create_server(server)
                await self.bot.say('A storage file has been generated for this server')
            await self.bot.send_cmd_help(ctx)
            return

    @orders.group(pass_context=True)
    async def set(self, ctx):
        await self.bot.say("Dummy message for the set command")





def tabulate(table_data, width, rotate=True, header_sep=True):
    rows = []
    cells_in_row = None
    for i in iter_rows(table_data, rotate):
        if cells_in_row is None:
            cells_in_row = len(i)
        elif cells_in_row != len(i):
            raise IndexError("Array is not uniform")
        rows.append('|'.join(['{:^{width}}']*len(i)).format(*i, width=width))
    if header_sep:
        rows.insert(1, '|'.join(['-' * width] * cells_in_row))
    return chat.box('\n'.join(rows))

def setup(bot):
    bot.add_cog(MCOCOrders(bot))
