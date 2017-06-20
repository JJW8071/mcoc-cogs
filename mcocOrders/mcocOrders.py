import discord
import re
import csv
import random
from discord.ext import commands

class MCOCOrders:
    '''Tools for Marvel Contest of Champions'''


    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True, aliases=('order',))
    async def orders(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)
            return

    @orders.group(pass_context=True, aliases=['set',])
    async def _set(self, ctx):
        await self.bot.say("Dummy message for the _set command")





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
