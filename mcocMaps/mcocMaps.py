import discord
from discord.ext import commands

class MCOCMaps:
    '''Maps for Marvel Contest of Champions'''

    aq_map = {'5':{'map': 'aq5', 'maptitle':'5'},
        '5.1':{'map': 'aq51','maptitle':'5 Tier 1'},
        '5.2':{'map':  'aq52', 'maptitle':'5 Tier 2'},
        '5.3':{'map': 'aq53','maptitle':'5 Tier 3'},}
    lolmap = {'lol':{'map':'lolmap','maptitle':'Labrynth of Legends Map'}}
    warmaps = {'af','ag','ag+','ah','ai','bf','bg','bg+','bh','bi','cf','cg',
                'cg+','ch','ci','df','dg','dg+','dh','ef','eg','eg+','eh','ei'}
    basepath = 'https://raw.githubusercontent.com/JasonJW/mcoc-cogs/master/mcocMaps/data/'
    icon_sdf = 'https://raw.githubusercontent.com/JasonJW/mcoc-cogs/master/mcoc/data/sdf_icon.png'

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, aliases=['warmap','aqmap','aq'])
    async def mmap(self, ctx, *, maptype: str=None):
        '''Select a Map
        lol map: lol
        aq maps : 5, 5.1, 5.2, 5.3
            /aq 5
        war map syntax: /map <left><right>
             <left> = [a, b, c, d, e]
             <right> = [f, g, g+, h, i]'''
        print(len(maptype))
        if maptype is None:
            mapurl = '{}warmap_ai.png'.format(self.basepath, maptype.lower())
            mapTitle = 'Alliance War Map {}'.format(maptype.upper())
            em = discord.Embed(color=discord.Color.gold(),title=mapTitle)
            em.set_image(url=mapurl)
            em.set_footer(text='Presented by [-SDF-]',icon_url=self.icon_sdf)
            await self.bot.say(embed=em)
        elif len(maptype) > 0:
            if maptype in self.aq_map:
                mapurl = '{}{}.png'.format(self.basepath, self.aq_map[maptype]['map'])
                maptitle = 'Alliance Quest {}'.format(self.aq_map[maptype]['maptitle'])
                em = discord.Embed(color=discord.Color.gold(),title=maptitle)
                em.set_image(url=mapurl)
            # elif maptype in self.lolmap:
            #     mapurl = '{}{}.png'.format(self.basepath, self.lolmap[maptype]['map'])
            #     maptitle = '{}'.format(self.aq_map[maptype]['maptitle'])
            #     em = discord.Embed(color=discord.Color.gold(),title=maptitle)
            #     em.set_image(url=mapurl)
            # else:
            #     em=discord.Embed(color=discord.Color.gold(),title='Apologies',description='Summoner, I cannot find a suitable map.')
            em.set_footer(text='Presented by [-SDF-]',icon_url=self.icon_sdf)
            await self.bot.say(embed=em)

def setup(bot):
    bot.add_cog(MCOCMaps(bot))
