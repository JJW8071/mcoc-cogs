import discord
import re
import csv
import random
import os
import datetime
from .utils import chat_formatting as chat
from discord.ext import commands

class MCOCTools:
    '''Tools for Marvel Contest of Champions'''
    lookup_links = {
            'event': (
                '<http://simians.tk/MCOC-Sched>',
                '[Tiny MCoC Schedule](http://simians.tk/MCOC-Sched)',
                'Josh Morris Schedule',
                'https://d2jixqqjqj5d23.cloudfront.net/assets/developer/imgs/icons/google-spreadsheet-icon.png'),
            'rttl':(
                '<https://drive.google.com/file/d/0B4ozoShtX2kFcDV4R3lQb1hnVnc/view>',
                '[Road to the Labyrinth Opponent List](https://drive.google.com/file/d/0B4ozoShtX2kFcDV4R3lQb1hnVnc/view)',
                'by Regal Empire {OG Wolvz}',
                'http://svgur.com/s/48'),
            'hook': (
                '<http://hook.github.io/champions>',
                '[hook/Champions by gabriel](http://hook.github.io/champions)',
                'hook/champions for Collector',
                'https://assets-cdn.github.com/favicon.ico'),
            'spotlight': (
                '<http://simians.tk/MCoCspotlight>',
                '[MCOC Spotlight Dataset](http://simians.tk/MCoCspotlight)\nIf you would like to donate prestige, signatures or stats, join us at \n[MCOC Spotlight on Discord](https://discord.gg/wJqpYGS)'),
            'marvelsynergy': (
                'http://www.marvelsynergy.com/team-builder>',
                '[Marvel Synergy Team Builder](http://www.marvelsynergy.com/team-builder)',
                'Marvel Synergy',
                'http://www.marvelsynergy.com/images/marvelsynergy.png'),
            'alsciende':(
                '<https://alsciende.github.io/masteries/v10.0.1/#>',
                '[Alsciende Mastery Tool](https://alsciende.github.io/masteries/v10.0.1/#)',
                'by u/alsciende',
                'https://assets-cdn.github.com/favicon.ico'),
            'simulator': (
                '<http://simians.tk/msimSDF>',
                '[-SDF- Mastery Simulator](http://simians.tk/msimSDF)'),
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
        em=discord.Embed(color=self.mcolor,title='',description=lookup[1])
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

    @commands.command(manage_server=True, manage_roles=True, pass_context=True)
    async def collectorsetup(self,ctx,*args):
        '''Server Setup Guide
        ### IN DEVELOPMENT - ALPHA ###
        As in, don't do this at home.
        '''
        server = ctx.message.server
        # 1 ) Check permissions
        # Manage Messages required for Cleanup
        # Manage Server required for Role Creation / Deletion
        # Manage Roles required for Role assignment / removal
        # 2 ) Check roles
        # 3 ) Check role order
        rolenames = []
        roles = server.roles
        phase_one = True
        for r in roles:
            rolenames.append(r.name)
        required_roles={'Collector','officers','bg1','bg2','bg3','LEGEND','100%LOL','LOL','RTL','ROL','100%Act4','Summoner'}
        roles_fields={'officers': {True, discord.Color.lighter_grey(),},
                    'bg1':{True, discord.Color.blue(), },
                    'bg2':{True, discord.Color.purple(), },
                    'bg3':{True, discord.Color.orange(), },}
        stageone=['Setup Conditions 1:\nRoles Required for Guild Setup:',]
        em=discord.Embed(color=discord.Color.gold(),title='Server Setup Protocol',description='')
        message0 = await self.bot.say(embed=em)
        for i in required_roles:
            if i in rolenames:
                stageone.append(':white_check_mark: {}'.format(i))
            else:
                stageone.append(':negative_squared_cross_mark: {}'.format(i))
                phase_one = False
        pages = chat.pagify('\n'.join(stageone))
        messages = []
        for page in pages:
            em = discord.Embed(color=discord.Color.gold(),title='',description=page)
            message = await self.bot.say(embed=em)
            messages.append(message)
        # await self.bot.say('\n'.join(stageone))
        if phase_one == False:
            em = discord.Embed(color=discord.Color.gold(),title='Server Setup Protocol', description='Stage 1: Roles')
            em.add_field(name='Corrective Action', value='Roles are missing. Do you want me to create missing Roles?\nIf yes, click the 🆗 reaction')
            message = await self.bot.say(embed=em)
            await self.bot.add_reaction(message, "🆗")
            await self.bot.add_reaction(message,'❌')
            react = await self.bot.wait_for_reaction(message=message, user=ctx.message.author,timeout=int(30),emoji=['🆗','❌'])
            if react is None or react.reaction.emoji == "❌":
                try:
                    try:
                        await self.bot.delete_message(message)
                        await self.bot.delete_message(message0)
                        for message in messages:
                            await self.bot.delete(message)
                        # await self.bot.clear_reactions(message)
                    except:
                        await self.bot.remove_reaction(message, "🆗", self.bot.user)
                except:
                    pass
                return None
            elif react.reaction.emoji == "🆗":
                await self.bot.say('Activate Role Order Correction')
                for i in required_roles:
                    if i not in rolenames:
                        try:
                            await discord.Client.create_role(server,name=i, mentionable=roles_fields[i][0], color=roles_fields[i][1])
                        except:
                            await self.bot.say('Could not create role: {}'.format(i))

            # await self.bot.say('Roles are out of Order.\nCorrect order and rerun ``/collectorsetup``')

                # await self.bot.say('Setup Error: add role {}'.format(i))

        # role_hierarchy = server.role_hierarchy
        # roleorder = ['Setup Conditions 2:\nRole Order: ']
        # for role in role_hierarchy:
        #
        #     # roleorder.append('{}'.format(role.name))
        # await self.bot.say('\n'.join(roleorder))
        # print(role_hierarchy)
        # await self.bot.say('collectorsetup complete')

    @commands.command(pass_context=True,aliases={'collector','infocollector'})
    async def aboutcollector(self,ctx):
        """Shows info about Collector"""
        author_repo = "https://github.com/Twentysix26"
        red_repo = author_repo + "/Red-DiscordBot"
        server_url = "https://discord.gg/wJqpYGS"
        dpy_repo = "https://github.com/Rapptz/discord.py"
        python_url = "https://www.python.org/"
        since = datetime.datetime(2016, 1, 2, 0, 0)
        days_since = (datetime.datetime.utcnow() - since).days
        dpy_version = "[{}]({})".format(discord.__version__, dpy_repo)
        py_version = "[{}.{}.{}]({})".format(*os.sys.version_info[:3],
                                             python_url)

        owner_set = self.bot.settings.owner is not None
        owner = self.bot.settings.owner if owner_set else None
        if owner:
            owner = discord.utils.get(self.bot.get_all_members(), id=owner)
            if not owner:
                try:
                    owner = await self.bot.get_user_info(self.bot.settings.owner)
                except:
                    owner = None
        if not owner:
            owner = "Unknown"

        about = (
            "Collector is an instance of [Red, an open source Discord bot]({}) "
            "created by [Twentysix]({}) and improved by many.\n\n"
            "The Collector Dev Team is backed by a passionate community who contributes and "
            "creates content for everyone to enjoy. [Join us today]({}) "
            "and help us improve!\n\n"
            "".format(red_repo, author_repo, server_url))
        devteam = ("[DeltaSigma#8530](https://discordapp.com/channels/@me/148622879817334784)\n[JJW#8071](https://discordapp.com/channels/@me/124984294035816448)\n[ranemartin8#1636](https://discordapp.com/channels/@me/245589956012146688)")
        artteam = ('[ViceOne#3005](https://discordapp.com/channels/@me/276111652943036416)')
        embed = discord.Embed(colour=discord.Colour.red())
        embed.add_field(name="Instance owned by", value=str(owner))
        embed.add_field(name="Python", value=py_version)
        embed.add_field(name="discord.py", value=dpy_version)
        embed.add_field(name="About Collector", value=about, inline=False)
        embed.add_field(name="The Collector Dev Team",value=devteam,inline=True)
        embed.add_field(name="The Collector Art Team",value=artteam,inline=True)
        embed.set_footer(text="Bringing joy since 02 Jan 2016 (over "
                         "{} days ago!)".format(days_since))

        try:
            await self.bot.say(embed=embed)
        except discord.HTTPException:
            await self.bot.say("I need the `Embed links` permission "
                               "to send this")

    @commands.command(help=lookup_links['event'][0], aliases=['events','schedule',])
    async def event(self):
        x = 'event'
        lookup = self.lookup_links[x]
        await self.bot.say(embed=self.present(lookup))
        await self.bot.say('iOS dumblink:\n{}'.format(lookup[0]))

    @commands.command(help=lookup_links['spotlight'][0],)
    async def spotlight(self):
        x = 'spotlight'
        lookup = self.lookup_links[x]
        await self.bot.say(embed=self.present(lookup))
        await self.bot.say('iOS dumblink:\n{}'.format(lookup[0]))

    @commands.command(help=lookup_links['rttl'][0],)
    async def rttl(self):
        x = 'rttl'
        lookup = self.lookup_links[x]
        await self.bot.say(embed=self.present(lookup))
        await self.bot.say('iOS dumblink:\n{}'.format(lookup[0]))

    @commands.command(help=lookup_links['marvelsynergy'][0])
    async def marvelsynergy(self):
        x = 'marvelsynergy'
        lookup = self.lookup_links[x]
        await self.bot.say(embed=self.present(lookup))
        await self.bot.say('iOS dumblink:\n{}'.format(lookup[0]))

    @commands.command(help=lookup_links['simulator'][0],aliases=['msim'])
    async def simulator(self):
        x = 'simulator'
        lookup = self.lookup_links[x]
        await self.bot.say(embed=self.present(lookup))
        await self.bot.say('iOS dumblink:\n{}'.format(lookup[0]))

    @commands.command(help=lookup_links['alsciende'][0], aliases=('mrig',))
    async def alsciende(self):
        x = 'alsciende'
        lookup = self.lookup_links[x]
        await self.bot.say(embed=self.present(lookup))
        await self.bot.say('iOS dumblink:\n{}'.format(lookup[0]))

    @commands.command(help=lookup_links['streak'][0])
    async def streak(self):
        x='streak'
        lookup = self.lookup_links[x]
        await self.bot.say(embed=self.present(lookup))
        await self.bot.say('iOS dumblink:\n{}'.format(lookup[0]))

    @commands.command(help=lookup_links['hook'][0])
    async def hook(self):
        x = 'hook'
        lookup = self.lookup_links[x]
        await self.bot.say(embed=self.present(lookup))
        await self.bot.say('iOS dumblink:\n{}'.format(lookup[0]))

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
