import discord
from discord.ext import commands

class MCOCTools:
    '''Tools for Marvel Contest of Champions'''
    lookup_links = {
            'event': (
                'Tiny MCoC Schedule',
                '<http://simians.tk/MCOC-Sched>',
                'Josh Morris Schedule',
                'https://d2jixqqjqj5d23.cloudfront.net/assets/developer/imgs/icons/google-spreadsheet-icon.png'),
            'hook': (
                'hook/champions',
                '<http://hook.github.io/champions>',
                'hook/champions for Collector',
                'https://assets-cdn.github.com/favicon.ico'),
            'spotlight': (
                'MCoC Spotlight',
                '<http://simians.tk/MCoCspotlight>'),
            'marvelsynergy': (
                'Team Builder',
                '<http://www.marvelsynergy.com/team-builder>',
                'Marvel Synergy',
                'http://www.marvelsynergy.com/images/marvelsynergy.png'),
            'alsciende':(
                'Alsciende Mastery Tool',
                '<https://alsciende.github.io/masteries/v10.0.1/#>'
                'by u/alsciende',
                'https://assets-cdn.github.com/favicon.ico')),
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

    def present(self, lookup):
        em=discord.Embed(color=self.mcolor,title=lookup[0],description=lookup[1])
        print(len(lookup))
        if len(lookup) > 2:
            em.set_footer(text=lookup[2],icon_url=lookup[3])
        else:
            em.set_footer(text='Presented by [-SDF-]',icon_url=self.icon_sdf)
        return em

    @commands.command(help=lookup_links['event'][0], aliases=['events','schedule',])
    async def event(self):
        lookup = self.lookup_links['event']
        await self.bot.say(embed=self.present(lookup))

    @commands.command(help=lookup_links['spotlight'][0],)
    async def spotlight(self):
        lookup = self.lookup_links['spotlight']
        await self.bot.say(embed=self.present(lookup))

    @commands.command(help=lookup_links['marvelsynergy'][0])
    async def marvelsynergy(self):
        lookup = self.lookup_links['marvelsynergy']
        await self.bot.say(embed=self.present(lookup))

    @commands.command(help=lookup_links['simulator'][0],aliases=['msim'])
    async def simulator(self):
        lookup = self.lookup_links['simulator']
        await self.bot.say(embed=self.present(lookup))

    @commands.command(help=lookup_links['alsciende'][0], aliases=('mrig',))
    async def alsciende(self):
        lookup = self.lookup_links['alsciende']
        await self.bot.say(embed=self.present(lookup))

    @commands.command(help=lookup_links['streak'][0])
    async def streak(self):
        lookup = self.lookup_links['streak']
        await self.bot.say(embed=self.present(lookup))

    @commands.command(help=lookup_links['hook'][0])
    async def hook(self):
        lookup = self.lookup_links['hook']
        await self.bot.say(embed=self.present(lookup))

def setup(bot):
    bot.add_cog(MCOCTools(bot))
