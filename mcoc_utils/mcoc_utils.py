
import discord
from discord.ext import commands
from math import *
from .utils.dataIO import dataIO
from .utils import chat_formatting as chat
from operator import itemgetter, attrgetter
from collections import OrderedDict, defaultdict, namedtuple
from functools import partial
import pygsheets
from pygsheets.utils import numericise_all
import types
import logging
import asyncio
import re
import os
import ast



class_color_codes = {
        'Cosmic': discord.Color(0x2799f7), 'Tech': discord.Color(0x0033ff),
        'Mutant': discord.Color(0xffd400), 'Skill': discord.Color(0xdb1200),
        'Science': discord.Color(0x0b8c13), 'Mystic': discord.Color(0x7f0da8),
        'All': discord.Color(0xffffff), 'default': discord.Color.light_grey(),
        }
class_emoji = {
        'All':'<:all2:339511715920084993>',
        'Cosmic':'<:cosmic2:339511716104896512>',
        'Tech':'<:tech2:339511716197171200>',
        'Mutant':'<:mutant2:339511716201365514>',
        'Skill':'<:skill2:339511716549230592>',
        'Science':'<:science2:339511716029267969>',
        'Mystic':'<:mystic2:339511716150771712>',
        }

def from_flat(flat, ch_rating):
    denom = 5 * ch_rating + 1500 + flat
    return round(100*flat/denom, 2)

def to_flat(per, ch_rating):
    num = (5 * ch_rating + 1500) * per
    return round(num/(100-per), 2)

class QuietUserError(commands.UserInputError):
    pass

class AmbiguousArgError(QuietUserError):
    pass

class MisorderedArgumentError(QuietUserError):
    pass

class MissingRosterError(QuietUserError):
    pass

class ChampConverter(commands.Converter):
    '''Argument Parsing class that geneartes Champion objects from user input'''

    arg_help = '''
    Specify a single champion with optional parameters of star, rank, or sig.
    Champion names can be a number of aliases or partial aliases if no conflicts are found.

    The optional arguments can be in any order, with or without spaces.
        <digit>* specifies star <default: 4>
        r<digit> specifies rank <default: 5>
        s<digit> specifies signature level <default: 99>

    Examples:
        4* yj r4 s30  ->  4 star Yellowjacket rank 4/40 sig 30
        r35*im        ->  5 star Ironman rank 3/45 sig 99
        '''
#(?:(?:s(?P<sig>[0-9]{1,3})) |(?:r(?P<rank>[1-5]))|(?:(?P<star>[1-5])\\?\*)|(?:d(?P<debug>[0-9]{1,2})))(?=\b|[a-zA-Z]|(?:[1-5]\\?\*))
    _bare_arg = None
    parse_re = re.compile(r'''(?:s(?P<sig>[0-9]{1,3}))
                             |(?:r(?P<rank>[1-5]))
                             |(?:(?P<star>[1-5])\\?\*)
                             |(?:d(?P<debug>[0-9]{1,2}))''', re.X)
    async def convert(self):
        bot = self.ctx.bot
        attrs = {}
        if self._bare_arg:
            args = self.argument.rsplit(' ', maxsplit=1)
            if len(args) > 1 and args[-1].isdecimal():
                attrs[self._bare_arg] = int(args[-1])
                self.argument = args[0]
        arg = ''.join(self.argument.lower().split(' '))
        for m in self.parse_re.finditer(arg):
            attrs[m.lastgroup] = int(m.group(m.lastgroup))
        token = self.parse_re.sub('', arg)
        if not token:
            err_str = "No Champion remains from arg '{}'".format(self.argument)
            await bot.say(err_str)
            raise commands.BadArgument(err_str)
        return (await self.get_champion(bot, token, attrs))

    async def get_champion(self, bot, token, attrs):
        mcoc = bot.get_cog('MCOC')
        try:
            champ = await mcoc.get_champion(token, attrs)
        except KeyError:
            champs = await mcoc.search_champions('.*{}.*'.format(token), attrs)
            if len(champs) == 1:
                await bot.say("'{}' was not exact but found close alternative".format(
                        token))
                champ = champs[0]
            elif len(champs) > 1:
                em = discord.Embed(title='Ambiguous Argument "{}"'.format(token),
                        description='Resolved to multiple possible champs')
                for champ in champs:
                    em.add_field(name=champ.full_name, inline=False,
                            value=chat.box(', '.join(champ.alias_set)))
                await bot.say(embed=em)
                raise AmbiguousArgError('Multiple matches for arg "{}"'.format(token))
            else:
                err_str = "Cannot resolve alias for '{}'".format(token)
                await bot.say(err_str)
                raise commands.BadArgument(err_str)
        return champ

class ChampConverterSig(ChampConverter):
    _bare_arg = 'sig'
    arg_help = ChampConverter.arg_help + '''
    Bare Number argument for this function is sig level:
        "yjr5s30" is equivalent to "yjr5 30"'''

class ChampConverterRank(ChampConverter):
    _bare_arg = 'rank'
    arg_help = ChampConverter.arg_help + '''
    Bare Number argument for this function is rank:
        "yjr5s30" is equivalent to "yjs30 5"'''

class ChampConverterStar(ChampConverter):
    _bare_arg = 'star'
    arg_help = ChampConverter.arg_help + '''
    Bare Number argument for this function is star:
        "5*yjr5s30" is equivalent to "yjr5s30 5"'''

class ChampConverterDebug(ChampConverter):
    _bare_arg = 'debug'

class ChampConverterMult(ChampConverter):

    arg_help = '''
    Specify multiple champions with optional parameters of star, rank, or sig.
    Champion names can be a number of aliases or partial aliases if no conflicts are found.

    The optional arguments can be in any order.
        <digit>* specifies star <default: 4>
        r<digit> specifies rank <default: 5>
        s<digit> specifies signature level <default: 99>

    If optional arguments are listed without a champion, it changes the default for all
    remaining champions.  Arguments attached to a champion are local to that champion
    only.

    Examples:
        s20 yj im        ->  4* Yellowjacket r5/50 sig 20, 4* Ironman r5/50 sig 20
        r35*ims20 ims40  ->  5 star Ironman r3/45 sig 20, 4* Ironman r5/50 sig 40
        r4s20 yj ims40 lc -> 4* Yellowjacket r4/40 sig 20, 4* Ironman r4/40 sig 40, 4* Luke Cage r4/40 sig 20
        '''

    async def convert(self):
        bot = self.ctx.bot
        champs = []
        default = {}
        dangling_arg = None
        for arg in self.argument.lower().split(' '):
            attrs = default.copy()
            for m in self.parse_re.finditer(arg):
                attrs[m.lastgroup] = int(m.group(m.lastgroup))
            token = self.parse_re.sub('', arg)
            if token != '':
                champ = await self.get_champion(bot, token, attrs)
                dangling_arg = None
                champs.append(champ)
            else:
                default.update(attrs)
                dangling_arg = arg
        if dangling_arg:
            em = discord.Embed(title='Dangling Argument',
                    description="Last argument '{}' is unused.\n".format(dangling_arg)
                        + "Place **before** the champion or **without a space**.")
            await bot.say(embed=em)
        return champs


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
            em = discord.Embed(color=discord.Color.green(),title='[????] {}'.format(user.name))
            em.add_field(name='Missing Roster',
                    value='Load up a "champ*.csv" file from Hook to import your roster')
            em.add_field(name='Hook Web App', value='http://hook.github.io/champions/#/roster')
            em.set_footer(text='hook/champions for Collector',icon_url='https://assets-cdn.github.com/favicon.ico')
            await self.ctx.bot.say(embed=em)
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


class GSExport():

    default_settings = dict(sheet_name=None,
                            sheet_action='file',
                            data_type='dict',
                            range=None,
                            include_empty=False,
                            postprocess=None,
                            prepare_function='do_nothing',
                        )

    def __init__(self, bot, gc, *, gkey, local, **kwargs):
        self.bot = bot
        self.gc = gc
        self.gkey = gkey
        self.local = local
        self.meta_sheet = kwargs.pop('meta_sheet', 'meta_sheet')
        self.settings = self.default_settings.copy()
        self.settings.update(kwargs)
        #self.sheet_name = kwargs.pop('sheet_name', None)
        #for k,v in self.default_settings:
            #self.settings[k] = kwargs.pop(k, v)
        self.data = defaultdict(partial(defaultdict, dict))

    async def retrieve_data(self):
        try:
            ss = self.gc.open_by_key(self.gkey)
        except:
            await self.bot.say("Error opening Spreadsheet <{}>".format(self.gkey))
            return
        if self.meta_sheet and self.settings['sheet_name'] is None:
            try:
                meta = ss.worksheet('title', self.meta_sheet)
            except pygsheets.WorksheetNotFound:
                meta = None
        else:
            meta = None

        if meta:
            for record in meta.get_all_records():
                [record.update(((k,v),)) for k,v in self.settings.items() if k not in record]
                await self.retrieve_sheet(ss, **record)
        else:
            await self.retrieve_sheet(ss, **self.settings)

        if self.settings['postprocess']:
            await self.settings['postprocess'](self.bot, self.data)
        if self.local:
            dataIO.save_json(self.local, self.data)
        return self.data

    async def retrieve_sheet(self, ss, *, sheet_name, sheet_action, data_type, **kwargs):
        if sheet_name:
            sheet = ss.worksheet('title', sheet_name)
        else:
            sheet = ss.sheet1
            sheet_name = sheet.title
        print(kwargs)
        print(self.settings)
        if kwargs['range']:
            rng = self.bound_range(sheet, kwargs['range'])
            data = sheet.get_values(*rng, returnas='matrix', 
                    include_empty=kwargs['include_empty'])
        else:
            data = sheet.get_all_values(include_empty=kwargs['include_empty'])
        header = data[0]
        if data_type.startswith('nested_list'):
            data_type, dlen = data_type.rsplit('::', maxsplit=1)
            dlen = int(dlen)

        prep_func = getattr(self, kwargs['prepare_function'])
        self.data['_headers'][sheet_name] = header
        for row in data[1:]:
            drow = numericise_all(prep_func(row), '')
            rkey = drow[0]
            if sheet_action == 'merge':
                if data_type == 'nested_dict':
                    pack = dict(zip(header[2:], drow[2:]))
                    self.data[rkey][sheet_name][drow[1]] = pack
                    continue
                if data_type == 'list':
                    pack = drow[1:]
                elif data_type == 'nested_list':
                    if len(drow[1:]) < dlen or not any(drow[1:]):
                        pack = None
                    else:
                        pack = [drow[i:i+dlen] for i in range(1, len(drow), dlen)]
                self.data[rkey][sheet_name] = pack
            elif sheet_action in ('dict', 'file'):
                if data_type == 'list':
                    pack = drow[1:]
                elif data_type == 'dict':
                    pack = dict(zip(header, drow))
                if sheet_action == 'dict':
                    self.data[sheet_name][rkey] = pack
                elif sheet_action == 'file':
                    self.data[rkey] = pack

    @staticmethod
    def bound_range(sheet, rng_str):
        rng = rng_str.split(':')
        rows = (1, sheet.rows)
        for i in range(2):
            if not rng[i][-1].isdigit():
                rng[i] = '{}{}'.format(rng[i], rows[i])
        return rng

    @staticmethod
    def do_nothing(row):
        return row

    @staticmethod
    def remove_commas(row):
        return [cell.replace(',', '') for cell in row]

    @staticmethod
    def remove_NA(row):
        return [None if cell in ("#N/A", "") else cell for cell in row]


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
                    color=discord.Color.gold())
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
                    icon_url='https://assets-cdn.github.com/favicon.ico')
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


class MCOCUtils:

    def __init__(self, bot):
        self.bot = bot



    @commands.command(aliases=('p2f',), hidden=True)
    async def per2flat(self, per: float, ch_rating: int=100):
        '''Convert Percentage to MCOC Flat Value'''
        await self.bot.say(to_flat(per, ch_rating))

    @commands.command(name='flat', aliases=('f2p'))
    async def flat2per(self, *, m):
        '''Convert MCOC Flat Value to Percentge
        <equation> [challenger rating = 100]'''
        if ' ' in m:
            m, cr = m.rsplit(' ',1)
            challenger_rating = int(cr)
        else:
            challenger_rating = 100
        m = ''.join(m)
        math_filter = re.findall(r'[\[\]\-()*+/0-9=.,% ]' +
            r'|acos|acosh|asin|asinh' +
            r'|atan|atan2|atanh|ceil|copysign|cos|cosh|degrees|e|erf|erfc|exp' +
            r'|expm1|fabs|factorial|floor|fmod|frexp|fsum|gamma|gcd|hypot|inf' +
            r'|isclose|isfinite|isinf|isnan|round|ldexp|lgamma|log|log10|log1p' +
            r'|log2|modf|nan|pi|pow|radians|sin|sinh|sqrt|tan|tanh', m)
        flat_val = eval(''.join(math_filter))
        p = from_flat(flat_val, challenger_rating)
        em = discord.Embed(color=discord.Color.gold(),
                title='FlatValue:',
                description='{}'.format(flat_val))
        em.add_field(name='Percentage:', value='{}\%'.format(p))
        await self.bot.say(embed=em)

    @commands.command(aliases=('compf','cfrac'), hidden=True)
    async def compound_frac(self, base: float, exp: int):
        '''Calculate multiplicative compounded fractions'''
        if base > 1:
            base = base / 100
        compound = 1 - (1 - base)**exp
        em = discord.Embed(color=discord.Color.gold(),
            title="Compounded Fractions",
            description='{:.2%} compounded {} times'.format(base, exp))
        em.add_field(name='Expected Chance', value='{:.2%}'.format(compound))
        await self.bot.say(embed=em)


def parse_value(value):
    try:
        return ast.literal_eval(value)
    except Exception:
        return value


def setup(bot):
    if not hasattr(bot, '_command_error_orig'):
        bot._command_error_orig = bot.on_command_error
        @bot.event
        async def on_command_error(error, ctx):
            if isinstance(error, QuietUserError):
                bot.logger.info('<{}> {}'.format(type(error).__name__, error))
            else:
                await bot._command_error_orig(error, ctx)
    bot.add_cog(MCOCUtils(bot))