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
    mfooter = (text='Presented by [-SDF-]',icon_url=icon_sdf)

    def __init__(self, bot):
        self.bot = bot

    @commands.command(help=lookup_links['event'][0], aliases=['events','schedule','event'])
    async def tool_event(self):
        # await self.bot.say('**{}**\n{}'.format(*self.lookup_links['event']))
        em=discord.Embed(color=self.mcolor,title=self.lookup_links['event'],description='')
        em.set_footer('Presented by [-SDF-]',icon_url=self.icon_sdf)
        await self.bot.say(embed=em)

    @commands.command(help=lookup_links['spotlight'][0], aliases=['spotlight'])
    async def tool_spotlight(self):
        await self.bot.say('**{}**\n{}'.format(*self.lookup_links['spotlight']))

    @commands.command(help=lookup_links['marvelsynergy'][0])
    async def marvelsynergy(self):
        await self.bot.say('**{}**\n{}'.format(*self.lookup_links['marvelsynergy']))

    @commands.command(help=lookup_links['simulator'][0])
    async def simulator(self):
        await self.bot.say('**{}**\n{}'.format(*self.lookup_links['simulator']))

    @commands.command(help=lookup_links['alsciende'][0], aliases=('mrig',))
    async def alsciende(self):
        await self.bot.say('**{}**\n{}'.format(*self.lookup_links['alsciende']))

    @commands.command(help=lookup_links['streak'][0])
    async def streak(self):
        await self.bot.say('**{}**\n{}'.format(*self.lookup_links['streak']))

    @commands.command(help=lookup_links['hook'][0])
    async def tool_hook(self):
        await self.bot.say('**{}**\n{}'.format(*self.lookup_links['hook']))


    def present(self, ptitle, plink, ppayload, pfooter):
        em = discord.embed(color=discord.Color.gold(),title=ptitle,description=ppayload)




    @commands.command()
    async def phc(self):
        '''Premium Hero Crystal Release Dates'''
        await self.bot.upload(data_files['phc_jpg']['local'],
                content='Dates Champs are added to PHC (and as 5* Featured for 2nd time)')

def setup(bot):
    bot.add_cog(MCOCTools(bot))
