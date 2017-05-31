import discord
from discord.ext import commands

class Lessons:
    aq_map = {'aq5':{'map': 'aq5', 'maptitle':'5'},
        'aq5.1':{'map': 'aq51','maptitle':'5 Tier 1'},
        'aq5.2':{'map':  'aq52', 'maptitle':'5 Tier 2'},
        'aq5.3':{'map': 'aq53','maptitle':'5 Tier 3'},}

    warmaps = {'af','ag','ag+','ah','ai','bf','bg','bg+','bh','bi','cf','cg',
                'cg+','ch','ci','df','dg','dg+','dh','ef','eg','eg+','eh','ei'}
    basepath = 'https://raw.githubusercontent.com/JasonJW/mcoc-cogs/master/mcoc_maps/data/maps/'
    icon_sdf = 'https://raw.githubusercontent.com/JasonJW/mcoc-cogs/master/mcoc/data/icon_sdf.png'

    @commands.command(aliases=['warmap','aqmap'])
    async def mmap(self, maptype):
        '''Select a Map
        aq syntax: /map aq<num>[.1]
            Where <num> = [1, 2, 3, 4, 5, 6]
            ex: /map aq5.1
        warmap syntax: /map <left><right>
             Where <left> = [a, b, c, d, e]
             Where <right> = [f, g, g+, h, i]
            ex: /map ef'''
        if maptype is not None:
            if maptype in aq_map:
                mapurl = '{}{}.png'.format(basepath, aq_map[maptype]['map'])
                maptitle = 'Alliance Quest {}'.format(aq_map[maptype]['maptitle'])
                em = discord.Embed(color=discord.Color.gold(),title=maptitle)
                em.set_image(url=mapurl)
            elif maptype in warmaps:
                mapurl = '{}{}.png'.format(basepath, maptype.lower())
                mapTitle = 'Alliance War Map {}'.format(maptype.upper())
                em = discord.Embed(color=discord.Color.gold(),title=mapTitle)
                em.set_image(url=mapurl)
            else:
                em=discord.Embed(color=discord.Color.gold(),title='Apologies',desc='Summoner, I cannot find a suitable map.')
                em.set_footer(text='Presented by [-SDF-]',icon_url=icon_sdf)
            await self.bot.say(embed=em)

def setup(bot):
    bot.add_cog(Lessons(bot))
