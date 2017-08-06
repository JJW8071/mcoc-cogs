import discord
import re
import csv
import random
import os
import datetime
from operator import itemgetter, attrgetter
from .utils import chat_formatting as chat
from cogs.utils import checks
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
                '<http://www.marvelsynergy.com/team-builder>',
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
                '<http://simians.tk/-sdf-streak>'
                '[Infinite Streak](http://simians.tk/-sdf-streak)'),
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
        devteam = ( "[DeltaSigma#8530](https://discordapp.com/channels/@me/148622879817334784)"
                    "[JJW#8071](https://discordapp.com/channels/@me/124984294035816448)"
                    "[ranemartin8#1636](https://discordapp.com/channels/@me/245589956012146688)")
        artteam = ('[ViceOne#3005](https://discordapp.com/channels/@me/276111652943036416)')
        supportteam=('[phil_wo#3733](https://discordapp.com/channels/@me/202502240072761356)'
                    '[SpiderSebas](https://discordapp.com/channels/@me/159707467834589184)'
                    '[The Living Tribunal](https://discordapp.com/channels/@me/268418759868284928'
                    )
        bughunters = ('[SpiderSebas]')
        embed = discord.Embed(colour=discord.Colour.red())
        embed.add_field(name="Instance owned by", value=str(owner))
        embed.add_field(name="Python", value=py_version)
        embed.add_field(name="discord.py", value=dpy_version)
        embed.add_field(name="About Collector", value=about, inline=False)
        embed.add_field(name="CollectorDevTeam",value=devteam,inline=True)
        embed.add_field(name='CollectorSupportTeam', value=supportteam,inline=True)
        embed.add_field(name="CollectorArtTeam",value=artteam,inline=True)
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
    async def keygen(self, prefix='SDCC17'):
        '''SDCC Code Generator
        No warranty :)'''
        letters='ABCDEFGHIJKLMNOPQURSTUVWXYZ'
        numbers='0123456789'
        package = []
        for i in range(0,9):
            lets='{}{}{}{}{}{}'.format(random.choice(letters),random.choice(letters),random.choice(numbers),random.choice(numbers),random.choice(letters),random.choice(letters))
            package.append(prefix+lets)
        em=discord.Embed(color=discord.Color.gold(),title='Email Code Generator',description='\n'.join(package))
        await self.bot.say(embed=em)

    def _get_text(self, mastery, rank):
        rows = csv_get_rows(self.dataset,'Mastery',mastery)
        for row in rows:
            text.append(row['Text'].format(row[str(rank)]))
        return text

    @checks.admin_or_permissions(manage_server=True, manage_roles=True)
    @commands.command(name='setup', pass_context=True)
    async def collectorsetup(self,ctx,*args):
        '''Server Setup Guide
        Collector Role Requires admin
        '''
        # 1) Check Roles present
        # 2) Check Role Permissions
        # 3) Check Role Order
        # Manage Messages required for Cleanup
        # Manage Server required for Role Creation / Deletion
        # Manage Roles required for Role assignment / removal
        # 2 ) Check roles
        # 3 ) Check role order
        check1 = await self.setup_phase_one(ctx)
        if check1:
            await self.bot.say(embed=discord.Embed(color=discord.color.red(),
                                title='Collector Setup Protocol',
                                description='☑ setup_phase_one '))



    async def setup_phase_one(self, ctx):
        '''Check Server ROLES'''
        # repeat_phase = await self.setup_phase_one(ctx)
        # next_phase = await self.setup_phase_two(ctx)

        server = ctx.message.server
        roles = server.roles
        rolenames = []
        phase = True
        for r in roles:
            rolenames.append(r.name)
        required_roles={'Collector','officers','bg1','bg2','bg3','LEGEND','100%LOL','LOL','RTL','ROL','100%Act4','Summoner','TestRole1','TestRole2'}
        roles_fields={'officers': {True, discord.Color.lighter_grey(),},
                    'bg1':{True, discord.Color.blue(), },
                    'bg2':{True, discord.Color.purple(), },
                    'bg3':{True, discord.Color.orange(), },
                    'TestRole1':{True, discord.Color.default(), },
                    'TestRole2':{True, discord.Color.light_grey()},
                    }
        stageone=['Setup Conditions 1:\nRoles Required for Guild Setup:',]
        for i in required_roles:
            if i in rolenames:
                stageone.append('☑️ {}'.format(i))
            else:
                stageone.append('❌ {}'.format(i))
                phase = False
        desc = '\n'.join(stageone)
        if phase == False:
            em=discord.Embed(color=discord.Color.red(),title='Server Setup Protocol [1]',description=desc)
            em.add_field(name='Corrective Action', value='Roles are missing. Create missing roles and Rerun test.\n🔁 == Rerun test\n❌ == Cancel setup')
            message = await self.bot.send_message(ctx.message.channel, embed=em)
            await self.bot.add_reaction(message,'\N{ANTICLOCKWISE DOWNWARDS AND UPWARDS OPEN CIRCLE ARROWS}')
            await self.bot.add_reaction(message,'\N{CROSS MARK}')
            await self.bot.add_reaction(message, '\N{BLACK RIGHT-POINTING TRIANGLE}')
            react = await self.bot.wait_for_reaction(message=message, user=ctx.message.author, timeout=120, emoji=['\N{CROSS MARK}','\N{ANTICLOCKWISE DOWNWARDS AND UPWARDS OPEN CIRCLE ARROWS}','\N{BLACK RIGHT-POINTING TRIANGLE}'])
            if react is None or react.reaction.emoji == '\N{CROSS MARK}':
                try:
                    await self.bot.delete_message(message)
                except:
                    pass
                return None
            elif react.reaction.emoji == '\N{ANTICLOCKWISE DOWNWARDS AND UPWARDS OPEN CIRCLE ARROWS}':
                await self.bot.delete_message(message)
                return await self.setup_phase_one(ctx)
            elif react.reaction.emoji == '\N{BLACK RIGHT-POINTING TRIANGLE}':
                await self.bot.delete_message(message)
                return await self.setup_phase_two(ctx)
        elif phase == True:
            await setup_phase_two

    async def setup_phase_two(self, ctx):
        '''Check Role ORDER'''
        server = ctx.message.server
        roles = sorted(server.roles, key=lambda roles:roles.position, reverse=True)
        required_roles = ('Collector','officers','bg1','bg2','bg3','LEGEND','100%LOL','LOL','RTL','ROL','100%Act4','Summoner', 'everyone')
        said = []
        em = discord.Embed(color=discord.Color.red(), title='Role Order Prerequisite',description='Role: Collector')
        positions = []
        for r in roles:
            positions.append('{} = {}'.format(r.position, r.name))
        em.add_field(name='Role Position on Server',value=chat.box('\n'.join(positions)),inline=False)
        said.append(await self.bot.say(embed=em))
        order = []
        c=len(required_roles)-1
        for r in required_roles:
            order.append('{} = {}'.format(c, r))
            c-=1
        em = discord.Embed(color=discord.Color.red(), title='',description='')
        em.add_field(name='Correct Role Positions', value =chat.box('\n'.join(order)),inline=False)
        perm_order = []
        phase = True
        for i in range(0,len(required_roles)-2):
            j = i+1
            if required_roles[j] > required_roles[i]:
                phase = False
                # perm_order.append('{} should be above {}'.format(required_roles[i],required_roles[j]))
        if phase == False:
            # em=discord.Embed(color=discord.Color.red(),title='Server Setup Protocol [2]',description=desc)
            em.add_field(name='Corrective Action', value='Roles are out of order. Adjust role order and Rerun test.')
            # em.add_field(name='',value='\n'.join(perm_order))
            message = await self.bot.send_message(ctx.message.channel, embed=em)
            said.append(message)
            await self.bot.add_reaction(message,'\N{BLACK LEFT-POINTING TRIANGLE}')
            await self.bot.add_reaction(message,'\N{ANTICLOCKWISE DOWNWARDS AND UPWARDS OPEN CIRCLE ARROWS}')
            await self.bot.add_reaction(message,'\N{CROSS MARK}')
            await self.bot.add_reaction(message, '\N{BLACK RIGHT-POINTING TRIANGLE}')
            react = await self.bot.wait_for_reaction(message=message, user=ctx.message.author, timeout=120, emoji=['\N{CROSS MARK}','\N{ANTICLOCKWISE DOWNWARDS AND UPWARDS OPEN CIRCLE ARROWS}','\N{BLACK RIGHT-POINTING TRIANGLE}'])
            if react is None or react.reaction.emoji == '\N{CROSS MARK}':
                try:
                    for message in said:
                        await self.bot.delete_message(message)
                except:
                    pass
                return None
            elif react.reaction.emoji == '\N{ANTICLOCKWISE DOWNWARDS AND UPWARDS OPEN CIRCLE ARROWS}':
                for message in said:
                    await self.bot.delete_message(message)
                return await self.setup_phase_two(ctx)
            elif react.reaction.emoji == '\N{BLACK RIGHT-POINTING TRIANGLE}':
                for message in said:
                    await self.bot.delete_message(message)
                return await self.setup_phase_three(ctx)
            elif react.reaction.emoji == '\N{BLACK LEFT-POINTING TRIANGLE}':
                for message in said:
                    await self.bot.delete_message(message)
                return await self.setup_phase_one(ctx)
        elif phase == True:
            await setup_phase_three

    async def setup_phase_three(self, ctx):
        '''Check Role Permissions'''
        message = await self.bot.say('initiate phase three')


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
