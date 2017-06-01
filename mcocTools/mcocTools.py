import discord
from discord.ext import commands

class MCOCTools:
    '''Tools for Marvel Contest of Champions'''
    lookup_links = {
            'event': (
                'Tiny MCoC Schedule',
                '<http://simians.tk/MCOC-Sched>'),
            'hook': (
                'hook/champions',
                '<http://hook.github.io/champions>'),
            'spotlight': (
                'MCoC Spotlight',
                '<http://simians.tk/MCoCspotlight>'),
            'marvelsynergy': (
                'Marvel Synergy Builder',
                '<http://www.marvelsynergy.com/team-builder>'),
            'alsciende':(
                'Alsciende Mastery Tool',
                '<https://alsciende.github.io/masteries/v10.0.1/#>'),
            'simulator': (
                'Mastery Simulator',
                '<http://simians.tk/msimSDF>'),
            'streak': (
                'Infinite Streak',
                'http://simians.tk/-sdf-streak')
                #'http://simians.tk/SDFstreak')
    }
    mcolor = discord.Color.gold()
    icon_sdf = 'https://raw.githubusercontent.com/JasonJW/mcoc-cogs/master/mcoc/data/sdf_icon.png'

    def __init__(self, bot):
        self.bot = bot

    @commands.command(help=lookup_links['event'][0], aliases=['events','schedule',])
    async def event(self):
        # await self.bot.say('**{}**\n{}'.format(*self.lookup_links['event']))
        lookup = *self.lookup_links['event']
        etitle = lookup[0]
        edesc = lookup[1]
        em=discord.Embed(color=discord.Color.gold(),title=title,description=edesc)
        em.set_footer(text='Presented by [-SDF-]',icon_url=*self.icon_sdf)
        await self.bot.say(embed=em)

    @commands.command(help=lookup_links['spotlight'][0],)
    async def spotlight(self):
        '''[-SDF-] Spotlight Dataset'''
        await self.bot.say('**{}**\n{}'.format(*self.lookup_links['spotlight']))

    @commands.command(help=lookup_links['marvelsynergy'][0])
    async def marvelsynergy(self):
        '''Link to MarvelSynergy'''
        await self.bot.say('**{}**\n{}'.format(*self.lookup_links['marvelsynergy']))

    @commands.command(help=lookup_links['simulator'][0])
    async def simulator(self):
        '''Pre-12.0 Mastery Simulator'''
        await self.bot.say('**{}**\n{}'.format(*self.lookup_links['simulator']))

    @commands.command(help=lookup_links['alsciende'][0], aliases=('mrig',))
    async def alsciende(self):
        '''Alsciende's Mastery Modeling Tool'''
        await self.bot.say('**{}**\n{}'.format(*self.lookup_links['alsciende']))

    @commands.command(help=lookup_links['streak'][0])
    async def streak(self):
        '''[-SDF-] Streak Chart'''
        await self.bot.say('**{}**\n{}'.format(*self.lookup_links['streak']))

    @commands.command(help=lookup_links['hook'][0])
    async def tool_hook(self):
        '''hook/champions Link'''
        await self.bot.say('**{}**\n{}'.format(*self.lookup_links['hook']))

    @commands.command()
    async def phc(self):
        '''Premium Hero Crystal Release Dates'''
        await self.bot.upload(data_files['phc_jpg']['local'],
                content='Dates Champs are added to PHC (and as 5* Featured for 2nd time)')

def setup(bot):
    bot.add_cog(MCOCTools(bot))
