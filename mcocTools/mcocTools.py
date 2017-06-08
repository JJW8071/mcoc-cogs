import discord
import re
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
                '<https://alsciende.github.io/masteries/v10.0.1/#>',
                'by u/alsciende',
                'https://assets-cdn.github.com/favicon.ico'),
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
        mcoc = self.bot.get_cog('MCOC')

    def present(self, lookup):
        em=discord.Embed(color=self.mcolor,title=lookup[0],description=lookup[1])
        print(len(lookup))
        if len(lookup) > 2:
            em.set_footer(text=lookup[2],icon_url=lookup[3])
        else:
            em.set_footer(text='Presented by [-SDF-]',icon_url=self.icon_sdf)
        return em

    #Gold Realm disabled
    # @commands.command()
    # async def gold(self,msg = None):
    #     '''Gold Realm Schedule'''
    #     package = '```           PST      CST      EST\nJun 5    10:00    12:00    13:00\nJun 5    19:00    21:00    22:00\nJun 6     4:00     6:00     7:00\nJun 6    13:00    15:00    16:00\nJun 6    22:00     0:00     1:00\nJun 7     7:00     9:00    10:00\nJun 7    16:00    18:00    19:00\nJun 8     1:00     3:00     4:00\nJun 8    10:00    12:00    13:00\nJun 8    19:00    21:00    22:00\nJun 9     4:00     6:00     7:00\nJun 9    13:00    15:00    16:00\nJun 10   22:00     0:00     1:00\nJun 11    7:00     9:00    10:00\nJun 11   16:00    18:00    19:00\nJun 12    1:00     3:00     4:00```'
    #     # await self.bot.say('```'+package+'```')
    #     if msg is not None:
    #         package = msg+'\n'+package
    #     em = discord.Embed(color=discord.Color.gold(),title='Gold Realm Schedule',description=package)
    #     em.set_footer(text='Presented by [-SDF-]',icon_url=self.icon_sdf)
    #     await self.bot.say(embed=em)

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

#### Mastery stuff###
# class MCOCMastery:
    masteryColor={'Offense': discord.Color.red(),
            'Defense': discord.Color.blue(),
            'Utility': discord.Color.green()}
    tokens={'Vitality','Greater Vitality','Salve','Recovery','Energy Resistance','Physical Resistance','Block Proficiancy','Perfect Block','Stand Your Ground','Collar Tech','Serum Science','Willpower','Coagulate','Suture','Inequity','Resonate',
            'Strength','Greater Strength','Pierce','Lesser Precision','Precision','Lesser Cruelty','Cruelty','Courage','Extended Fury','Enhanced Fury','Pure Skill','Mutagenesis','Glass Canon','Recoil','Liquid Courage','Double Edge','Despair','DeepWounds','Unfazed','Assassin',
            'Wisdom','Intelligence','Limber','Parry','Stupefy','Petrify','Pacify','Dexterity','Pitance','Prosperity','Cosmic Awareness','Mystic Dispersion','Detect Cosmic','Detect Tech','Detect Mystic','Scouter Lens','Detect Mutant','Detect Science','Detect Skill'}

    @commands.group(pass_context=True, aliases=['masteries',])
    async def mastery(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)
            return

    @mastery.command(pass_context=True, aliases=['test'])
    async def _test(self,ctx):
        mastery='Resonate'
        rank=3
        rows = csv_get_rows(mcoc.data_files['masteries']['local'],'Mastery',mastery)
        text = {}
        cost = {'ucarb': {0, 'Carbonadium Mastery Core'}, 'ustoney': {0,'Stony Mastery Core'}, 'uclass': {0,''}, 'uunit': {0, 'Units'}, 'rgold': {0,'Gold'}, 'runit': {0,'Units'}}
        cores = {'Collar Tech': 'Tech Core', 'Serum Science': 'Mastery Serum', 'Mutagenesis': 'Mastery Core X', 'Pure Skill': 'Mastery Core of Apptitude', 'Cosmic Awareness':'Cosmic Mastery Core', 'Mystic Dispersion': 'Mystical Mastery Core',
                'Detect Tech': 'Tech Core', 'Detect Science': 'Mastery Serum', 'Detect Mutant': 'Mastery Core X', 'Detect Skill': 'Mastery Core of Apptitude', 'Detect Cosmic':'Cosmic Mastery Core', 'Detect Mystic': 'Mystical Mastery Core',}
        if mastery in cores:
            cost['uclass'][1]=cores[mastery]
        category = rows[0]['Category']
        for row in rows:
            text.append(row['Text'].format(row[str(rank)]))
        for c in cost:
            c[1]=rows[0][c[0]+str(rank)]

        em=discord.Embed(color=masteryColor[category],title=mastery,description=' '.join(t for t in text))
        unlock=[]
        rank=[]
        for i in {0, 1, 2, 3}:
            if cost[i][0] > 0:
                unlock.append('{}x {}'.format(cost[i][1], cost[i][0])
        for i in {4, 5}
            if cost[i][0] > 0:
                unlock.append('{}x {}'.format(cost[i][1], cost[i][0])
        em.add_field(name='Unlock Cost',value='\n'.join(u for u in unlock))
        em.add_field(name='Rank Cost',value='\n'.join(r for r in rank))




    @mastery.command(pass_context=True, name='cost')
    async def _cost(self,ctx):
        # args = ctx.split(' ')
        #
        # for arg in args:
        #     # parse_re = re.compile(r'''(?:r(?P<rank>[0-9]))|(?:d(?P<debug>[0-9]{1,2}))''', re.X)
        #     if arg in tokens:
        #         row = mcoc.csv_get_row(mcoc.data_files['masteries']['local'], 'MasteryExt', arg)

        await self.bot.say('Dummy message for cost')

    @mastery.command(pass_context=True, name='set')
    async def _set(self,ctx):
        await self.bot.say('Dummy message for set')




def setup(bot):
    bot.add_cog(MCOCTools(bot))
