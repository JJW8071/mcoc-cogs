import discord
import re
import csv
import random
import logging
import os
import datetime
import json
import asyncio
import aiohttp
from collections import ChainMap, namedtuple, OrderedDict
from .utils import chat_formatting as chat
from .utils.dataIO import dataIO
from cogs.utils import checks
from discord.ext import commands
#from . import hook as hook

logger = logging.getLogger('red.mcoc.tools')
logger.setLevel(logging.INFO)

COLLECTOR_ICON='https://raw.githubusercontent.com/CollectorDevTeam/assets/master/data/cdt_icon.png'
KABAM_ICON='https://imgur.com/UniRf5f.png'
GSX2JSON='http://gsx2json.com/api?id={}&sheet={}&columns=false&integers=false'

class StaticGameData:
    instance = None

    remote_data_basepath = "https://raw.githubusercontent.com/CollectorDevTeam/assets/master/data/"
    cdt_data, cdt_versions, cdt_masteries = None, None, None
    cdt_trials = None
    test = 2

    def __new__(cls):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    async def ainit(self):
        if self.cdt_data is None:
            await self.load_cdt_data()
        if self.cdt_trials is None:
            await self.fetch_gsx2json('1TSmQOTXz0-jIVgyuFRoaPCUZA73t02INTYoXNgrI5y4')
        return self

    async def load_cdt_data(self):
        cdt_data, cdt_versions = ChainMap(), ChainMap()
        files = (
            'https://raw.githubusercontent.com/CollectorDevTeam/assets/master/data/json/snapshots/en/bcg_en.json',
            'https://raw.githubusercontent.com/CollectorDevTeam/assets/master/data/json/snapshots/en/bcg_stat_en.json',
            'https://raw.githubusercontent.com/CollectorDevTeam/assets/master/data/json/snapshots/en/special_attacks_en.json',
            'https://raw.githubusercontent.com/CollectorDevTeam/assets/master/data/json/snapshots/en/masteries_en.json',
            'https://raw.githubusercontent.com/CollectorDevTeam/assets/master/data/json/snapshots/en/character_bios_en.json',
            'https://raw.githubusercontent.com/CollectorDevTeam/assets/master/data/json/snapshots/en/dungeons_en.json'
        )
        async with aiohttp.ClientSession() as session:
            for url in files:
                raw_data = await self.fetch_json(url, session)
                val, ver = {}, {}
                for dlist in raw_data['strings']:
                    val[dlist['k']] = dlist['v']
                    if 'vn' in dlist:
                        ver[dlist['k']] = dlist['vn']
                cdt_data.maps.append(val)
                cdt_versions.maps.append(ver)
            self.cdt_data = cdt_data
            self.cdt_versions = cdt_versions

            self.cdt_masteries = await self.fetch_json(
                    self.remote_data_basepath + 'json/masteries.json',
                    session )

    @staticmethod
    async def fetch_json(url, session):
        async with session.get(url) as response:
            raw_data = json.loads(await response.text())
        logger.info("Fetching " + url)
        return raw_data

    @staticmethod
    async def fetch_gsx2json(sheet_id, sheet_number = 1, query: str = ''):
        url = GSX2JSON.format(sheet_id, sheet_number)
        if query != '':
            url=url+'&q'+query
        async with aiohttp.ClientSession() as session:
            temp = await self.fetch_json(url, session)
            package = tmp['rows'][0]
            return package


class PagesMenu:

    EmojiReact = namedtuple('EmojiReact', 'emoji include page_inc')

    def __init__(self, bot, *, add_pageof=True, timeout=30, choice=False,
            delete_onX=True):
        self.bot = bot
        self.timeout = timeout
        self.add_pageof = add_pageof
        self.choice = choice
        self.delete_onX = delete_onX
        self.embedded = True

    async def menu_start(self, pages, page_number=0):
        page_list = []
        if isinstance(pages, list):
            page_list = pages
        else:
            for page in pages:
                page_list.append(page)
        page_length = len(page_list)
        if page_length == 1:
            if isinstance(page_list[0], discord.Embed) == True:
                message = await self.bot.say(embed=page_list[0])
            else:
                message = await self.bot.say(page_list[0])
            return
        self.embedded = isinstance(page_list[0], discord.Embed)
        self.all_emojis = OrderedDict([(i.emoji, i) for i in (
            self.EmojiReact("\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}", page_length > 5, -5),
            self.EmojiReact("\N{BLACK LEFT-POINTING TRIANGLE}", True, -1),
            self.EmojiReact("\N{CROSS MARK}", True, None),
            self.EmojiReact("\N{BLACK RIGHT-POINTING TRIANGLE}", True, 1),
            self.EmojiReact("\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}", page_length > 5, 5),
                      )])

        print('menu_pages is embedded: '+str(self.embedded))

        if self.add_pageof:
            for i, page in enumerate(page_list):
                if isinstance(page, discord.Embed):
                    ftr = page.footer
                    page.set_footer(text='{} (Page {} of {})'.format(ftr.text,
                            i+1, page_length), icon_url=ftr.icon_url)
                else:
                    page += '\n(Page {} of {})'.format(i+1, page_length)

        self.page_list = page_list
        await self.display_page(None, page_number)

    async def display_page(self, message, page):
        if not message:
            if isinstance(self.page_list[page], discord.Embed) == True:
                message = await self.bot.say(embed=self.page_list[page])
            else:
                message = await self.bot.say(self.page_list[page])
            self.included_emojis = set()
            for emoji in self.all_emojis.values():
                if emoji.include:
                    await self.bot.add_reaction(message, emoji.emoji)
                    self.included_emojis.add(emoji.emoji)
        else:
            if self.embedded == True:
                message = await self.bot.edit_message(message, embed=self.page_list[page])
            else:
                message = await self.bot.edit_message(message, self.page_list[page])
        await asyncio.sleep(1)

        react = await self.bot.wait_for_reaction(message=message,
                timeout=self.timeout, emoji=self.included_emojis)
        if react is None:
            try:
                await self.bot.clear_reactions(message)
            except discord.Forbidden:
                logger.warn("clear_reactions didn't work")
                for emoji in self.included_emojis:
                    await self.bot.remove_reaction(message, emoji, self.bot.user)
            return None

        emoji = react.reaction.emoji
        pages_to_inc = self.all_emojis[emoji].page_inc if emoji in self.all_emojis else None
        if pages_to_inc:
            next_page = (page + pages_to_inc) % len(self.page_list)
            try:
                await self.bot.remove_reaction(message, emoji, react.user)
                await self.display_page(message=message, page=next_page)
            except discord.Forbidden:
                await self.bot.delete_message(message)
                await self.display_page(message=None, page=next_page)
        elif emoji == '\N{CROSS MARK}':
            try:
                if self.delete_onX:
                    await self.bot.delete_message(message)
                else:
                    await self.bot.clear_reactions(message)
            except discord.Forbidden:
                await self.bot.say("Bot does not have the proper Permissions")

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
        supportteam=('phil_wo#3733\nSpiderSebas#9910\nsuprmatt#2753\ntaoness#5565\nOtriux#9964')
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

    @commands.command(hidden=True, pass_context=True, name='datamine', aliases=('dm', 'search'))
    async def kabam_search(self, ctx, *, term: str):
        '''Enter a search term or a JSON key'''
        kdata = StaticGameData()
        cdt_data, cdt_versions = kdata.cdt_data, kdata.cdt_versions
        ksearchlist = []
        is_number = term.replace('.', '').isdigit()
        if is_number:
            for k,v in cdt_versions.items():
                if term == v:
                    ksearchlist.append('\n**{}**\n{}\nvn: {}'.format(k,
                            self._bcg_recompile(cdt_data[k]), v))
        elif term.upper() in cdt_data:
            term = term.upper()
            if term in cdt_versions:
                ver = '\nvn: {}'.format(cdt_versions[term])
            else:
                ver = ''
            em = discord.Embed(title='Data Search',
                    description='\n**{}**\n{}{}'.format(term,
                            self._bcg_recompile(cdt_data[term]),
                            ver)
                )
            # em.set_thumbnail(url=COLLECTOR_ICON)
            em.set_footer(text='MCOC Game Files', icon_url=KABAM_ICON)
            ## term is a specific JSON key
            # await self.bot.say('\n**{}**\n{}'.format(term, self._bcg_recompile(cdt_data[term])))
            await self.bot.say(embed=em)
            return
        else:
            ## search for term in json
            for k,v in cdt_data.items():
                if term.lower() in v.lower():
                    if k in cdt_versions:
                        ver = '\nvn: {}'.format(cdt_versions[k])
                    else:
                        ver = ''
                    ksearchlist.append('\n**{}**\n{}{}'.format(k,
                            self._bcg_recompile(v), ver)
                    )
        if len(ksearchlist) > 0:
            pages = chat.pagify('\n'.join(s for s in ksearchlist))
            page_list = []
            for page in pages:
                em = discord.Embed(title='Data Search',  description = page)
                # em.set_thumbnail(url=COLLECTOR_ICON)
                em.set_footer(text='MCOC Game Files', icon_url=KABAM_ICON)
                page_list.append(em)
                # page_list.append(page)
            menu = PagesMenu(self.bot, timeout=120, delete_onX=True, add_pageof=True)
            await menu.menu_start(page_list)

    def _bcg_recompile(self, str_data):
        hex_re = re.compile(r'\[[0-9a-f]{6,8}\](.+?)\[-\]', re.I)
        return hex_re.sub(r'\1', str_data)

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

    @commands.command(pass_context=True, hidden=True)
    async def awopp_calc(self, ctx, wr:int, gain:int, loss:int):
        '''MutaMatt's War Opponent Calculator
        https://en.wikipedia.org/wiki/Elo_rating_system
        '''
        playera = 1/(1+exp(10,(gain-loss)/400))
        await self.bot.say('{}'.format(playera))

    # @commands.command(pass_context=True, hiddent=True)
    # async def trials(self, ctx, trial, tier='epic'):
        



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
    sgd = StaticGameData()
    bot.loop.create_task(sgd.load_cdt_data())
    bot.add_cog(MCOCTools(bot))
