import re
import discord
from math import *
from random import *
from discord.ext import commands


class Calculator:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, name='calculator', aliases=('calc',))
    async def _calc(self, context, *, m):
        print(m)
        m = ''.join(m)
        math_filter = re.findall(r'[\[\]\-()*+/0-9=.,% ]|>|<|==|>=|<=|\||&|~|!=|^|sum'
        		+ '|range|random|randint|choice|randrange|True|False|if|and|or|else'
        		+ '|is|not|for|in|acos|acosh|asin|asinh|atan|atan2|atanh|ceil'
        		+ '|copysign|cos|cosh|degrees|e|erf|erfc|exp|expm1|fabs|factorial'
        		+ '|floor|fmod|frexp|fsum|gamma|gcd|hypot|inf|isclose|isfinite'
        		+ '|isinf|isnan|ldexp|lgamma|log|log10|log1p|log2|modf|nan|pi'
        		+ '|pow|radians|sin|sinh|sqrt|tan|tanh|round', m)
        print(''.join(math_filter))
        calculate_stuff = eval(''.join(math_filter))
        if len(str(calculate_stuff)) > 0:
            em = discord.Embed(color=discord.Color.blue(), 
            	description='**Input**\n`{}`\n\n**Result**\n`{}`'.format(m, calculate_stuff))
            await self.bot.say(embed=em)


def setup(bot):
    bot.add_cog(Calculator(bot))
