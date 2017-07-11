import discord
from discord.ext import commands

class DND:
    """D&D Lookup Stuff"""
    baseurl = "http://dnd5eapi.co/api/"

    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True, invoke_without_command=True)
    async def dnd(self, ctx, *, hargs=''):
        if ctx.invoked_subcommand is None:
            await self.bot.say('DEBUG: hargs = '+ hargs)
            return

    @dnd.command()
    async def spells(self, ctx, *, hargs):
        """Lookup Spells"""
        baseurl = self.baseurl+'spells'
        #Your code will go here
        await self.bot.say("Lookup Spells initiated.")

    @dnd.command()
    async def classes(self, ctx, *, hargs):
        """Lookup Classes"""
        baseurl = self.baseurl+'classes'
        #Your code will go here
        await self.bot.say("Lookup Classes initiated.")

    @dnd.command()
    async def monsters(self, ctx, *, hargs):
        """Lookup monsters"""
        baseurl = self.baseurl+'monsters'
        #Your code will go here
        await self.bot.say("Lookup Monsters initiated.")

    @dnd.command()
    async def equipment(self, ctx, *, hargs):
        """Lookup Equpiment"""
        baseurl = self.baseurl+'equipment'
        #Your code will go here
        await self.bot.say("Lookup Spells initiated.")


    def _get_file(url):
        async with aiohttp.ClientSession() as session:
            async with session.get(attachment['url']) as response:
                file_txt = await response.text()

    def _parse_hargs(hargs):



def setup(bot):
    bot.add_cog(Mycog(bot))
