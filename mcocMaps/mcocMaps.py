import discord
from discord.ext import commands

class MCOCMaps:
    '''Maps for Marvel Contest of Champions'''

    aq_map = {'5':{'map': 'aq5', 'maptitle':'5'},
        '5.1':{'map': 'aq51','maptitle':'5 Tier 1'},
        '5.2':{'map':  'aq52', 'maptitle':'5 Tier 2'},
        '5.3':{'map': 'aq53','maptitle':'5 Tier 3'},}
    lolmaps = {'1':{'map':'lol1', 'maptitle': 'Path 1'},
        '2':{'map':'lol1', 'maptitle': 'Path 2'},
        '3':{'map':'lol1', 'maptitle': 'Path 3'},
        '4':{'map':'lol1', 'maptitle': 'Path 4'},
        '5':{'map':'lol1', 'maptitle': 'Path 5'},
        '6':{'map':'lol1', 'maptitle': 'Path 6'},
        '7':{'map':'lol1', 'maptitle': 'Path 7'},}

    basepath = 'https://raw.githubusercontent.com/JasonJW/mcoc-cogs/master/mcocMaps/data/'
    icon_sdf = 'https://raw.githubusercontent.com/JasonJW/mcoc-cogs/master/mcoc/data/sdf_icon.png'

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, aliases=['aq'])
    async def aqmap(self, ctx, *, maptype: str):
        '''Select a Map
            aq maps : 5, 5.1, 5.2, 5.3
            /aq 5'''
        if maptype in self.aq_map:
            mapurl = '{}{}.png'.format(self.basepath, self.aq_map[maptype]['map'])
            maptitle = 'Alliance Quest {}'.format(self.aq_map[maptype]['maptitle'])
            em = discord.Embed(color=discord.Color.gold(),title=maptitle)
            em.set_image(url=mapurl)
            em.set_footer(text='Presented by [-SDF-]',icon_url=self.icon_sdf)
            await self.bot.say(embed=em)

    @commands.command(pass_context=True, aliases=['lol'])
    async def lolmap(self, ctx, *, maptype: str):
        '''Select a Map
            LOL maps: 1, 2, 3, 4, 5, 6, 7
            /lol 5'''
        if maptype in self.lolmaps:
            mapurl = '{}{}.png'.format(self.basepath, self.lolmaps[maptype]['map'])
            maptitle = 'Labyrinth of Legends: {}'.format(self.lolmaps[maptype]['maptitle'])
            em = discord.Embed(color=discord.Color.gold(),title=maptitle)
            em.set_image(url=mapurl)
            em.set_footer(text='Presented by [-SDF-]',icon_url=self.icon_sdf)
            await self.bot.say(embed=em)

    @commands.command(pass_context=True, aliases=('aw'))
    async def warmap(self, ctx):
        '''Alliance War 2.0 Map'''
        mapurl = '{}warmap_2.png'.format(self.basepath)
        mapTitle = 'Alliance War 2.0 Map'
        em = discord.Embed(color=discord.Color.gold(),title=mapTitle)
        em.set_image(url=mapurl)
        em.set_footer(text='Presented by [-SDF-]',icon_url=self.icon_sdf)
        await self.bot.say(embed=em)


def setup(bot):
    bot.add_cog(MCOCMaps(bot))
