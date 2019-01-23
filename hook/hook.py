import discord
from discord.ext import commands
from .mcoc import (class_color_codes, ChampConverter, ChampConverterMult,
                  QuietUserError, override_error_handler)
from .utils.dataIO import dataIO
from .utils.dataIO import fileIO
from .utils import checks
from .utils import chat_formatting as chat
from operator import itemgetter, attrgetter
from collections import OrderedDict, namedtuple
from random import randint
from math import ceil
import shutil
import time
import types
import logging
import os
import ast
import csv
import aiohttp
import re
import asyncio
### Monkey Patch of JSONEncoder
from json import JSONEncoder, dump, dumps

logger = logging.getLogger('red.roster')
logger.setLevel(logging.INFO)

def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)

PRESTIGE_SURVEY='https://docs.google.com/forms/d/e/1FAIpQLSeo3YhZ70PQ4t_I4i14jX292CfBM8DMb5Kn2API7O8NAsVpRw/viewform?usp=sf_link'
GITHUB_ICON='http://www.smallbutdigital.com/static/media/twitter.png'
HOOK_URL='http://hook.github.io/champions/#/roster'
COLLECTOR_ICON='https://raw.githubusercontent.com/CollectorDevTeam/assets/master/data/portraits/portrait_collector.png'
GSHEET_ICON='https://d2jixqqjqj5d23.cloudfront.net/assets/developer/imgs/icons/google-spreadsheet-icon.png'

_default.default = JSONEncoder().default  # Save unmodified default.
JSONEncoder.default = _default # replacemente
### Done with patch
#class CustomEncoder(JSONEncoder):
#    def default(self, obj):
#        return getattr(obj.__class__, "to_json", JSONEncoder.default)(obj)

class MissingRosterError(QuietUserError):
    pass

class MisorderedArgumentError(QuietUserError):
    pass

class HashtagRosterConverter(commands.Converter):
    async def convert(self):
        tags = set()
        user = None
        for arg in self.argument.split():
            if arg.startswith('#'):
                tags.add(arg.lower())
            elif user is None:
                user = commands.UserConverter(self.ctx, arg).convert()
            else:
                err_msg = "There can only be 1 user argument.  All others should be '#'"
                await self.ctx.bot.say(err_msg)
                raise commands.BadArgument(err_msg)
        if user is None:
            user = self.ctx.message.author
        chmp_rstr = ChampionRoster(self.ctx.bot, user)
        await chmp_rstr.load_champions()
        if not chmp_rstr:
            menu = PagesMenu(self.ctx.bot, timeout=120, delete_onX=True, add_pageof=True)
            hook = Hook(self, self.ctx.bot)
            try:
                color=user.color
            except:
                color = discord.Color.gold()
            embeds = await hook.roster_kickback(color)
            await menu.pages_menu(page_list=embeds)



            # try:
            #     embeds = await Hook.roster_kickback(self.ctx, user.color)
            #     await Hook.pages_menu(self.ctx.bot, self.ctx, embeds)
            # except:

            # await self.ctx.bot.say('No roster detected.  \nUse ``/profile`` for import instructions.')

            # em = discord.Embed(color=discord.Color.green(),title='[????] {}'.format(user.name))
            # em.add_field(name='Missing Roster',
            #         value='Load up a "champ*.csv" file from Hook to import your roster')
            # em.add_field(name='Hook Web App', value=HOOK_URL)
            # em.set_footer(text='hook/champions for Collector',icon_url=GITHUB_ICON)
            # await self.ctx.bot.say(embed=em)
            raise MissingRosterError('No Roster found for {}'.format(user.name))
        return types.SimpleNamespace(tags=tags, roster=chmp_rstr)

class HashtagRankConverter(commands.Converter):
    parse_re = ChampConverter.parse_re
    async def convert(self):
        tags = set()
        attrs = {}
        arguments = self.argument.split()
        start_hashtags = 0
        for i, arg in enumerate(arguments):
            if arg[0] in '#(~':
                start_hashtags = i
                break
            for m in self.parse_re.finditer(arg):
                attrs[m.lastgroup] = int(m.group(m.lastgroup))
        else:
            start_hashtags = len(arguments)
        for arg in arguments[start_hashtags:]:
            if arg[0] not in '#(~':
                await self.ctx.bot.say('All arguments must be before the Hashtags')
                raise MisorderedArgumentError(arg)
            if arg.startswith('#'):
                tags.add(arg.lower())
        return types.SimpleNamespace(tags=tags, attrs=attrs)


class RosterUserConverter(commands.Converter):
    async def convert(self):
        user = None
        if self.argument:
            user = commands.UserConverter(self.ctx, self.argument).convert()
        else:
            user = self.ctx.message.author
        chmp_rstr = ChampionRoster(self.ctx.bot, user)
        await chmp_rstr.load_champions()
        return chmp_rstr

class RosterConverter(commands.Converter):
    async def convert(self):
        chmp_rstr = ChampionRoster(self.ctx.bot, self.ctx.message.author)
        await chmp_rstr.load_champions()
        return chmp_rstr


class PagesMenu:

    EmojiReact = namedtuple('EmojiReact', 'emoji include page_inc')

    def __init__(self, bot, *, add_pageof=True, timeout=30, choice=False,
            delete_onX=True):
        self.bot = bot
        self.timeout = timeout
        self.add_pageof = add_pageof
        self.choice = choice
        self.delete_onX = delete_onX

    async def menu_start(self, page_list):
        page_length = len(page_list)
        self.all_emojis = OrderedDict([(i.emoji, i) for i in (
            self.EmojiReact("\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}", page_length > 5, -5),
            self.EmojiReact("\N{BLACK LEFT-POINTING TRIANGLE}", True, -1),
            self.EmojiReact("\N{CROSS MARK}", True, None),
            self.EmojiReact("\N{BLACK RIGHT-POINTING TRIANGLE}", True, 1),
            self.EmojiReact("\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}", page_length > 5, 5),
                      )])

        self.is_embeds = isinstance(page_list[0], discord.Embed)
        if not self.is_embeds:
            await self.bot.say('Function does not support non-embeds currently')
            return

        if self.add_pageof:
            for i, page in enumerate(page_list):
                if self.is_embeds:
                    ftr = page.footer
                    page.set_footer(text='{} (Page {} of {})'.format(ftr.text,
                            i+1, page_length), icon_url=ftr.icon_url)
                else:
                    page += '\n(Page {} of {})'.format(i+1, page_length)

        self.page_list = page_list
        await self.display_page(None, 0)

    async def display_page(self, message, page):
        if not message:
            message = await self.bot.say(embed=self.page_list[page])
            self.included_emojis = set()
            for emoji in self.all_emojis.values():
                if emoji.include:
                    await self.bot.add_reaction(message, emoji.emoji)
                    self.included_emojis.add(emoji.emoji)
        else:
            message = await self.bot.edit_message(message, embed=self.page_list[page])
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


class ChampionRoster:

    _data_dir = 'data/hook/users/{}/'
    _champs_file = _data_dir + 'champs.json'
    #champ_str = '{0.star}{0.star_char} {0.full_name} r{0.rank} s{0.sig:<2} [ {0.prestige} ]'
    attr_map = {'Rank': 'rank', 'Awakened': 'sig', 'Stars': 'star', 'Role': 'quest_role'}
    alliance_map = {'alliance-war-defense': 'awd',
                    'alliance-war-attack': 'awo',
                    'alliance-quest': 'aq'}
    update_str = '{0.star_name_str} {1} -> {0.rank_sig_str} [ {0.prestige} ]'

    def __init__(self, bot, user):
        self.bot = bot
        self.user = user
        self.roster = {}
        self._create_user()
        self._cache = {}
        #self.load_champions()

    def __len__(self):
        return len(self.roster)

    def __contains__(self, item):
        if hasattr(item, 'immutable_id'):
            return item.immutable_id in self.roster
        return item in self.roster


    # handles user creation, adding new server, blocking
    def _create_user(self):
        if not os.path.exists(self.champs_file):
            if not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir)
            champ_data = {
                #"clan": None,
                #"battlegroup": None,
                "fieldnames": ["Id", "Stars", "Rank", "Level", "Awakened", "Pi", "Role"],
                "roster": [],
                "prestige": 0,
                "top5": [],
                "aq": [],
                "awd": [],
                "awo": [],
                "max5": [],
            }
            dataIO.save_json(self.champs_file, champ_data)
            #self.save_champ_data(champ_data)

    async def load_champions(self):
        data = self.load_champ_data()
        self.roster = {}
        name = 'roster' if 'roster' in data else 'champs'
        for k in data[name]:
            champ = await self.get_champion(k)
            self.roster[champ.immutable_id] = champ

    def from_list(self, champ_list):
        self.roster = {champ.immutable_id: champ for champ in champ_list}

    def load_champ_data(self):
        data = dataIO.load_json(self.champs_file)
        self.fieldnames = data['fieldnames']
        return data

    def save_champ_data(self):
        #print(dumps(self, cls=CustomEncoder))
        #with open(self.champs_file.format(self.user.id), 'w') as fp:
            #dump(self, fp, indent=2, cls=CustomEncoder)
        dataIO.save_json(self.champs_file, self)

    def to_json(self):
        translate = ['fieldnames', 'prestige', 'max_prestige', 'top5',
                     'max5']
        pack = {i: getattr(self, i) for i in translate}
        pack['roster'] = list(self.roster.values())
        return pack
        #return {i: getattr(self, i) for i in translate}

    @property
    def data_dir(self):
        return self._data_dir.format(self.user.id)

    @property
    def champs_file(self):
        return self._champs_file.format(self.user.id)

    @property
    def embed_display(self):
        return getattr(self, 'display_override', self.prestige)

    async def get_champion(self, cdict):
        mcoc = self.bot.get_cog('MCOC')
        champ_attr = {v: cdict[k] for k,v in self.attr_map.items()}
        return await mcoc.get_champion(cdict['Id'], champ_attr)

    async def filter_champs(self, tags):
        residual_tags = tags - self.all_tags
        if residual_tags:
            em = discord.Embed(title='Unused tags', description=' '.join(residual_tags))
            await self.bot.say(embed=em)
        filtered = set()
        for c in self.roster.values():
            if tags.issubset(c.all_tags):
                filtered.add(c.immutable_id)
        return [self.roster[iid] for iid in filtered]

    @property
    def all_tags(self):
        if not self.roster:
            return set()
        return set.union(*[c.all_tags for c in self.roster.values()])

    @property
    def prestige(self):
        return self._get_five('prestige')[0]

    @property
    def top5(self):
        return self._get_five('prestige')[1]

    @property
    def max_prestige(self):
        return self._get_five('max_prestige')[0]

    @property
    def max5(self):
        return self._get_five('max_prestige')[1]

    def _get_five(self, key):
        if self._cache.get(key, None) is None:
            champs = sorted(self.roster.values(), key=attrgetter(key),
                        reverse=True)
            prestige = sum([getattr(champ, key) for champ in champs[:5]])/5
            champs_str = [champ.verbose_prestige_str for champ in champs[:5]]
            self._cache[key] = (prestige, champs_str)
        return self._cache[key]

    async def parse_champions_csv(self, channel, attachment):
        async with aiohttp.ClientSession() as session:
            async with session.get(attachment['url']) as response:
                file_txt = await response.text()
        #dialect = csv.Sniffer().sniff(file_txt[:1024])
        cr = csv.DictReader(file_txt.split('\n'), #dialect,
                quoting=csv.QUOTE_NONE)
        missing = []
        dupes = []
        for row in cr:
            champ_csv = {k: parse_value(v) for k, v in row.items()}
            try:
                champ = await self.get_champion(champ_csv)
            except KeyError:
                if champ_csv['Id'].strip():
                    # non-empty champion ID
                    missing.append(champ_csv['Id'])
                continue
            if champ.immutable_id in self.roster:
                dupes.append(champ)
            self.roster[champ.immutable_id] = champ

        if missing:
            await self.bot.send_message(channel, 'Missing hookid for champs: '
                    + ', '.join(missing))
        if dupes:
            await self.bot.send_message(channel,
                    'WARNING: Multiple instances of champs in file.  '
                    + 'Overloading:\n\t'.format(
                    ', '.join([c.star_name_str for c in dupes])))

        em = discord.Embed(title="Updated Champions")
        em.add_field(name='Prestige', value=self.prestige)
        em.add_field(name='Max Prestige', value=self.max_prestige, inline=True)
        em.add_field(name='Top Champs', value='\n'.join(self.top5), inline=False)
        em.add_field(name='Max PI Champs', value='\n'.join(self.max5), inline=True)

        self.fieldnames = cr.fieldnames

        #champ_data.update({v: [] for v in self.alliance_map.values()})
        #for champ in champ_data['champs']:
        #    if champ['Role'] in self.alliance_map:
        #        champ_data[self.alliance_map[champ['Role']]].append(champ['Id'])

        self.save_champ_data()
        #if mcoc:
        await self.bot.send_message(channel, embed=em)
        #else:
        #    await self.bot.send_message(channel, 'Updated Champion Information')

    def set_defaults_of(self, champs):
        for champ in champs:
            iid = champ.immutable_id
            if iid not in self.roster:
                champ.update_default({'rank': 1, 'sig': 0})
            else:
                champ.update_default({'rank': self.roster[iid].rank,
                        'sig': self.roster[iid].sig})

    def update(self, champs):
        self.set_defaults_of(champs)
        track = {'new': set(), 'modified': set(), 'unchanged': set()}
        self._cache = {}
        for champ in champs:
            iid = champ.immutable_id
            if iid not in self.roster:
                track['new'].add(champ.verbose_prestige_str)
            else:
                if champ == self.roster[iid]:
                    track['unchanged'].add(champ.verbose_prestige_str)
                else:
                    track['modified'].add(self.update_str.format(champ,
                            self.roster[iid].rank_sig_str))
            self.roster[iid] = champ
        self.save_champ_data()
        return track

    def inc_dupe(self, champs):
        self.set_defaults_of(champs)
        track = {'modified': set(), 'missing': set()}
        self._cache = {}
        for champ in champs:
            iid = champ.immutable_id
            if iid in self.roster:
                old_str = self.roster[iid].rank_sig_str
                self.roster[iid].inc_dupe()
                track['modified'].add(self.update_str.format(self.roster[iid], old_str))
            else:
                track['missing'].add(champ.star_name_str)
        self.save_champ_data()
        return track

    def delete(self, champs):
        track = {'deleted': set(), 'non-existant': set()}
        self._cache = {}
        for champ in champs:
            iid = champ.immutable_id
            if iid not in self.roster:
                track['non-existant'].add(champ.star_name_str)
            else:
                track['deleted'].add(champ.star_name_str)
                self.roster.pop(iid)
        self.save_champ_data()
        return track

    async def display(self, tags):
        filtered = await self.filter_champs(tags)
        user = self.user
        embeds = []
        if not filtered:
            em = discord.Embed(title='User', description=user.name,
                    color=discord.Color.gold(), url=PRESTIGE_SURVEY)
            em.add_field(name='Tags used filtered to an empty roster',
                    value=' '.join(tags))
            await self.bot.say(embed=em)
            return

        strs = [champ.verbose_prestige_str for champ in sorted(filtered, reverse=True,
                    key=attrgetter('prestige', 'chlgr_rating', 'star', 'klass', 'full_name'))]
        champs_per_page = 15
        for i in range(0, len(strs)+1, champs_per_page):
            em = discord.Embed(title='', color=discord.Color.gold())
            em.set_author(name=user.name, icon_url=user.avatar_url)
            em.set_footer(text='hook/champions for Collector',
                    icon_url=GITHUB_ICON)
            page = strs[i:min(i+champs_per_page, len(strs))]
            if not page:
                break
            em.add_field(name=self.embed_display, inline=False,
                    value='\n'.join(page))
            embeds.append(em)

        if len(embeds) == 1:
            await self.bot.say(embed=embeds[0])
        else:
            menu = PagesMenu(self.bot, timeout=120, delete_onX=True, add_pageof=True)
            await menu.menu_start(embeds)

class Hook:

    def __init__(self, bot):
        self.bot = bot
        self.champ_re = re.compile(r'.*hamp.*\.csv')
        # self.champ_re = re.compile(r'champ.*\.csv')
        #self.champ_re = re.compile(r'champions(?:_\d+)?.csv')
        #self.champ_str = '{0[Stars]}★ R{0[Rank]} S{0[Awakened]:<2} {0[Id]}'


    # @commands.command(pass_context=True)
    # #async def profile(self, roster: RosterUserConverter):
    # async def profile(self, ctx, user=''):
    #     """Displays a user profile."""
    #     roster = await RosterUserConverter(ctx, user).convert()
    #     user = roster.user
    #     embeds = []
    #     if roster:
    #         em = discord.Embed(color=discord.Color.gold(),title='Prestige: {}'.format(roster.prestige))
    #         em.set_author(name=roster.user.name, icon_url=roster.user.avatar_url)
    #         em.set_footer(text='hook/champions for Collector',icon_url=GITHUB_ICON)
    #         em.add_field(name='Top Champs', value='\n'.join(roster.top5), inline=False)
    #         embeds.append(em)
    #         em2 = discord.Embed(color=discord.Color.red(),title='Max Prestige: {}'.format(roster.max_prestige))
    #         em2.set_author(name=roster.user.name,icon_url=roster.user.avatar_url)
    #         em2.set_footer(text='hook/champions for Collector',icon_url=GITHUB_ICON)
    #         em2.add_field(name='Max Champs', value='\n'.join(roster.max5), inline=False)
    #         embeds.append(em2)
    #         em3 = discord.Embed(color=discord.Color.red(),title='User Stats'.format(roster.max_prestige))
    #         em3.add_field(name='Total Number of Heroes', value='{}'.format(len(roster)))
    #         total = 0
    #         #
    #         # em3.add_field(name='Cosmic ',value='TBD')
    #         # em3.add_field(name='Mystic ',value='TBD')
    #         # em3.add_field(name='Science ',value='TBD')
    #         # em3.add_field(name='Skill ',value='TBD')
    #         # em3.add_field(name='Mutant ',value='TBD')
    #         # em3.add_field(name='Tech ',value='TBD')
    #         # rating=0
    #         # for r in range(len(roster)):
    #         #     champ = roster[r]
    #         #     if champ["Stars"] == "4" or champ["Stars"] == "5":
    #         #         rating += roster[r]['Pi']
    #         # # em3.add_field(name='Total Hero Rating',value='{}'.format(rating))
    #         # em3.add_field(name='Total 4★ & 5★ Hero Rating',value='{}'.format(rating))
    #         # embeds.append(em3)
    #     else:
    #         embeds = await self.roster_kickback(user.color)
    #     await self.pages_menu(ctx, embed_list=embeds)

    async def roster_kickback(self, ucolor = discord.Color.gold()):
        embeds=[]
        em0=discord.Embed(color=ucolor,title='No Roster detected!', description='There are several methods available to you to create your roster.  \nPlease note the paging buttons below to select your instruction set.')
        em0.set_footer(text='Collector Profile',icon_url=COLLECTOR_ICON)
        embeds.append(em0)
        em01=discord.Embed(color=ucolor, title='Manual Entry', description='Use the ```/roster add <champs>``` command to submit Champions directly to Collector.\nThis is the most common method to add to your roster, and the method you will use to maintain your roster.\n```/roster del <champs>``` allows you to remove a Champion.\n\nYouTube demo: https://youtu.be/O9Wqn1l2DEg', url='https://youtu.be/O9Wqn1l2DEg')
        em01.set_footer(text='Collector Profile',icon_url=COLLECTOR_ICON)
        embeds.append(em01)
        em=discord.Embed(color=ucolor, title='Champion CSV template', url='https://goo.gl/LaFrg7')
        em.add_field(name='Google Sheet Instructions',value='Save a copy of the template (blue text):\n1. Add 5★ champions you do have.\n2. Delete 4★ champions you do not have.\n3. Set Rank = champion rank (1 to 5).\n4. Set Awakened = signature ability level.\n``[4★: 0 to 99 | 5★: 0 to 200]``\n5. Export file as \'champions.csv\'.\n6. Upload to Collector.\n7. Select OK to confirm')
        em.add_field(name='Prerequisite', value='Google Sheets\n(there is an app for iOS|Android)',inline=False)
        em.set_footer(text='CSV import',icon_url=GSHEET_ICON)
        embeds.append(em)
        em2=discord.Embed(color=ucolor,title='Import from Hook',url=HOOK_URL)
        em2.add_field(name='Hook instructions',value='1. Go to Hook/Champions webapp (blue text)\n2. Add Champions.\n3. Set Rank & Signature Ability level\n4. From the Menu > Export CSV as \'champions.csv\'\n5. Upload to Collector.\n6. Select OK to confirm')
        em2.set_footer(text='hook/champions',icon_url=GITHUB_ICON)
        embeds.append(em2)
        em3=discord.Embed(color=ucolor,title='Import from Hook',url=HOOK_URL)
        em3.add_field(name='iOS + Hook instructions',value='1. Go to Hook/Champions webapp (blue text)\n2. Add Champions.\n3. Set Rank & Signature Ability level\n4. From the Menu > Export CSV > Copy Text from Safari\n5. In Google Sheets App > paste\n6. Download as \'champions.csv\'\n5. Upload to Collector.\n6. Select OK to confirm')
        em3.add_field(name='Prerequisite', value='Google Sheets\n(there is an app for iOS|Android)',inline=False)
        em3.set_footer(text='hook + Google Sheets',icon_url=GSHEET_ICON)
        embeds.append(em3)
        return embeds



    @commands.command(pass_context=True, aliases=('list_members','role_roster','list_users'))
    async def users_by_role(self, ctx, role: discord.Role, use_alias=True):
        '''Embed a list of server users by Role'''
        server = ctx.message.server
        members = []
        for member in server.members:
            if role in member.roles:
                members.append(member)
        # members.sort(key=attrgetter('name'))
        if use_alias:
            ret = '\n'.join([m.display_name for m in members])
        else:
            ret = '\n'.join([m.name for m in members])
        em = discord.Embed(title='{0.name} Role - {1} member(s)'.format(role, len(members)),
                description=ret, color=role.color)
        await self.bot.say(embed=em)

    @commands.command(pass_context=True, no_pm=True)
    async def team(self,ctx, *, user : discord.Member=None):
        """Displays a user's AQ/AWO/AWD teams.
        Teams are set in hook/champions"""
        if user is None:
            user = ctx.message.author
        # creates user if doesn't exist
        info = self.load_champ_data(user)
        em = discord.Embed(title="User Profile", description=user.name)
        if info['aq']:
            em.add_field(name='AQ Champs', value='\n'.join(info['aq']))
        if info['awo']:
            em.add_field(name='AWO Champs', value='\n'.join(info['awo']))
        if info['awd']:
            em.add_field(name='AWD Champs', value='\n'.join(info['awd']))
        await self.bot.say(embed=em)

    @commands.group(pass_context=True, invoke_without_command=True)
    async def roster(self, ctx, *, hargs=''):
    #async def roster(self, ctx, *, hargs: HashtagRosterConverter):
        """Displays a user roster with tag filtering

        example:
        /roster [user] [#mutant #bleed]"""
        hargs = await HashtagRosterConverter(ctx, hargs).convert()
        await hargs.roster.display(hargs.tags)

    @roster.command(pass_context=True, name='add', aliases=('update',))
    async def _roster_update(self, ctx, *, champs: ChampConverterMult):
        '''Add or Update champion(s).

        Add or Update your roster using the standard command line syntax.
        Defaults for champions you specify are the current values in your roster.
        If it is a new champ, defaults are 4*, rank 1, sig 0.

        This means that
        /roster update some_champs20
        would just set some_champ's sig to 20 but keep it's rank the same.

        example:
        /roster add angelar4s20 karnakr5s80 medusar4s20
        '''
        roster = ChampionRoster(ctx.bot, ctx.message.author)
        await roster.load_champions()
        await self._update(roster, champs)

    async def _update(self, roster, champs):
        track = roster.update(champs)
        em = discord.Embed(title='Champion Update for {}'.format(roster.user.name),
                color=discord.Color.gold())
        if len(champs) <= 20:
            for k in ('new', 'modified', 'unchanged'):
                if track[k]:
                    em.add_field(name='{} Champions'.format(k.capitalize()),
                            value='\n'.join(sorted(track[k])), inline=False)
        else:
            em.add_field(name='{} Champions updated, confirmed.'.format(len(champs)), value='Number exceeds display limitation')
        await self.bot.say(embed=em)

    @roster.command(pass_context=True, name='dupe')
    async def _roster_dupe(self, ctx, *, champs: ChampConverterMult):
        '''Increase sig level by dupe.

        Update your roster by incrementing your champs by the duped sig level, i.e. 20 for a 4*.
        example:
        /roster dupe karnak
        '''
        roster = ChampionRoster(ctx.bot, ctx.message.author)
        await roster.load_champions()
        track = roster.inc_dupe(champs)
        em = discord.Embed(title='Champion Dupe Update for {}'.format(roster.user.name),
                color=discord.Color.gold())
        for k in ('modified', 'missing'):
            if track[k]:
                em.add_field(name='{} Champions'.format(k.capitalize()),
                        value='\n'.join(sorted(track[k])), inline=False)
        await self.bot.say(embed=em)

    @roster.command(pass_context=True, name='delete', aliases=('del','remove',))
    async def _roster_del(self, ctx, *, champs: ChampConverterMult):
        '''Delete champion(s)

        Delete champion(s) from your roster.
        example:
        /roter delete angela blackbolt medusa'''
        roster = ChampionRoster(ctx.bot, ctx.message.author)
        await roster.load_champions()
        track = roster.delete(champs)
        em = discord.Embed(title='Champion Deletion for {}'.format(roster.user.name),
                color=discord.Color.gold())
        for k in ('deleted', 'non-existant'):
            if track[k]:
                em.add_field(name='{} Champions'.format(k.capitalize()),
                        value='\n'.join(sorted(track[k])), inline=False)
        await self.bot.say(embed=em)

    @roster.command(pass_context=True, name='import', hidden=True)
    async def _roster_import(self, ctx):
        '''Silent import file attachement'''
        if not ctx.message.attachments:
            await self.bot.say('This command can only be used when uploading files')
            return
        for atch in ctx.message.attachments:
            if atch['filename'].endswith('.csv'):
                roster = ChampionRoster(self.bot, ctx.message.author)
                await roster.parse_champions_csv(ctx.message.channel, atch)
            else:
                await self.bot.say("Cannot import '{}'.".format(atch)
                        + "  File must end in .csv and come from a Hook export")

    @roster.command(pass_context=True, name='export')
    async def _roster_export(self, ctx):
        '''Export roster as champions.csv
        Exported file can be imported to hook/champions
        '''
        roster = ChampionRoster(ctx.bot, ctx.message.author)
        await roster.load_champions()
        rand = randint(1000, 9999)
        path, ext = os.path.split(roster.champs_file)
        tmp_file = '{}-{}.tmp'.format(path, rand)
        # with open(tmp_file, 'w') as fp:
        with open(tmp_file, 'w', encoding='utf-8') as fp:
            writer = csv.DictWriter(fp, fieldnames=roster.fieldnames,
                    extrasaction='ignore', lineterminator='\n')
            writer.writeheader()
            for champ in roster.roster.values():
                writer.writerow(champ.to_json())
        filename = roster.data_dir + '/champions.csv'
        os.replace(tmp_file, filename)
        await self.bot.upload(filename)
        os.remove(filename)

    @roster.command(pass_context=True, name='template')
    async def _roster_template(self, ctx, *, user : discord.User = None):
        '''Google Sheet Template

        Blank CSV template for champion importself.

        1. Add 5★ champions you do have.
        2. Delete 4★ champions (rows) you do not have.
        3. Set Rank = champion rank (1 to 5).
        4. Set Awakened = signature ability level.
        [4★: 0 to 99 | 5★: 0 to 200]
        5. Export file as 'champions.csv'.
        6. Upload CSV to Collector.
        7. Press OK'''

        if user is None:
            user=ctx.message.author
        message = 'Save a copy of the template (blue text):\n\n1. Add 5★ champions you do have.\n2. Delete 4★ champions you do not have.\n3. Set Rank = champion rank (1 to 5).\n4. Set Awakened = signature ability level.\n``[4★: 0 to 99 | 5★: 0 to 200]``\n5. Export file as \'champions.csv\'.\n6. Upload to Collector.\n7. Press OK\n\nPrerequisite: Google Sheets\n(there is an app for iOS|Android)\n'

        em =discord.Embed(color=user.color, title='Champion CSV template',description=message, url='https://goo.gl/LaFrg7')
        em.set_author(name=user.name, icon_url=user.avatar_url)
        em.set_footer(text='hook/champions for Collector',icon_url=GITHUB_ICON)
        await self.bot.send_message(ctx.message.channel, embed=em)
        # await self.bot.send_message(ctx.message.channel,'iOS dumblink: https://goo.gl/LaFrg7')

    @roster.command(pass_context=True, hidden=True, name='role_export',aliases=('rrx',))
    async def _role_roster_export(self, ctx, role: discord.Role):
        '''Returns a CSV file with all Roster data for all members of a Role'''
        server = ctx.message.server
        roster = ChampionRoster(ctx.bot, ctx.message.author)
        await roster.load_champions()
        rand = randint(1000, 9999)
        path, ext = os.path.split(roster.champs_file)
        tmp_file = '{}-{}.tmp'.format(path, rand)
        # with open(tmp_file, 'w') as fp:
        with open(tmp_file, 'w', encoding='utf-8') as fp:
            writer = csv.DictWriter(fp, fieldnames=['member_mention','member_name', *(roster.fieldnames)], extrasaction='ignore', lineterminator='\n')
            writer.writeheader()
            for member in server.members:
                if role in member.roles:
                    roster = ChampionRoster(ctx.bot, member)
                    await roster.load_champions()
                    for champ in roster.roster.values():
                        champ_dict = champ.to_json()
                        champ_dict['member_mention'] = member.mention
                        champ_dict['member_name'] = member.name
                        writer.writerow(champ_dict)
        filename = roster.data_dir + '/' + role.name + '.csv'
        os.replace(tmp_file, filename)
        await self.bot.upload(filename)
        os.remove(filename)


    @commands.command(pass_context=True, name='rank_prestige', aliases=('prestige_list',))
    async def _rank_prestige(self, ctx, *, hargs=''):
        hargs = await HashtagRankConverter(ctx, hargs).convert()
        roster = ChampionRoster(self.bot, self.bot.user)
        mcoc = self.bot.get_cog('MCOC')
        rlist = []
        for champ_class in mcoc.champions.values():
            champ = champ_class(hargs.attrs.copy())
            if champ.has_prestige:
                rlist.append(champ)
        roster.from_list(rlist)
        roster.display_override = 'Prestige Listing: {0.attrs_str}'.format(rlist[0])
        await roster.display(hargs.tags)


    @commands.command(pass_context=True, no_pm=True)
    async def clan_prestige(self, ctx, role : discord.Role, verbose=0):
        '''Report Clan Prestige.
        Specify clan-role or battlegroup-role.'''
        server = ctx.message.server
        width = 20
        prestige = 0
        cnt = 0
        line_out = []
        for member in server.members:
            if role in member.roles:
                roster = ChampionRoster(self.bot, member)
                await roster.load_champions()
                if roster.prestige > 0:
                    prestige += roster.prestige
                    cnt += 1
                if verbose is 1:
                    line_out.append('{:{width}} p = {}'.format(
                        member.name, roster.prestige, width=width))
                elif verbose is 2:
                    line_out.append('{:{width}} p = {}'.format(
                        member.display_name, roster.prestige, width=width))
        if verbose > 0:
            line_out.append('_' * (width + 11))
        if cnt > 0:
            line_out.append('{0:{width}} p = {1}  from {2} members'.format(
                    role.name, round(prestige/cnt,0), cnt, width=width))
            await self.bot.say('```{}```'.format('\n'.join(line_out)))
        else:
            await self.bot.say('You cannot divide by zero.')


    # @commands.group(pass_context=True, aliases=('teams',))
    # async def team(self, ctx):
    #     if ctx.invoked_subcommand is None:
    #         await self.bot.send_cmd_help(ctx)
    #         return
    #
    # @team.command(pass_context=True, name='awd')
    # async def _team_awd(self, ctx):
    #     '''Return user AWD team'''
    #     channel = ctx.message.channel
    #     self.bot.send_message(channel,'DEBUG: team awd invoked: {}'.format(ctx))
    #     user = ctx.message.author
    #     message = ctx.message
    #     if message is discord.Role:
    #         self.bot.say('DEBUG: discord.Role identified')
    #     elif message is discord.Member:
    #         self.bot.say('DEBUG: discord.Member identified')
    #         user = message
    #         info = self.load_champ_data(user)
    #         em = discord.Embed(title='War Defense',description=user.name)
    #         team = []
    #         for k in info['awd']:
    #             champ = self.mcocCog._resolve_alias(k)
    #             team.append(champ.full_name)
    #         em.add_field(name='AWD:',value=team)
    #         self.bot.say(embed=em)

    async def pages_menu(self, ctx, embed_list: list, category: str='',
            message: discord.Message=None, page=0, timeout: int=30, choice=False):
        """menu control logic for this taken from
           https://github.com/Lunar-Dust/Dusty-Cogs/blob/master/menu/menu.py"""
        #print('list len = {}'.format(len(embed_list)))
        length = len(embed_list)
        em = embed_list[page]
        if not message:
            message = await self.bot.say(embed=em)
            if length > 5:
                await self.bot.add_reaction(message, '⏪')
            if length > 1:
                await self.bot.add_reaction(message, '◀')
            if choice is True:
                await self.bot.add_reaction(message,'🆗')
            await self.bot.add_reaction(message, '❌')
            if length > 1:
                await self.bot.add_reaction(message, '▶')
            if length > 5:
                await self.bot.add_reaction(message, '⏩')
        else:
            message = await self.bot.edit_message(message, embed=em)
        await asyncio.sleep(1)

        react = await self.bot.wait_for_reaction(message=message, timeout=timeout,emoji=['▶', '◀', '❌', '⏪', '⏩','🆗'])
        # if react.reaction.me == self.bot.user:
        #     react = await self.bot.wait_for_reaction(message=message, timeout=timeout,emoji=['▶', '◀', '❌', '⏪', '⏩','🆗'])
        if react is None:
            try:
                try:
                    await self.bot.clear_reactions(message)
                except:
                    await self.bot.remove_reaction(message,'⏪', self.bot.user) #rewind
                    await self.bot.remove_reaction(message, '◀', self.bot.user) #previous_page
                    await self.bot.remove_reaction(message, '❌', self.bot.user) # Cancel
                    await self.bot.remove_reaction(message,'🆗',self.bot.user) #choose
                    await self.bot.remove_reaction(message, '▶', self.bot.user) #next_page
                    await self.bot.remove_reaction(message,'⏩', self.bot.user) # fast_forward
            except:
                pass
            return None
        elif react is not None:
            # react = react.reaction.emoji
            if react.reaction.emoji == '▶': #next_page
                next_page = (page + 1) % len(embed_list)
                # await self.bot.remove_reaction(message, '▶', react.user)
                try:
                    await self.bot.remove_reaction(message, '▶', react.user)
                except:
                    pass
                return await self.pages_menu(ctx, embed_list, message=message, page=next_page, timeout=timeout)
            elif react.reaction.emoji == '◀': #previous_page
                next_page = (page - 1) % len(embed_list)
                try:
                    await self.bot.remove_reaction(message, '◀', react.user)
                except:
                    pass
                return await self.pages_menu(ctx, embed_list, message=message, page=next_page, timeout=timeout)
            elif react.reaction.emoji == '⏪': #rewind
                next_page = (page - 5) % len(embed_list)
                try:
                    await self.bot.remove_reaction(message, '⏪', react.user)
                except:
                    pass
                return await self.pages_menu(ctx, embed_list, message=message, page=next_page, timeout=timeout)
            elif react.reaction.emoji == '⏩': # fast_forward
                next_page = (page + 5) % len(embed_list)
                try:
                    await self.bot.remove_reaction(message, '⏩', react.user)
                except:
                    pass
                return await self.pages_menu(ctx, embed_list, message=message, page=next_page, timeout=timeout)
            elif react.reaction.emoji == '🆗': #choose
                if choice is True:
                    # await self.bot.remove_reaction(message, '🆗', react.user)
                    prompt = await self.bot.say(SELECTION.format(category+' '))
                    answer = await self.bot.wait_for_message(timeout=10, author=ctx.message.author)
                    if answer is not None:
                        await self.bot.delete_message(prompt)
                        prompt = await self.bot.say('Process choice : {}'.format(answer.content.lower().strip()))
                        url = '{}{}/{}'.format(BASEURL,category,answer.content.lower().strip())
                        await self._process_item(ctx, url=url, category=category)
                        await self.bot.delete_message(prompt)
                else:
                    pass
            else:
                try:
                    return await self.bot.delete_message(message)
                except:
                    pass

    async def _on_attachment(self, msg):
        channel = msg.channel
        prefixes = tuple(self.bot.settings.get_prefixes(msg.server))
        if not msg.attachments or msg.author.bot or msg.content.startswith(prefixes):
            return
        for attachment in msg.attachments:
            if self.champ_re.match(attachment['filename']):
                message = await self.bot.send_message(channel,
                        "Found a CSV file to import.  \nLoad new champions? \nSelect OK to continue or X to cancel.")
                await self.bot.add_reaction(message, '❌')
                await self.bot.add_reaction(message, '🆗')
                react = await self.bot.wait_for_reaction(message=message, user=msg.author, timeout=30, emoji=['❌', '🆗'])
                if react is not None:
                    # await self.bot.send_message(channel, 'Reaction detected.')
                    if react.reaction.emoji == '🆗':
                        await self.bot.send_message(channel,'OK detected')
                        roster = ChampionRoster(self.bot, msg.author)
                        await roster.parse_champions_csv(msg.channel, attachment)
                    elif react.reaction.emoji == '❌':
                        await self.bot.send_message(channel,'X detected')
                        await self.bot.delete_message(message)
                        await self.bot.send_message(channel, 'Import canceled by user.')
                elif react is None:
                    await self.bot.send_message(channel, 'No reaction detected.')
                    try:
                        await self.bot.remove_reaction(message, '❌', self.bot.user) # Cancel
                        await self.bot.remove_reaction(message,'🆗',self.bot.user) #choose
                    except:
                        self.bot.delete_message(message)
                    await self.bot.send_message(channel, "Did not import")

def parse_value(value):
    try:
        return ast.literal_eval(value)
    except Exception:
        return value


#-------------- setup -------------
def check_folders():
    #if not os.path.exists("data/hook"):
        #print("Creating data/hook folder...")
        #os.makedirs("data/hook")

    if not os.path.exists("data/hook/users"):
        print("Creating data/hook/users folder...")
        os.makedirs("data/hook/users")
        #transfer_info()

def setup(bot):
    check_folders()
    override_error_handler(bot)
    n = Hook(bot)
    bot.add_cog(n)
    bot.add_listener(n._on_attachment, name='on_message')
