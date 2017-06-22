import discord
import re
import csv
import random
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
                '<http://simians.tk/MCoCspotlight>\n \nMCOC Spotlight Discord\n<https://discord.gg/wJqpYGS>'),
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
    mcolor = discord.Color.red()
    icon_sdf = 'https://raw.githubusercontent.com/JasonJW/mcoc-cogs/master/mcoc/data/sdf_icon.png'
    dataset = 'data/mcoc/masteries.csv'

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

    @commands.command(manage_server=True,pass_context=True)
    async def collectorsetup(self,ctx):
        server = ctx.message.server
        # 1 ) Check permissions
        # 2 ) Check roles
        # 3 ) Check role order
        rolenames = []
        roles = server.roles
        for r in roles:
            rolenames.append(r.name)
        required_roles={'bg1','bg2','bg3','officers','ROL','RTL','LOL','100\%\Act4','LEGEND','Summoner'}
        for i in required_roles:
            if i not in rolenames:
                await self.bot.say('Setup Error: add role {}'.format(i))

        role_hierarchy = server.role_hierarchy
        print(role_hierarchy)
        await self.bot.say('collectorsetup complete')

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

    @commands.command()
    async def keygen(self, prefix='SECEMP99'):
        letters='ABCDEFGHIJKLMNOPQURSTUVWXYZ'
        package = []
        for i in range(0,9):
            lets='{}{}{}{}'.format(random.choice(letters),random.choice(letters),random.choice(letters),random.choice(letters))
            package.append(prefix+lets)
        em=discord.Embed(color=discord.Color.gold(),title='Email Code Generator',description='\n'.join(package))
        await self.bot.say(embed=em)
#### Mastery stuff###
# class MCOCMastery:
    masteryColor={'Offense': discord.Color.red(),
            'Defense': discord.Color.blue(),
            'Utility': discord.Color.green()}
    tokens={'Vitality','Greater Vitality','Salve','Recovery','Energy Resistance','Physical Resistance','Block Proficiency','Perfect Block','Stand Your Ground','Collar Tech','Serum Science','Willpower','Coagulate','Suture','Inequity','Resonate',
            'Strength','Greater Strength','Pierce','Lesser Precision','Precision','Lesser Cruelty','Cruelty','Courage','Extended Fury','Enhanced Fury','Pure Skill','Mutagenesis','Glass Canon','Recoil','Liquid Courage','Double Edge','Despair','DeepWounds','Unfazed','Assassin',
            'Wisdom','Intelligence','Limber','Parry','Stupefy','Petrify','Pacify','Dexterity','Pitance','Prosperity','Cosmic Awareness','Mystic Dispersion','Detect Cosmic','Detect Tech','Detect Mystic','Scouter Lens','Detect Mutant','Detect Science','Detect Skill'}

    @commands.group(pass_context=True, aliases=['masteries',])
    async def mastery(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)
            return

    @mastery.command(pass_context=True,)
    async def test(self,ctx):
        message = ctx.message.content
        # mastery='Resonate'
        # rank=3
        # rows = get_csv_rows(self.dataset,'Mastery',mastery)
        #  text = []
        # cost = {'ucarb': 'Carbonadium Mastery Core', 'ustony': 'Stony Mastery Core', 'uclass': '', 'uunit': 'Units', 'rgold': 'Gold', 'runit': 'Units'}
        # cores = {'Collar Tech': 'Tech Core', 'Serum Science': 'Mastery Serum', 'Mutagenesis': 'Mastery Core X', 'Pure Skill': 'Mastery Core of Apptitude', 'Cosmic Awareness':'Cosmic Mastery Core', 'Mystic Dispersion': 'Mystical Mastery Core',
        #         'Detect Tech': 'Tech Core', 'Detect Science': 'Mastery Serum', 'Detect Mutant': 'Mastery Core X', 'Detect Skill': 'Mastery Core of Apptitude', 'Detect Cosmic':'Cosmic Mastery Core', 'Detect Mystic': 'Mystical Mastery Core',}
        # if mastery in cores:
        #     cost['uclass'][1]=cores[mastery]
        for token in self.tokens:
            print(token+' found')
            if token in message:
                maxrank = rows[0]['Max Ranks']
                category = rows[0]['Category']

                em=discord.Embed(color=self.masteryColor[category],title=mastery,description=' '.join(t for t in text))
                # for r in maxrank:
                    # unlock, rankcost = _get_cost(mastery, r)
                unlock, rankcost = self._get_cost(mastery)

                em.add_field(name='Unlock Cost',value='\n'.join(u[0] for u in unlock))
                em.add_field(name='Rank Cost',value='\n'.join(r for r in rankcost))
                await self.bot.say(embed=em)

    @mastery.command(pass_context=True, name='cost')
    async def _cost(self,ctx):
        # message = ctx.message.content.split(' ')
        # stack = []
        # for i in range(0,len(message)-1):
        #     if i+1 < len(message):
        #         test='{} {}'.format(message[i],message[i+1])
        #         if test in self.tokens:
        #             stack.append(test)
        #             i=i+2
        #         elif message[i] in self.tokens:
        #             stack.append(message[i])
        #     else:
        #         if message[i] in self.tokens:
        #             stack.append(message[i])
        # await self.bot.say('\n'.join(stack))

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

    # def _get_cost(self, mastery):
    #     row = csv_get_row(self.dataset,'Mastery',mastery)
    #     cost = {'ucarb': 'Carbonadium Mastery Core', 'ustony': 'Stony Mastery Core', 'uclass': '', 'uunit': 'Units', 'rgold': 'Gold', 'runit': 'Units'}
    #     cores = {'Collar Tech': 'Tech Core', 'Serum Science': 'Mastery Serum', 'Mutagenesis': 'Mastery Core X', 'Pure Skill': 'Mastery Core of Apptitude', 'Cosmic Awareness':'Cosmic Mastery Core', 'Mystic Dispersion': 'Mystical Mastery Core',
    #             'Detect Tech': 'Tech Core', 'Detect Science': 'Mastery Serum', 'Detect Mutant': 'Mastery Core X', 'Detect Skill': 'Mastery Core of Apptitude', 'Detect Cosmic':'Cosmic Mastery Core', 'Detect Mystic': 'Mystical Mastery Core',}
        # if mastery in cores:
        #     classcore=cores[mastery]
        # unlockcost=[]
        # rankcost=[]
        # maxranks=row['maxranks']
        # carbcost=row['ucarb'].split(',')
        # stonycost=row['ustony'].split(',')
        # classcost=row['uclass'].split(',')
        # unitcost=row['uunit'].split(',')
        # if len(carbcost) > 0:
        #     unlockcost.append({'ucarb':{carbcost,'Carbonadium Mastery Core'})
        # if len(stonycost) > 0:
        #     unlockcost.append({'ustony':{stonycost,'Stony Mastery Core'})
        # if len(classcost) > 0:
        #     unlockcost.append({'uclass':{classcost,classcore})
        # if len(unitcost) > 0:
        #     unlockcost.append({'uunit':{unitcost,'Units'})
        # goldrank=row['rgold'].split(',')
        # unitrank=row['runit'].split(',')
        # if len(goldrank) > 0:
        #     rankcost.append({'rgold':{goldrank,'Gold'})
        # if len(unitrank) > 0:
        #     unlockcost.append({'runit':{unitrank,'Units'})
        #
        # return unlockcost, rankcost


    def _get_text(self, mastery, rank):
        rows = csv_get_rows(self.dataset,'Mastery',mastery)
        for row in rows:
            text.append(row['Text'].format(row[str(rank)]))
        return text


def load_csv(filename):
    return csv.DictReader(open(filename))

def get_csv_row(filecsv, column, match_val, default=None):
    print(match_val)
    csvfile = load_csv(filecsv)
    for row in csvfile:
        if row[column] == match_val:
            if default is not None:
                for k, v in row.items():
                    if v == '':
                        row[k] = default
            return row

def get_csv_rows(filecsv, column, match_val, default=None):
    print(match_val)
    csvfile = load_csv(filecsv)
    package =[]
    for row in csvfile:
        if row[column] == match_val:
            if default is not None:
                for k, v in row.items():
                    if v == '':
                        row[k] = default
            package.append(row)
    return package

def tabulate(table_data, width, rotate=True, header_sep=True):
    rows = []
    cells_in_row = None
    for i in iter_rows(table_data, rotate):
        if cells_in_row is None:
            cells_in_row = len(i)
        elif cells_in_row != len(i):
            raise IndexError("Array is not uniform")
        rows.append('|'.join(['{:^{width}}']*len(i)).format(*i, width=width))
    if header_sep:
        rows.insert(1, '|'.join(['-' * width] * cells_in_row))
    return chat.box('\n'.join(rows))



def setup(bot):
    bot.add_cog(MCOCTools(bot))
