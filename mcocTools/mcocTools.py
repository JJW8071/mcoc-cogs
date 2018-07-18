import discord
import re
import csv
import random
import os
import datetime
from operator import itemgetter, attrgetter
from .utils import chat_formatting as chat
from .utils.dataIO import dataIO
from cogs.utils import checks
from discord.ext import commands
from . import hook as hook

class MCOCTools:
    '''Tools for Marvel Contest of Champions'''
    lookup_links = {
            'event': (
                '<http://simians.tk/MCOC-Sched>',
                '[Tiny MCoC Schedule](https://docs.google.com/spreadsheets/d/e/2PACX-1vT5A1MOwm3CvOGjn7fMvYaiTKDuIdvKMnH5XHRcgzi3eqLikm9SdwfkrSuilnZ1VQt8aSfAFJzZ02zM/pubhtml?gid=390226786)',
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
                '[MCOC Spotlight Dataset](http://simians.tk/MCoCspotlight)\nIf you would like to donate prestige, signatures or stats, join us at \n[CollectorDevTeam](https://discord.gg/BwhgZxk)'),
            # 'marvelsynergy': (
            #     '<http://www.marvelsynergy.com/team-builder>',
            #     '[Marvel Synergy Team Builder](http://www.marvelsynergy.com/team-builder)',
            #     'Marvel Synergy',
            #     'http://www.marvelsynergy.com/images/marvelsynergy.png'),
            'alsciende':(
                '<https://alsciende.github.io/masteries/v10.0.1/#>',
                '[Alsciende Mastery Tool](https://alsciende.github.io/masteries/v17.0.2/#)',
                'by u/alsciende',
                'https://images-ext-2.discordapp.net/external/ymdMNrkhO9L5tUDupbFSEmu-JK0X2bpV0ZE-VYTBICc/%3Fsize%3D1024/https/cdn.discordapp.com/avatars/268829380262756357/b55ae7fc51d9b741450f949accd15fbe.webp?width=80&height=80'),
            'simulator': (
                '<http://simians.tk/msimSDF>',
                '[-SDF- Mastery Simulator](http://simians.tk/msimSDF)'),
            # 'streak': (
            #     '<http://simians.tk/-sdf-streak>'
            #     '[Infinite Streak](http://simians.tk/-sdf-streak)'),
            #     #'http://simians.tk/SDFstreak')
    }
    mcolor = discord.Color.red()
    COLLECTOR_ICON='https://raw.githubusercontent.com/JasonJW/mcoc-cogs/master/mcoc/data/cdt_icon.png'
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
            em.set_footer(text='CollectorDevTeam',icon_url=self.COLLECTOR_ICON)
        return em

    @commands.command(pass_context=True,aliases={'collector','infocollector','about'})
    async def aboutcollector(self,ctx):
        """Shows info about Collector"""
        author_repo = "https://github.com/Twentysix26"
        red_repo = author_repo + "/Red-DiscordBot"
        server_url = "https://discord.gg/wJqpYGS"
        dpy_repo = "https://github.com/Rapptz/discord.py"
        python_url = "https://www.python.org/"
        collectorpatreon = 'https://patreon.com/collectorbot'
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
            "Collector is an instance of [Red, an open source Discord bot]({0}) "
            "created by [Twentysix]({1}) and improved by many.\n\n"
            "The Collector Dev Team is backed by a passionate community who contributes and "
            "creates content for everyone to enjoy. [Join us today]({2}) "
            "and help us improve!\n\n"
            "★ If you would like to support the Collector, please visit {3}.\n"
            "★ Patrons and Collaborators recieve priority support and secrety stuff.\n\n~ JJW"
            "".format(red_repo, author_repo, server_url, collectorpatreon))
        devteam = ( "DeltaSigma#8530\n"
                    "JJW#8071\n"
                    )
        supportteam=('phil_wo#3733\nSpiderSebas#9910\nsuprmatt#2753\ntaoness#5565\n')
        embed = discord.Embed(colour=discord.Colour.red(), title="Collector", url=collectorpatreon)
        embed.add_field(name="Instance owned by", value=str(owner))
        embed.add_field(name="Python", value=py_version)
        embed.add_field(name="discord.py", value=dpy_version)
        embed.add_field(name="About", value=about, inline=False)
        embed.add_field(name="PrestigePartner",value='mutamatt#4704',inline=True)
        embed.add_field(name='DuelsPartners',value='2OO2RC51#4587',inline=True)
        embed.add_field(name='MapsPartners',value='jpags#5202\nBlooregarde#5848 ',inline=True)
        embed.add_field(name='LabyrinthTeam',value='Kiryu#5755\nre-1#7595',inline=True)
        embed.add_field(name='CollectorSupportTeam', value=supportteam,inline=True)
        embed.add_field(name="CollectorDevTeam",value=devteam,inline=True)
        embed.set_footer(text="Bringing joy since 02 Jan 2016 (over "
                         "{} days ago!)".format(days_since))

        try:
            await self.bot.say(embed=embed)
        except discord.HTTPException:
            await self.bot.say("I need the `Embed links` permission "
                               "to send this")

    # @checks.admin_or_permissions(manage_server=True)
    # @commands.command()
    # async def tickets(self):
    #     ticketsjson = 'data/tickets/tickets.json'
    #     tickets = dataIO.load_json(ticketsjson)
    #     em = discord.Embed(title='Tickets')
    #     cnt = 0
    #     ids = tickets.keys()
    #
    #     for ticket in :
    #         em.add_field(name='{} - filed by {}'.format(cnt, ticket['name'],value='{}\n id: {}'.format(ticket['message'],ticket)))
    #     await self.bot.say(embed=em)


    @commands.command(help=lookup_links['event'][0], aliases=['events','schedule',])
    async def event(self):
        x = 'event'
        lookup = self.lookup_links[x]
        await self.bot.say(embed=self.present(lookup))
        # await self.bot.say('iOS dumblink:\n{}'.format(lookup[0]))

    @commands.command(help=lookup_links['spotlight'][0],)
    async def spotlight(self):
        x = 'spotlight'
        lookup = self.lookup_links[x]
        await self.bot.say(embed=self.present(lookup))
        # await self.bot.say('iOS dumblink:\n{}'.format(lookup[0]))

    @commands.command(help=lookup_links['rttl'][0],)
    async def rttl(self):
        x = 'rttl'
        lookup = self.lookup_links[x]
        await self.bot.say(embed=self.present(lookup))
        # await self.bot.say('iOS dumblink:\n{}'.format(lookup[0]))

    @commands.command(help=lookup_links['simulator'][0],aliases=['msim'])
    async def simulator(self):
        x = 'simulator'
        lookup = self.lookup_links[x]
        await self.bot.say(embed=self.present(lookup))
        # await self.bot.say('iOS dumblink:\n{}'.format(lookup[0]))

    @commands.command(help=lookup_links['alsciende'][0], aliases=('mrig',))
    async def alsciende(self):
        x = 'alsciende'
        lookup = self.lookup_links[x]
        await self.bot.say(embed=self.present(lookup))
        # await self.bot.say('iOS dumblink:\n{}'.format(lookup[0]))

    @commands.command(help=lookup_links['hook'][0])
    async def hook(self):
        x = 'hook'
        lookup = self.lookup_links[x]
        await self.bot.say(embed=self.present(lookup))
        # await self.bot.say('iOS dumblink:\n{}'.format(lookup[0]))

    # @commands.command()
    # async def keygen(self, prefix='SDCC17'):
    #     '''SDCC Code Generator
    #     No warranty :)'''
    #     letters='ABCDEFGHIJKLMNOPQURSTUVWXYZ'
    #     numbers='0123456789'
    #     package = []
    #     for i in range(0,9):
    #         lets='{}{}{}{}{}{}'.format(random.choice(letters),random.choice(letters),random.choice(numbers),random.choice(numbers),random.choice(letters),random.choice(letters))
    #         package.append(prefix+lets)
    #     em=discord.Embed(color=discord.Color.gold(),title='Email Code Generator',description='\n'.join(package))
    #     await self.bot.say(embed=em)

    def _get_text(self, mastery, rank):
        rows = csv_get_rows(self.dataset,'Mastery',mastery)
        for row in rows:
            text.append(row['Text'].format(row[str(rank)]))
        return text

    @checks.admin_or_permissions(manage_server=True, manage_roles=True)
    @commands.command(name='gaps', pass_context=True, hidden=True)
    async def _alliance_popup(self, ctx, *args):
        '''Guild | Alliance Popup System'''

        warning_msg =('The G.A.P.S. System will configure your server for basic Alliance Operations.'
                'Roles will be added for summoners, alliance, officers, bg1, bg2, bg3'
                'Channels will be added for announcements, alliance, & battlegroups.'
                'Channel permissions will be configured.'
                'After the G.A.P.S. system prepares your server, there will be additional instructions.'
                'If you consent, press OK')
        em = discord.Embed(color=ctx.message.author.color, title='G.A.P.S. Warning Message', description=warning_msg)
        message = await self.bot.say(embed=em)
        await self.bot.add_reaction(message, '❌')
        await self.bot.add_reaction(message, '🆗')
        react = await self.bot.wait_for_reaction(message=message, user=ctx.message.author, timeout=30, emoji=['❌', '🆗'])
        if react is not None:
            if react.reaction.emoji == '❌':
                await self.bot.say('G.A.P.S. canceled.')
                return
            elif react.reaction.emoji == '🆗':
                message2 = await self.bot.say('G.A.P.S. in progess.')
        else:
            await self.bot.say('Ambiguous response.  G.A.P.S. canceled')
            return

        server = ctx.message.server
        adminpermissions = discord.PermissionOverwrite(administrator=True)
        moderatorpermissions = discord.PermissionOverwrite(manage_roles=True)
        moderatorpermissions.manage_server=True
        moderatorpermissions.kick_members=True
        moderatorpermissions.ban_members=True
        moderatorpermissions.manage_channels=True
        moderatorpermissions.manage_server=True
        moderatorpermissions.manage_messages=True
        moderatorpermissions.view_audit_logs=True
        moderatorpermissions.read_messages=True
        moderatorpermissions.create_instant_invite=True

        roles = server.roles
        rolenames = []
        for r in roles:
            rolenames.append('{}'.format(r.name))
        aroles = ['officers', 'bg1', 'bg2', 'bg3', 'alliance', 'summoners']
        # message = await self.bot.say('Stage 1: Creating roles')
        if 'admin' not in rolenames:
            admin = await self.bot.create_role(server=server, name='admin', color=discord.Color.gold(), hoist=False, mentionable=False)
        if 'officers' not in rolenames:
            officers = await self.bot.create_role(server=server, name='officers', color=discord.Color.light_grey(), hoist=False, mentionable=True)
        if 'bg1' not in rolenames:
            bg1 = await self.bot.create_role(server=server, name='bg1', color=discord.Color.blue(), hoist=False, mentionable=True)
        if 'bg2' not in rolenames:
            bg2 = await self.bot.create_role(server=server, name='bg2', color=discord.Color.purple(), hoist=False, mentionable=True)
        if 'bg3' not in rolenames:
            bg3 = await self.bot.create_role(server=server, name='bg3', color=discord.Color.orange(), hoist=False, mentionable=True)
        if 'alliance' not in rolenames:
            alliance = await self.bot.create_role(server=server, name='alliance', color=discord.Color.teal(), hoist=True, mentionable=True)
        if 'summoners' not in rolenames:
            summoners = await self.bot.create_role(server=server, name='summoners', color=discord.Color.lighter_grey(), hoist=True, mentionable=True)

        roles = sorted(server.roles, key=lambda roles:roles.position, reverse=True)
        em = discord.Embed(color=discord.Color.red(), title='Guild Alliance Popup System', description='')
        positions = []
        for r in roles:
            positions.append('{} = {}'.format(r.position, r.mention))
            if r.name == 'officers':
                officers = r
            elif r.name == 'bg1':
                bg1 = r
            elif r.name == 'bg2':
                bg2 = r
            elif r.name == 'bg3':
                bg3 = r
            elif r.name == 'alliance':
                alliance = r
            elif r.name == 'summoners':
                summoners = r
            elif r.name == 'admin':
                admin = r
            elif r.name=='everyone':
                everyone = r
        em.add_field(name='Stage 1 Role Creation',value='\n'.join(positions),inline=False)
        await self.bot.say(embed=em)

        everyone_perms = discord.PermissionOverwrite(read_messages = False)
        everyoneperms = discord.ChannelPermissions(target=server.default_role, overwrite=everyone_perms)
        readperm = discord.PermissionOverwrite(read_messages = True)
        officerperms = discord.ChannelPermissions(target=officers, overwrite=readperm)
        allianceperms = discord.ChannelPermissions(target=alliance, overwrite=readperm)
        summonerperms = discord.ChannelPermissions(target=summoners, overwrite=readperm)
        bg1perms = discord.ChannelPermissions(target=bg1, overwrite=readperm)
        bg2perms = discord.ChannelPermissions(target=bg2, overwrite=readperm)
        bg3perms = discord.ChannelPermissions(target=bg3, overwrite=readperm)

        channellist = []
        for c in server.channels:
            channellist.append(c.name)
        if 'announcements' not in channellist:
            await self.bot.create_channel(server, 'announcements', everyoneperms, allianceperms, summonerperms)
        # if 'alliance' not in channellist:
        #     await self.bot.create_channel(server, 'alliance', everyoneperms, allianceperms)
        if 'alliance-chatter' not in channellist:
            await self.bot.create_channel(server, 'alliance-chatter', everyoneperms, allianceperms)
        if 'officers' not in channellist:
            await self.bot.create_channel(server, 'officers', everyoneperms, officerperms)
        if 'bg1aq' not in channellist:
            await self.bot.create_channel(server, 'bg1aq', everyoneperms, officerperms, bg1perms)
        if 'bg1aw' not in channellist:
            await self.bot.create_channel(server, 'bg1aw', everyoneperms, officerperms, bg1perms)
        if 'bg2aq' not in channellist:
            await self.bot.create_channel(server, 'bg2aq', everyoneperms, officerperms, bg2perms)
        if 'bg2aw' not in channellist:
            await self.bot.create_channel(server, 'bg2aw', everyoneperms, officerperms, bg2perms)
        if 'bg3aq' not in channellist:
            await self.bot.create_channel(server, 'bg3aq', everyoneperms, officerperms, bg3perms)
        if 'bg3aw' not in channellist:
            await self.bot.create_channel(server, 'bg3aw', everyoneperms, officerperms, bg2perms)

        channels= sorted(server.channels, key=lambda channels:channels.position, reverse=False)
        channelnames=[]
        for c in channels:
            channelnames.append('{} = {} '.format(c.position, c.mention))
        em = discord.Embed(color=discord.Color.red(), title='Guild Alliance Popup System', description='')
        em.add_field(name='Stage 2 Create Channels',value='\n'.join(channelnames),inline=False)
        await self.bot.say(embed=em)

        em = discord.Embed(color=discord.Color.red(), titel= 'Guild Alliance Popup System', descritpion='')

        # fixNotifcations = await self.bot.say('Stage 3: Attempting to set Default Notification to Direct Message Only')
        try:
            # mentions only
            await self.bot.http.request(discord.http.Route('PATCH', '/guilds/{guild_id}', guild_id=server.id), json={'default_message_notifications': 1})
            em.add_field(name='Stage 3: Notification Settings', value='I have modified the servers to use better notification settings.')
        except Exception as e:
            await self.bot.edit_message(fixNotifcations, "An exception occurred. check your log.")

        await self.bot.say(embed=em)
        em = discord.Embed(color=ctx.message.author.color, titel= 'Guild Alliance Popup System', descritpion='Server Owner Instructions')
        em.add_field(name='Enroll for Collector announcements', value='Enroll a channel for Collector announcements\n```/addchan #announcements```\n', inline=False)
        em.add_field(name='Set up Autorole', value='Default Role should be {}\n```/autorole role summoners```\n```/autorole toggle``` '.format(summoners.mention), inline=False)
        await self.bot.say(embed=em)
        await self.bot.delete_message(message2)

    # @checks.is_owner()
    # @commands.group(pass_context=True, hidden=True)
    # async def inspect(self, ctx):

    # @checks.is_owner()
    @commands.command(pass_context=True, hidden=True, name='inspectroles', aliases=['inspectrole', 'ir',])
    async def _inspect_roles(self, ctx):
        server = ctx.message.server
        roles = sorted(server.roles, key=lambda roles:roles.position, reverse=True)
        positions = []
        for r in roles:
            positions.append('{} = {}'.format(r.position, r.name))
        desc =  '\n'.join(positions)
        em = discord.Embed(color=discord.Color.red(), title='Collector Inspector: ROLES', description=desc)
        await self.bot.say(embed=em)


    @checks.admin_or_permissions(manage_roles=True)
    @commands.command(name='norole',pass_context=True,hidden=True)
    async def _no_role(self, ctx, role : discord.Role):
        members = ctx.message.server.members
        missing = []
        print(str(len(missing)))
        for member in members:
            if not member.bot:
                if role not in member.roles:
                    missing.append('{0.name} : {0.id}'.format(member))
        print(str(len(missing)))
        if len(missing) == 0:
            await self.bot.say('No users are missing the role: {}'.format(role.name))
        else:
            pages = chat.pagify('\n'.join(missing))
            for page in pages:
                await self.bot.say(chat.box(page))
    # @checks.admin_or_permissions(manage_server=True, manage_roles=True)
    # @commands.command(name='setup', pass_context=True)
    # async def collectorsetup(self,ctx,*args):
    #     '''Server Setup Guide
    #     Collector Role Requires admin
    #     '''
        # 1) Check Roles present
        # 2) Check Role Permissions
        # 3) Check Role Order
        # Manage Messages required for Cleanup
        # Manage Server required for Role Creation / Deletion
        # Manage Roles required for Role assignment / removal
        # 2 ) Check roles
        # 3 ) Check role order
        # check1 = await self.setup_phase_one(ctx)
        # if check1:
        #     await self.bot.say(embed=discord.Embed(color=discord.color.red(),
        #                         title='Collector Setup Protocol',
        #                         description='☑ setup_phase_one '))



    # async def setup_phase_one(self, ctx):
    #     '''Check Server ROLES'''
    #     # repeat_phase = await self.setup_phase_one(ctx)
    #     # next_phase = await self.setup_phase_two(ctx)
    #
    #     server = ctx.message.server
    #     roles = server.roles
    #     rolenames = []
    #     phase = True
    #     for r in roles:
    #         rolenames.append(r.name)
    #     required_roles={'Collector','officers','bg1','bg2','bg3','LEGEND','100%LOL','LOL','RTL','ROL','100%Act4','Summoner','TestRole1','TestRole2'}
    #     roles_fields={'officers': {True, discord.Color.lighter_grey(),},
    #                 'bg1':{True, discord.Color.blue(), },
    #                 'bg2':{True, discord.Color.purple(), },
    #                 'bg3':{True, discord.Color.orange(), },
    #                 'TestRole1':{True, discord.Color.default(), },
    #                 'TestRole2':{True, discord.Color.light_grey()},
    #                 }
    #     stageone=['Setup Conditions 1:\nRoles Required for Guild Setup:',]
    #     for i in required_roles:
    #         if i in rolenames:
    #             stageone.append('☑️ {}'.format(i))
    #         else:
    #             stageone.append('❌ {}'.format(i))
    #             phase = False
    #     desc = '\n'.join(stageone)
    #     if phase == False:
    #         em=discord.Embed(color=discord.Color.red(),title='Server Setup Protocol [1]',description=desc)
    #         em.add_field(name='Corrective Action', value='Roles are missing. Create missing roles and Rerun test.\n🔁 == Rerun test\n❌ == Cancel setup')
    #         message = await self.bot.send_message(ctx.message.channel, embed=em)
    #         await self.bot.add_reaction(message,'\N{ANTICLOCKWISE DOWNWARDS AND UPWARDS OPEN CIRCLE ARROWS}')
    #         await self.bot.add_reaction(message,'\N{CROSS MARK}')
    #         await self.bot.add_reaction(message, '\N{BLACK RIGHT-POINTING TRIANGLE}')
    #         react = await self.bot.wait_for_reaction(message=message, user=ctx.message.author, timeout=120, emoji=['\N{CROSS MARK}','\N{ANTICLOCKWISE DOWNWARDS AND UPWARDS OPEN CIRCLE ARROWS}','\N{BLACK RIGHT-POINTING TRIANGLE}'])
    #         if react is None or react.reaction.emoji == '\N{CROSS MARK}':
    #             try:
    #                 await self.bot.delete_message(message)
    #             except:
    #                 pass
    #             return None
    #         elif react.reaction.emoji == '\N{ANTICLOCKWISE DOWNWARDS AND UPWARDS OPEN CIRCLE ARROWS}':
    #             await self.bot.delete_message(message)
    #             return await self.setup_phase_one(ctx)
    #         elif react.reaction.emoji == '\N{BLACK RIGHT-POINTING TRIANGLE}':
    #             await self.bot.delete_message(message)
    #             return await self.setup_phase_two(ctx)
    #     elif phase == True:
    #         await setup_phase_two
    #
    # async def setup_phase_two(self, ctx):
    #     '''Check Role ORDER'''
    #     server = ctx.message.server
    #     roles = sorted(server.roles, key=lambda roles:roles.position, reverse=True)
    #     required_roles = ('Collector','officers','bg1','bg2','bg3','LEGEND','100%LOL','LOL','RTL','ROL','100%Act4','Summoner', 'everyone')
    #     said = []
    #     em = discord.Embed(color=discord.Color.red(), title='Role Order Prerequisite',description='Role: Collector')
    #     positions = []
    #     for r in roles:
    #         positions.append('{} = {}'.format(r.position, r.name))
    #     em.add_field(name='Role Position on Server',value=chat.box('\n'.join(positions)),inline=False)
    #     said.append(await self.bot.say(embed=em))
    #     order = []
    #     c=len(required_roles)-1
    #     for r in required_roles:
    #         order.append('{} = {}'.format(c, r))
    #         c-=1
    #     em = discord.Embed(color=discord.Color.red(), title='',description='')
    #     em.add_field(name='Correct Role Positions', value =chat.box('\n'.join(order)),inline=False)
    #     perm_order = []
    #     phase = True
    #     for i in range(0,len(required_roles)-2):
    #         j = i+1
    #         if required_roles[j] > required_roles[i]:
    #             phase = False
    #             # perm_order.append('{} should be above {}'.format(required_roles[i],required_roles[j]))
    #     if phase == False:
    #         # em=discord.Embed(color=discord.Color.red(),title='Server Setup Protocol [2]',description=desc)
    #         em.add_field(name='Corrective Action', value='Roles are out of order. Adjust role order and Rerun test.')
    #         # em.add_field(name='',value='\n'.join(perm_order))
    #         message = await self.bot.send_message(ctx.message.channel, embed=em)
    #         said.append(message)
    #         await self.bot.add_reaction(message,'\N{BLACK LEFT-POINTING TRIANGLE}')
    #         await self.bot.add_reaction(message,'\N{ANTICLOCKWISE DOWNWARDS AND UPWARDS OPEN CIRCLE ARROWS}')
    #         await self.bot.add_reaction(message,'\N{CROSS MARK}')
    #         await self.bot.add_reaction(message, '\N{BLACK RIGHT-POINTING TRIANGLE}')
    #         react = await self.bot.wait_for_reaction(message=message, user=ctx.message.author, timeout=120, emoji=['\N{CROSS MARK}','\N{ANTICLOCKWISE DOWNWARDS AND UPWARDS OPEN CIRCLE ARROWS}','\N{BLACK RIGHT-POINTING TRIANGLE}'])
    #         if react is None or react.reaction.emoji == '\N{CROSS MARK}':
    #             try:
    #                 for message in said:
    #                     await self.bot.delete_message(message)
    #             except:
    #                 pass
    #             return None
    #         elif react.reaction.emoji == '\N{ANTICLOCKWISE DOWNWARDS AND UPWARDS OPEN CIRCLE ARROWS}':
    #             for message in said:
    #                 await self.bot.delete_message(message)
    #             return await self.setup_phase_two(ctx)
    #         elif react.reaction.emoji == '\N{BLACK RIGHT-POINTING TRIANGLE}':
    #             for message in said:
    #                 await self.bot.delete_message(message)
    #             return await self.setup_phase_three(ctx)
    #         elif react.reaction.emoji == '\N{BLACK LEFT-POINTING TRIANGLE}':
    #             for message in said:
    #                 await self.bot.delete_message(message)
    #             return await self.setup_phase_one(ctx)
    #     elif phase == True:
    #         await setup_phase_three
    #
    # async def setup_phase_three(self, ctx):
    #     '''Check Role Permissions'''
    #     message = await self.bot.say('initiate phase three')

    @commands.command(pass_context=True, hidden=True)
    async def awopp_calc(self, ctx, wr:int, gain:int, loss:int):
        '''MutaMatt's War Opponent Calculator
        https://en.wikipedia.org/wiki/Elo_rating_system
        '''
        playera = 1/(1+exp(10,(gain-loss)/400))
        await self.bot.say('{}'.format(playera))

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
