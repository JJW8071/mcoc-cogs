import re
import discord
from math import *
from random import *
from discord.ext import commands


class Calculator:
    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True, name='calculator')
    async def _calc(self, context, *, m):
        m = ''.join(m)
        math_filter = re.findall(r'[\[\]\-()*+/0-9=.,% ]|random|randint|choice'+
            r'|randrange|True|False|if|and|or|else|is|acos|acosh|asin|asinh' +
            r'|atan|atan2|atanh|ceil|copysign|cos|cosh|degrees|e|erf|erfc|exp' +
            r'|expm1|fabs|factorial|floor|fmod|frexp|fsum|gamma|gcd|hypot|inf' +
            r'|isclose|isfinite|isinf|isnan|round|ldexp|lgamma|log|log10|log1p' +
            r'|log2|modf|nan|pi|pow|radians|sin|sinh|sqrt|tan|tanh', m)
        calculate_stuff = eval(''.join(math_filter))
        if len(str(calculate_stuff)) > 0:
            em = discord.Embed(color=discord.Color.blue(), description='**Input**\n`{}`\n\n**Result**\n`{}`'.format(m, calculate_stuff))
            await self.bot.say(embed=em)


def setup(bot):
    bot.add_cog(Calculator(bot))
