import re
from datetime import datetime, timedelta
from textwrap import wrap
from collections import UserDict, defaultdict, ChainMap, namedtuple, OrderedDict
from functools import partial
from math import log2
from math import *
from operator import attrgetter
import os
import time
import inspect
import aiohttp
import logging
import csv
import json
import pygsheets
import random

from pygsheets.utils import numericise_all, numericise
import asyncio
from .utils.dataIO import dataIO
from functools import wraps
import discord
from discord.ext import commands
from .utils import chat_formatting as chat
from __main__ import send_cmd_help
from cogs.utils import checks
#from .hook import ChampionRoster, HashtagRankConverter
# from .hook import PagesMenu

## experimental jjw
import matplotlib.pyplot as plt

logger = logging.getLogger('red.mcoc')
logger.setLevel(logging.INFO)

class TitleError(Exception):
    def __init__(self, champ):
        self.champ = champ

data_files = {
    'spotlight': {'remote': 'https://docs.google.com/spreadsheets/d/1I3T2G2tRV05vQKpBfmI04VpvP5LjCBPfVICDmuJsjks/pub?gid=0&single=true&output=csv',
                'local': 'data/mcoc/spotlight_data.csv', 'update_delta': 1},
    'crossreference': {'remote': 'https://docs.google.com/spreadsheets/d/1WghdD4mfchduobH0me4T6IvhZ-owesCIyLxb019744Y/pub?gid=0&single=true&output=csv',
                'local': 'data/mcoc/crossreference.csv', 'update_delta': 1},
    'prestigeCSV':{'remote': 'https://docs.google.com/spreadsheets/d/1I3T2G2tRV05vQKpBfmI04VpvP5LjCBPfVICDmuJsjks/pub?gid=1346864636&single=true&output=csv',
                'local': 'data/mcoc/prestige.csv', 'update_delta': 1},
    'duelist' : {'remote': 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTsPSNaY6WbNF1fY49jqjRm9hJZ60Sa6fU6Yd_t7nOrIxikVj-Y7JW_YSPwHoJfix9MA4YgWSenIwfl/pub?gid=694495962&single=true&output=csv',
                'local': 'data/mcoc/duelist.csv', 'update_delta': 1},
    #'masteries' : {'remote':'https://docs.google.com/spreadsheets/d/1mEnMrBI5c8Tbszr0Zne6qHkW6WxZMXBOuZGe9XmrZm8/pub?gid=0&single=true&output=csv',
                #'local': 'data/mcoc/masteries.csv', 'update_delta': 1},
    }

GS_BASE='https://sheets.googleapis.com/v4/spreadsheets/{}/values/{}?key=AIzaSyBugcjKbOABZEn-tBOxkj0O7j5WGyz80uA&majorDimension=ROWS'
GSHEET_ICON='https://d2jixqqjqj5d23.cloudfront.net/assets/developer/imgs/icons/google-spreadsheet-icon.png'
SPOTLIGHT_DATASET='https://docs.google.com/spreadsheets/d/e/2PACX-1vRFLWYdFMyffeOzKiaeQeqoUgaESknK-QpXTYV2GdJgbxQkeCjoSajuLjafKdJ5imE1ADPYeoh8QkAr/pubhtml?gid=1483787822&single=true'
SPOTLIGHT_SURVEY='https://docs.google.com/forms/d/e/1FAIpQLSe4JYzU5CsDz2t0gtQ4QKV8IdVjE5vaxJBrp-mdfKxOG8fYiA/viewform?usp=sf_link'
PRESTIGE_SURVEY='https://docs.google.com/forms/d/e/1FAIpQLSeo3YhZ70PQ4t_I4i14jX292CfBM8DMb5Kn2API7O8NAsVpRw/viewform?usp=sf_link'
COLLECTOR_ICON='https://raw.githubusercontent.com/JasonJW/mcoc-cogs/master/mcoc/data/cdt_icon.png'
MODOKSAYS = ['alien', 'buffoon', 'charlatan', 'creature', 'die', 'disintegrate',
        'evaporate', 'feelmypower', 'fool', 'fry', 'haha', 'iamscience', 'idiot',
        'kill', 'oaf', 'peabrain', 'pretender', 'sciencerules', 'silence',
        'simpleton', 'tincan', 'tremble', 'ugh', 'useless']

local_files = {
    "sig_coeff": "data/mcoc/sig_coeff.csv",
    "effect_keys": "data/mcoc/effect_keys.csv",
    "signature": "data/mcoc/signature.json",
    "sig_coeff_4star": "data/mcoc/sig_coeff_4star.json",
    "sig_coeff_5star": "data/mcoc/sig_coeff_5star.json",
    "synergy": "data/mcoc/synergy.json",
}

async def postprocess_sig_data(bot, struct):
    sigs = load_kabam_json(kabam_bcg_stat_en, aux=struct.get("bcg_stat_en_aux"))
    mcoc = bot.get_cog('MCOC')
    missing = []
    for key in struct.keys():
        champ_class = mcoc.champions.get(key.lower(), None)
        if champ_class is None:
            continue
        try:
            struct[key]['kabam_text'] = champ_class.get_kabam_sig_text(
                    champ_class, sigs=sigs,
                    champ_exceptions=struct['kabam_key_override'])
        except TitleError as e:
            missing.append(e.champ)
    if missing:
        await bot.say("Skipped Champs due to Kabam Key Errors: {}".format(', '.join(missing)))

gapi_service_creds = "data/mcoc/mcoc_service_creds.json"
gsheet_files = {
    'signature': {'gkey': '1kNvLfeWSCim8liXn6t0ksMAy5ArZL5Pzx4hhmLqjukg',
            'local': local_files['signature'],
            'postprocess': postprocess_sig_data,
            },
    'sig_coeff_4star': {'gkey': '1WrAj9c41C4amzP8-jY-QhyKurO8mIeclk9C1pSvmWsk',
            'local': local_files['sig_coeff_4star'],
            },
    'sig_coeff_5star': {'gkey': '1VHi9MioEGAsLoZneYQm37gPkmbD8mx7HHa-zuMiwWns',
            'local': local_files['sig_coeff_5star'],
            },
    #'spotlight': {'gkey': '1I3T2G2tRV05vQKpBfmI04VpvP5LjCBPfVICDmuJsjks',
            #'local': 'data/mcoc/spotlight_test.json',
            #},
    #'crossreference': {'gkey': '1WghdD4mfchduobH0me4T6IvhZ-owesCIyLxb019744Y',
            #'local': 'data/mcoc/xref_test.json',
            #},
    'synergy': {'gkey': '1Apun0aUcr8HcrGmIODGJYhr-ZXBCE_lAR7EaFg_ZJDY',
            'local': local_files['synergy'],
            },
}

star_glyph = "★"
lolmap_path="data/mcoc/maps/lolmap.png"
file_checks_json = "data/mcoc/file_checks.json"
remote_data_basepath = "https://raw.githubusercontent.com/JasonJW/mcoc-cogs/master/mcoc/data/"
icon_sdf = "https://raw.githubusercontent.com/JasonJW/mcoc-cogs/master/mcoc/data/sdf_icon.png"

###### KEYS for MCOC JSON Data Extraction
mcoc_dir="data/mcoc/json/snapshots/en/"
kabam_bio = mcoc_dir + "character_bios_en.json"
kabam_special_attacks = mcoc_dir+"special_attacks_en.json"
kabam_bcg_stat_en = mcoc_dir+"bcg_stat_en.json"
kabam_bcg_en= mcoc_dir+"bcg_en.json"
kabam_masteries=mcoc_dir+"masteries_en.json"
ability_desc = "data/mcoc/ability-desc/{}.txt"
##### Special attacks require:
## mcoc_files + mcoc_special_attack + <champ.mcocjson> + {"_0","_1","_2"} ---> Special Attack title
#mcoc_special_attack="ID_SPECIAL_ATTACK_"
## mcoc_files mcoc_special_attack_desc + <champ.mcocjson> + {"_0","_1","_2"} ---> Special Attack Short description
#mcoc_special_attack_desc="ID_SPECIAL_ATTACK_DESCRIPTION_"


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

class MODOKError(QuietUserError):
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
                             |(?:(?P<star>[1-6])(?:★|☆|\\?\*))
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
            #await bot.say(err_str)
            #raise commands.BadArgument(err_str)
            raise MODOKError(err_str)
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
                #await bot.say(err_str)
                #raise commands.BadArgument(err_str)
                raise MODOKError(err_str)
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

async def warn_bold_say(bot, msg):
    await bot.say('\u26a0 ' + chat.bold(msg))

def numericise_bool(val):
    if val == "TRUE":
        return True
    elif val == "FALSE":
        return False
    else:
        return numericise(val)

def strip_and_numericise(val):
        return numericise_bool(val.strip())

def cell_to_list(cell):
    return [strip_and_numericise(i) for i in cell.split(',')] if cell is not None else None

def cell_to_dict(cell):
    if cell is None:
        return None
    ret  = {}
    for i in cell.split(','):
        k, v = [strip_and_numericise(j) for j in i.split(':')]
        ret[k] = v
    return ret

def remove_commas(cell):
    return numericise_bool(cell.replace(',', ''))

def remove_NA(cell):
    return None if cell in ("#N/A", "") else numericise_bool(cell)

class GSExport():

    default_settings = {
                'sheet_name': None,
                'sheet_action': 'file',
                'data_type': 'dict',
                'range': None,
                'include_empty': False,
                'column_handler': None,
                'row_handler': None,
                'rc_priority': 'column',
                'postprocess': None,
                'prepare_function': 'numericise_bool',
            }
    default_cell_handlers = (
                'cell_to_list',
                'cell_to_dict',
                'remove_commas',
                'remove_NA',
                'numericise',
                'numericise_bool'
            )
    cell_handler_aliases = {
                'to_list': 'cell_to_list',
                'to_dict': 'cell_to_dict',
            }

    def __init__(self, bot, gc, *, name, gkey, local, **kwargs):
        self.bot = bot
        self.gc = gc
        self.name = name
        self.gkey = gkey
        self.local = local
        self.meta_sheet = kwargs.pop('meta_sheet', 'meta_sheet')
        self.settings = self.default_settings.copy()
        self.settings.update(kwargs)
        self.data = defaultdict(partial(defaultdict, dict))
        self.cell_handlers = {}
        module_namespace = globals()
        for handler in self.default_cell_handlers:
            self.cell_handlers[handler] = module_namespace[handler]
        for alias, handler in self.cell_handler_aliases.items():
            self.cell_handlers[alias] = module_namespace[handler]

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
                [record.update(((k,v),)) for k,v in self.settings.items() if k not in record or not record[k]]
                await self.retrieve_sheet(ss, **record)
        else:
            await self.retrieve_sheet(ss, **self.settings)

        if self.settings['postprocess']:
            try:
                await self.settings['postprocess'](self.bot, self.data)
            except Exception as err:
                await self.bot.say("Runtime Error in postprocess of Spreadsheet "
                        "'{}':\n\t{}".format( self.name, err))
                raise
        if self.local:
            dataIO.save_json(self.local, self.data)
        return self.data

    async def retrieve_sheet(self, ss, *, sheet_name, sheet_action, data_type, **kwargs):
        sheet_name, sheet = await self._resolve_sheet_name(ss, sheet_name)
        data = self.get_sheet_values(sheet, kwargs)
        header = data[0]

        if data_type.startswith('nested_list'):
            data_type, dlen = data_type.rsplit('::', maxsplit=1)
            dlen = int(dlen)
        #prep_func = self.cell_handlers[kwargs['prepare_function']]
        prep_func = self.get_prepare_function(kwargs)
        self.data['_headers'][sheet_name] = header
        col_handlers = self._build_column_handlers(sheet_name, header,
                            kwargs['column_handler'])
        if sheet_action == 'table':
            self.data[sheet_name] = [header]
        for row in data[1:]:
            clean_row = self._process_row(header, row, col_handlers, prep_func)
            rkey = clean_row[0]
            if sheet_action == 'merge':
                if data_type == 'nested_dict':
                    pack = dict(zip(header[2:], clean_row[2:]))
                    self.data[rkey][sheet_name][clean_row[1]] = pack
                    continue
                if data_type == 'list':
                    pack = clean_row[1:]
                elif data_type == 'dict':
                    pack = dict(zip(header[1:],clean_row[1:]))
                elif data_type == 'nested_list':
                    if len(clean_row[1:]) < dlen or not any(clean_row[1:]):
                        pack = None
                    else:
                        pack = [clean_row[i:i+dlen] for i in range(1, len(clean_row), dlen)]
                else:
                    await self.bot.say("Unknown data type '{}' for worksheet '{}' in spreadsheet '{}'".format(
                            data_type, sheet_name, self.name))
                    return
                self.data[rkey][sheet_name] = pack
            elif sheet_action in ('dict', 'file'):
                if data_type == 'list':
                    pack = clean_row[1:]
                elif data_type == 'dict':
                    pack = dict(zip(header, clean_row))
                if data_type == 'nested_dict':
                    pack = dict(zip(header[2:], clean_row[2:]))
                    self.data[sheet_name][rkey][clean_row[1]] = pack
                elif sheet_action == 'dict':
                    self.data[sheet_name][rkey] = pack
                elif sheet_action == 'file':
                    self.data[rkey] = pack
            elif sheet_action == 'list':
                if data_type == 'list':
                    pack = clean_row[0:]
                elif data_type == 'dict':
                    pack = dict(zip(header, clean_row))
                if sheet_name not in self.data:
                    self.data[sheet_name] = []
                self.data[sheet_name].append(pack)
            elif sheet_action == 'table':
                self.data[sheet_name].append(clean_row)
            else:
                raise KeyError("Unknown sheet_action '{}' for worksheet '{}' in spreadsheet '{}'".format(
                            sheet_action, sheet_name, self.name))

    async def _resolve_sheet_name(self, ss, sheet_name):
        if sheet_name:
            try:
                sheet = ss.worksheet('title', sheet_name)
            except pygsheets.WorksheetNotFound:
                await self.bot.say("Cannot find worksheet '{}' in Spreadsheet '{}' ({})".format(
                        sheet_name, ss.title, ss.id))
        else:
            sheet = ss.sheet1
            sheet_name = sheet.title
        return sheet_name, sheet

    def _process_row(self, header, row, col_handlers, prep_func):
        clean_row = [row[0]]
        # don't process first column.  Can't use list, dicts, or numbers as keys in json
        for cell_head, cell, c_hand in zip(header[1:], row[1:], col_handlers[1:]):
            if c_hand:
                clean_row.append(c_hand(cell))
            else:
                clean_row.append(prep_func(cell))
        return clean_row

    def get_prepare_function(self, kwargs):
        prep_func = kwargs['prepare_function']
        prep_list = cell_to_list(prep_func)
        if prep_list[0] == prep_func:  # single prep
            return self.cell_handlers[prep_func]

        #  multiple prep
        handlers = [self.cell_handlers[i] for i in prep_list]
        def _curried(x):
            ret = x
            for func in handlers:
                ret = func(ret)
            return ret
        return _curried

    def get_sheet_values(self, sheet, kwargs):
        if kwargs['range']:
            rng = self.bound_range(sheet, kwargs['range'])
            data = sheet.get_values(*rng, returnas='matrix',
                    include_empty=kwargs['include_empty'])
        else:
            data = sheet.get_all_values(include_empty=kwargs['include_empty'])
        return data

    def _build_column_handlers(self, sheet_name, header, column_handler_str):
        if not column_handler_str:
            return [None] * len(header)
        col_handler = cell_to_dict(column_handler_str)
        #print(col_handler)

        #  Column Header check
        invalid = set(col_handler.keys()) - set(header)
        if invalid:
            raise ValueError("Undefined Columns in column_handler for sheet "
                    + "'{}':\n\t{}".format(sheet_name, ', '.join(invalid)))
        #  Callback Cell Handler check
        invalid = set(col_handler.values()) - set(self.cell_handlers.keys())
        if invalid:
            raise ValueError("Undefined CellHandler in column_handler for sheet "
                    + "'{}':\n\t{}".format(sheet_name, ', '.join(invalid)))

        handler_funcs = []
        for column in header:
            if column not in col_handler:
                handler_funcs.append(None)
            else:
                handler_funcs.append(self.cell_handlers[col_handler[column]])
        return handler_funcs

    @staticmethod
    def bound_range(sheet, rng_str):
        rng = rng_str.split(':')
        rows = (1, sheet.rows)
        for i in range(2):
            if not rng[i][-1].isdigit():
                rng[i] = '{}{}'.format(rng[i], rows[i])
        return rng


class GSHandler:

    def __init__(self, bot, service_file):
        self.bot = bot
        self.service_file = service_file
        self.gsheets = {}

    def register_gsheet(self, *, name, gkey, local, **kwargs):
        if name in self.gsheets:
            raise KeyError("Key '{}' has already been registered".format(name))
        self.gsheets[name] = dict(gkey=gkey, local=local, **kwargs)

    async def cache_gsheets(self, key=None):
        gc = await self.authorize()
        if key and key not in self.gsheets:
            raise KeyError("Key '{}' is not registered".format(key))
        gfiles = self.gsheets.keys() if not key else (key,)

        num_files = len(gfiles)
        msg = await self.bot.say('Pulled Google Sheet data 0/{}'.format(num_files))
        for i, k in enumerate(gfiles):
            gsdata = GSExport(self.bot, gc, name=k, **self.gsheets[k])
            try:
                await gsdata.retrieve_data()
            except:
                await self.bot.say("Error while pulling '{}'".format(k))
                raise
            msg = await self.bot.edit_message(msg,
                    'Pulled Google Sheet data {}/{}'.format(i+1, num_files))
        await self.bot.say('Retrieval Complete')

    async def authorize(self):
        try:
            return pygsheets.authorize(service_file=self.service_file, no_cache=True)
        except FileNotFoundError:
            err_msg = 'Cannot find credentials file.  Needs to be located:\n' \
                    + self.service_file
            await self.bot.say(err_msg)
            raise FileNotFoundError(err_msg)


class AliasDict(UserDict):
    '''Custom dictionary that uses a tuple of aliases as key elements.
    Item addressing is handled either from the tuple as a whole or any
    element within the tuple key.
    '''
    def __getitem__(self, key):
        if key in self.data:
            return self.data[key]
        for k in self.data.keys():
            if key in k:
                return self.data[k]
        raise KeyError("Invalid Key '{}'".format(key))

class ChampionFactory():
    '''Creation and storage of the dynamically created Champion subclasses.
    A new subclass is created for every champion defined.  Then objects are
    created from user function calls off of the dynamic classes.'''

    def __init__(self, *args, **kwargs):
        self.cooldown_delta = 5 * 60
        self.cooldown = time.time() - self.cooldown_delta - 1
        self.needs_init = True
        super().__init__(*args, **kwargs)
        self.bot.loop.create_task(self.update_local())  # async init
        logger.debug('ChampionFactory Init')

    def data_struct_init(self):
        logger.info('Preparing data structures')
        self._prepare_aliases()
        self._prepare_prestige_data()
        self.needs_init = False

    async def update_local(self):
        now = time.time()
        if now - self.cooldown_delta < self.cooldown:
            return
        self.cooldown = now
        is_updated = await self.verify_cache_remote_files()
        if is_updated or self.needs_init:
            self.data_struct_init()

    def create_champion_class(self, bot, alias_set, **kwargs):
        if not kwargs['champ'.strip()]: #empty line
            return
        kwargs['bot'] = bot
        kwargs['alias_set'] = alias_set
        kwargs['klass'] = kwargs.pop('class', 'default')

        if not kwargs['champ'].strip():  #empty line
            return
        kwargs['full_name'] = kwargs['champ']
        kwargs['bold_name'] = chat.bold(' '.join(
                [word.capitalize() for word in kwargs['full_name'].split(' ')]))
        kwargs['class_color'] = class_color_codes[kwargs['klass']]
        kwargs['class_icon'] = class_emoji[kwargs['klass']]

        kwargs['class_tags'] = {'#' + kwargs['klass'].lower()}
        for a in kwargs['abilities'].split(','):
            kwargs['class_tags'].add('#' + ''.join(a.lower().split(' ')))
        for a in kwargs['hashtags'].split('#'):
            kwargs['class_tags'].add('#' + ''.join(a.lower().split(' ')))
        for a in kwargs['extended_abilities'].split(','):
            kwargs['class_tags'].add('#' + ''.join(a.lower().split(' ')))
        for a in kwargs['counters'].split(','):
            kwargs['class_tags'].add('#!' + ''.join(a.lower().split(' ')))
        if kwargs['class_tags']:
            kwargs['class_tags'].difference_update({'#'})

        for key, value in kwargs.items():
            if not value or value == 'n/a':
                kwargs[key] = None

        champion = type(kwargs['mattkraftid'], (Champion,), kwargs)
        self.champions[tuple(alias_set)] = champion
        logger.debug('Creating Champion class {}'.format(kwargs['mattkraftid']))
        return champion

    async def get_champion(self, name_id, attrs=None):
        '''straight alias lookup followed by new champion object creation'''
        #await self.update_local()
        return self.champions[name_id](attrs)

    async def search_champions(self, search_str, attrs=None):
        '''searching through champion aliases and allowing partial matches.
        Returns an array of new champion objects'''
        #await self.update_local()
        re_str = re.compile(search_str)
        champs = []
        for champ in self.champions.values():
            if any([re_str.search(alias) is not None
                    for alias in champ.alias_set]):
                champs.append(champ(attrs))
        return champs

    async def verify_cache_remote_files(self, verbose=False, force_cache=False):
        logger.info('Check remote files')
        if os.path.exists(file_checks_json):
            try:
                file_checks = dataIO.load_json(file_checks_json)
            except:
                file_checks = {}
        else:
            file_checks = {}
        async with aiohttp.ClientSession() as s:
            is_updated = False
            for key in data_files.keys():
                if key in file_checks:
                    last_check = datetime(*file_checks.get(key))
                else:
                    last_check = None
                remote_check = await self.cache_remote_file(key, s, verbose=verbose,
                        last_check=last_check)
                if remote_check:
                    is_updated = True
                    file_checks[key] = remote_check.timetuple()[:6]
        dataIO.save_json(file_checks_json, file_checks)
        return is_updated

    async def cache_remote_file(self, key, session, verbose=False, last_check=None,
                force_cache=False):
        dargs = data_files[key]
        strf_remote = '%a, %d %b %Y %H:%M:%S %Z'
        response = None
        remote_check = False
        now = datetime.now()
        if os.path.exists(dargs['local']) and not force_cache:
            if last_check:
                check_marker = now - timedelta(days=dargs['update_delta'])
                refresh_remote_check = check_marker > last_check
            else:
                refresh_remote_check = True
            local_dt = datetime.fromtimestamp(os.path.getmtime(dargs['local']))
            if refresh_remote_check:
                response = await session.get(dargs['remote'])
                if 'Last-Modified' in response.headers:
                    remote_dt = datetime.strptime(response.headers['Last-Modified'], strf_remote)
                    remote_check = now
                    if remote_dt < local_dt:
                        # Remote file is older, so no need to transfer
                        response = None
        else:
            response = await session.get(dargs['remote'])
        if response and response.status == 200:
            logger.info('Caching ' + dargs['local'])
            with open(dargs['local'], 'wb') as fp:
                fp.write(await response.read())
            remote_check = now
            await response.release()
        elif response:
            err_str = "HTTP error code {} while trying to Collect {}".format(
                    response.status, key)
            logger.error(err_str)
            await response.release()
        elif verbose and remote_check:
            logger.info('Local file up-to-date:', dargs['local'], now)
        return remote_check

    def _prepare_aliases(self):
        '''Create a python friendly data structure from the aliases json'''
        logger.debug('Preparing aliases')
        self.champions = AliasDict()
        raw_data = load_csv(data_files['crossreference']['local'])
        punc_strip = re.compile(r'[\s)(-]')
        champs = []
        all_aliases = set()
        id_index = raw_data.fieldnames.index('status')
        alias_index = raw_data.fieldnames[:id_index]
        for row in raw_data:
            if all([not i for i in row.values()]):
                continue    # empty row check
            alias_set = set()
            for col in alias_index:
                if row[col]:
                    alias_set.add(row[col].lower())
            alias_set.add(punc_strip.sub('', row['champ'].lower()))
            if all_aliases.isdisjoint(alias_set):
                all_aliases.union(alias_set)
            else:
                raise KeyError("There are aliases that conflict with previous aliases."
                        + "  First occurance with champ {}.".format(row['champ']))
            self.create_champion_class(self.bot, alias_set, **row)

    def _prepare_prestige_data(self):
        logger.debug('Preparing prestige')
        mattkraft_re = re.compile(r'(?P<star>\d)-(?P<champ>.+)-(?P<rank>\d)')
        with open(data_files['prestigeCSV']['local'], newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                champ_match = mattkraft_re.fullmatch(row.pop(0))
                if not champ_match:
                    continue
                name = champ_match.group('champ')
                star = int(champ_match.group('star'))
                rank = int(champ_match.group('rank'))

                champ = self.champions.get(name)
                if not champ:
                    logger.info('Skipping ' + name)
                    continue

                sig_len = 201 if star >= 5 else 100
                sig = [0] * sig_len
                for i, v in enumerate(row):
                    try:
                        if v and i < sig_len:
                            sig[i] = int(v)
                    except:
                        print(name, i, v, len(sig))
                        raise
                if not hasattr(champ, 'prestige_data'):
                    champ.prestige_data = {4: [None] * 5, 5: [None] * 5,6: [None] * 5, 3: [None] * 4, 2: [None]*3, 1: [None]*2}
                try:
                    champ.prestige_data[star][rank-1] = sig
                except:
                    print(name, star, rank, len(champ.prestige_data),
                            len(champ.prestige_data[star]))
                    raise

def command_arg_help(**cmdkwargs):
    def internal_func(f):
        helps = []
        for param in inspect.signature(f).parameters.values():
            if issubclass(param.annotation, commands.Converter):
                arg_help = getattr(param.annotation, 'arg_help')
                if arg_help is not None:
                    helps.append(arg_help)
        if helps:
            if f.__doc__:
                helps.insert(0, f.__doc__)
            f.__doc__ = '\n'.join(helps)
        @wraps(f)
        async def wrapper(*args, **kwargs):
            return await f(*args, **kwargs)
        return commands.command(**cmdkwargs)(wrapper)
    return internal_func

class MCOC(ChampionFactory):
    '''A Cog for Marvel's Contest of Champions'''

    def __init__(self, bot):
        self.bot = bot

        self.settings = {
                'siglvl': 1,
                'sigstep': 20,
                'table_width': 9,
                'sig_inc_zero': False,
                }
        self.data_dir="data/mcoc/{}/"
        self.shell_json=self.data_dir + "{}.json"
        self.split_re = re.compile(', (?=\w+:)')
        self.gsheet_handler = GSHandler(bot, gapi_service_creds)
        self.gsheet_handler.register_gsheet(
                name='signature',
                gkey='1kNvLfeWSCim8liXn6t0ksMAy5ArZL5Pzx4hhmLqjukg',
                local=local_files['signature'],
                postprocess=postprocess_sig_data,
            )
        self.gsheet_handler.register_gsheet(
                name='sig_coeff_4star',
                gkey='1WrAj9c41C4amzP8-jY-QhyKurO8mIeclk9C1pSvmWsk',
                local=local_files['sig_coeff_4star'],
            )
        self.gsheet_handler.register_gsheet(
                name='sig_coeff_5star',
                gkey='1VHi9MioEGAsLoZneYQm37gPkmbD8mx7HHa-zuMiwWns',
                local=local_files['sig_coeff_5star'],
            )
        self.gsheet_handler.register_gsheet(
                name='synergy',
                gkey='1Apun0aUcr8HcrGmIODGJYhr-ZXBCE_lAR7EaFg_ZJDY',
                local=local_files['synergy'],
            )
    #'spotlight': {'gkey': '1I3T2G2tRV05vQKpBfmI04VpvP5LjCBPfVICDmuJsjks',
            #'local': 'data/mcoc/spotlight_test.json',
            #},
    #'crossreference': {'gkey': '1WghdD4mfchduobH0me4T6IvhZ-owesCIyLxb019744Y',
            #'local': 'data/mcoc/xref_test.json',
            #},

        logger.info("MCOC Init")
        super().__init__()

    @commands.command(aliases=('p2f',), hidden=True)
    async def per2flat(self, per: float, ch_rating: int=100):
        '''Convert Percentage to MCOC Flat Value'''
        await self.bot.say(to_flat(per, ch_rating))

    @commands.command(name='flat') #, aliases=('f2p')) --> this was translating as "flat | f | 2 | p"
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

    @commands.command(aliases=('update_mcoc','mu','um',), hidden=True)
    async def mcoc_update(self, fname, force=False):
        if len(fname) > 3:
            for key in data_files.keys():
                if key.startswith(fname):
                    fname = key
                    break
        if fname in data_files:
            async with aiohttp.ClientSession() as s:
                await self.cache_remote_file(fname, s, force_cache=True, verbose=True)
        else:
            await self.bot.say('Valid options for 1st argument are one of (or initial portion of)\n\t'
                    + '\n\t'.join(data_files.keys()))
            return

        self.data_struct_init()
        await self.bot.say('Summoner, I have Collected the data')

    async def say_user_error(self, msg):
        em = discord.Embed(color=discord.Color.gold(), title=msg)
        await self.bot.say(embed=em)

    @commands.command(hidden=True)
    async def mcocset(self, setting, value):
        if setting in self.settings:
            self.settings[setting] = int(value)

    @commands.command(hidden=True, aliases=['cg',])
    async def cache_gsheets(self, key=None):
         await self.update_local()
         await self.gsheet_handler.cache_gsheets(key)
    #     try:
    #         gc = pygsheets.authorize(service_file=gapi_service_creds, no_cache=True)
    #     except FileNotFoundError:
    #         await self.bot.say('Cannot find credentials file.  Needs to be located:\n'
    #                 + gapi_service_creds)
    #         return
    #     num_files = len(gsheet_files)
    #     msg = await self.bot.say('Pulled Google Sheet data 0/{}'.format(num_files))
    #     for i, k in enumerate(gsheet_files.keys()):
    #         await self.retrieve_gsheet(k, gc)
    #         msg = await self.bot.edit_message(msg,
    #                 'Pulled Google Sheet data {}/{}'.format(i+1, num_files))
    #     await self.bot.say('Retrieval Complete')
    #
    # async def retrieve_gsheet(self, key, gc=None, silent=True):
    #     if gc is None:
    #         gc = pygsheets.authorize(service_file=gapi_service_creds, no_cache=True)
    #     if not silent:
    #         msg = await self.bot.say('Pulling Google Sheet for {}'.format(key))
    #     gsdata = GSExport(self.bot, gc, name=key, **gsheet_files[key])
    #     await gsdata.retrieve_data()
    #     if not silent:
    #         await self.bot.edit_message(msg, 'Downloaded Google Sheet for {}'.format(key))

    @commands.command(pass_context=True, aliases=['modok',], hidden=True)
    async def modok_says(self, ctx, *, word:str = None):
        await self.bot.delete_message(ctx.message)
        await raw_modok_says(self.bot, ctx.message.channel, word)

    # @checks.admin_or_permissions(manage_server=True)
    @commands.command(pass_context=True, aliases=['nbs',], hidden=True)
    async def nerfbuffsell(self, ctx):
        '''Random draw of 3 champions.
        Choose one to Nerf, one to Buff, and one to Sell'''
        colors=[discord.Color.teal(), discord.Color.dark_teal(),
                discord.Color.green(), discord.Color.dark_green(),
                discord.Color.blue(), discord.Color.dark_blue(),
                discord.Color.purple(), discord.Color.dark_purple(),
                discord.Color.magenta(), discord.Color.dark_magenta(),
                discord.Color.gold(), discord.Color.dark_gold(),
                discord.Color.orange(), discord.Color.dark_orange(),
                discord.Color.red(), discord.Color.dark_red(),
                discord.Color.lighter_grey(), discord.Color.dark_grey(),
                discord.Color.light_grey(), discord.Color.darker_grey()]
        rcolor=random.choice(colors)
        selected = []
        embeds = []
        emojis = ['🇳', '🇧', '🇸']
        em1 = discord.Embed(color=rcolor, title='Nerf, Buff, or Sell', description='')
        em2 = discord.Embed(color=rcolor, description='',
                title='Select one to Nerf, one to Buff, and one to Sell. Explain your choices',
            )

        while len(selected) < 3:
            name_id = random.choice(list(self.champions.values()))
            champ = await self.get_champion(name_id.mattkraftid)
            if champ not in selected:
                if champ.status == 'released':
                    selected.append(champ)
                    em = discord.Embed(color=champ.class_color, title=champ.full_name)
                    em.set_thumbnail(url=champ.get_avatar())
                    embeds.append(em)
        try:
            await self.bot.say(embed=em1)
            for em in embeds:
                message = await self.bot.say(embed=em)
                for emoji in emojis:
                    await self.bot.add_reaction(message=message, emoji=emoji)
                    # await asyncio.sleep(1)
            await self.bot.say(embed=em2)
        except:
            await self.bot.say('\n'.join(s.full_name for s in selected))

    @commands.group(pass_context=True, aliases=['champs',])
    async def champ(self, ctx):
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @champ.command(name='featured',aliases=['feature',])
    async def champ_featured(self, *, champs : ChampConverterMult):
        '''Champion Featured image'''
        for champ in champs:
            em = discord.Embed(color=champ.class_color, title=champ.full_name)
            em.set_author(name=champ.full_name + ' - ' + champ.short, icon_url=champ.get_avatar())
            em.set_image(url=champ.get_featured())
            await self.bot.say(embed=em)

    @champ.command(name='portrait', aliases=['avatar',])
    async def champ_portrait(self, *, champs : ChampConverterMult):
        '''Champion portraits'''
        for champ in champs:
            em = discord.Embed(color=champ.class_color, title=champ.full_name)
            em.set_author(name=champ.full_name + ' - ' + champ.short, icon_url=champ.get_avatar())
            em.set_image(url=champ.get_avatar())
            print(champ.get_avatar())
            await self.bot.say(embed=em)

    @champ.command(name='bio', aliases=('biography',))
    async def champ_bio(self, *, champ : ChampConverterDebug):
        '''Champio Bio'''
        try:
            bio_desc = await champ.get_bio()
        except KeyError:
            await self.say_user_error("Cannot find bio for Champion '{}'".format(champ.full_name))
            return
        em = discord.Embed(color=champ.class_color, title='Champion Biography',
                description=bio_desc)
        em.set_author(name='{0.full_name}'.format(champ), icon_url=champ.get_avatar())
        em.add_field(name='hashtags',
                value=chat.box(' '.join(champ.class_tags.union(champ.tags))),inline=False)
        em.add_field(name='Shortcode', value=champ.short,inline=False)
        em.set_thumbnail(url=champ.get_avatar())
        em.set_footer(text='MCOC Game Files', icon_url='https://imgur.com/UniRf5f.png')
        await self.bot.say(embed=em)

    @champ.command(name='duel')
    async def champ_duel(self, champ : ChampConverter):
        '''Duel & Spar Targets'''
        #dataset=data_files['duelist']['local']
        gc = pygsheets.authorize(service_file=gapi_service_creds, no_cache=True)
        sh = gc.open_by_key('1FZdJPB8sayzrXkE3F2z3b1VzFsNDhh-_Ukl10OXRN6Q')
        ws = sh.worksheet('title', 'DataExport')
        data = ws.get_all_records()
        if not len(data):
            await self.bot.say("Data did not get retrieved")
            raise IndexError

        DUEL_SPREADSHEET='https://docs.google.com/spreadsheets/d/1FZdJPB8sayzrXkE3F2z3b1VzFsNDhh-_Ukl10OXRN6Q/view#gid=61189525'
        em = discord.Embed(color=champ.class_color, title='Duel & Spar Targets',url=DUEL_SPREADSHEET)
        em.set_author(name='{0.full_name}'.format(champ), icon_url=champ.get_avatar())
        em.set_thumbnail(url=champ.get_featured())
        em.set_footer(text='2OO2RC51\' Duel Targets',
                icon_url=GSHEET_ICON)

        targets = []
        for duel in data:    # single iteration through the data
            uniq = duel['unique']
            star, duel_champ, rank = int(uniq[:1]), uniq[2:-2], int(uniq[-1:])
            if duel_champ == champ.full_name:
                targets.append('{}{} {} {} : {}'.format(star, champ.star_char,
                            duel['maxlevel'],
                            champ.full_name,
                            duel['username']))
        targets.sort()
        #for star in range(3,7):
            #for rank in range(1,6):
                #key = '{0}-{1}-{2}'.format(star, champ.full_name, rank)
                #for data in get_csv_rows(dataset, 'unique', key):#champ.unique):
                    #targets.append( '{}{} {} {} : {}'.format(star, champ.star_char, data['maxlevel'], champ.full_name, data['username']))
        if len(targets) > 0:
            em.description='\n'.join(targets)
        else:
            em.description='Target not found!\nAdd one to the Community Spreadhseet!\n[bit.ly/DuelTargetForm](http://bit.ly/DuelTargetForm)'
            em.url='http://bit.ly/DuelTargetForm'
        em.add_field(name='Shortcode', value=champ.short, inline=False)
        await self.bot.say(embed=em)

    @champ.command(name='about', aliases=('about_champ',))
    async def champ_about(self, *, champ : ChampConverterRank):
        '''Champion Base Stats'''
        data = champ.get_spotlight(default='x')
        title = 'Base Attributes for {}'.format(champ.verbose_str)
        em = discord.Embed(color=champ.class_color,
                title='Base Attributes')
        em.set_author(name=champ.verbose_str, icon_url=champ.get_avatar())
        titles = ('Health', 'Attack', 'Crit Rate', 'Crit Dmg', 'Armor', 'Block Prof')
        keys = ('health', 'attack', 'critical', 'critdamage', 'armor', 'blockprof')
        xref = get_csv_row(data_files['crossreference']['local'],'champ',champ.full_name)

        if champ.debug:
            em.add_field(name='Attrs', value='\n'.join(titles))
            em.add_field(name='Values', value='\n'.join([data[k] for k in keys]), inline=True)
            em.add_field(name='Added to PHC', value=xref['4basic'])
        else:
            stats = [[titles[i], data[keys[i]]] for i in range(len(titles))]
            em.add_field(name='Base Stats',
                value=tabulate(stats, width=11, rotate=False, header_sep=False))
        em = await self.get_synergies([champ], em)
        if champ.infopage != 'none':
            em.add_field(name='Infopage',value='<{}>'.format(champ.infopage),inline=False)
        else:
            em.add_field(name='Infopage',value='No spotlight post from Kabam',inline=False)
            em.add_field(name='hashtags',
                    value=chat.box(' '.join(champ.class_tags.union(champ.tags))))
        em.add_field(name='Shortcode', value=champ.short)
        em.set_footer(text='CollectorDevTeam Dataset', icon_url=COLLECTOR_ICON)
        em.set_thumbnail(url=champ.get_avatar())
        await self.bot.say(embed=em)

    @champ.command(pass_context=True, name='list')
    async def champ_list(self, ctx, *, hargs=''):
        '''List of all champions in prestige order.

        hargs:  [attribute_args] [hashtags]
        The optional attribute arguments can be in any order, with or without spaces.
            <digit>* specifies star <default: 4>
            r<digit> specifies rank <default: 5>
            s<digit> specifies signature level <default: 99>

        Examples:
            /champ list    (all 4* champs rank5, sig99)
            /champ list 5*r3s20 #bleed   (all 5* bleed champs at rank3, sig20)
        '''
        hargs = await hook.HashtagRankConverter(ctx, hargs).convert() #imported from hook
        #await self.update_local()
        roster = hook.ChampionRoster(self.bot, self.bot.user) #imported from hook
        rlist = []
        for champ_class in self.champions.values():
            champ = champ_class(hargs.attrs.copy())
            if champ.has_prestige:
                rlist.append(champ)
        roster.from_list(rlist)
        roster.display_override = 'Prestige Listing: {0.attrs_str}'.format(rlist[0])
        await roster.display(hargs.tags) #imported from hook

    @champ.command(name='released', aliases=('odds','chances',))
    async def champ_released(self, *, champs : ChampConverterMult):
        '''Champion(s) Release Date'''
        for champ in champs:
            xref = get_csv_row(data_files['crossreference']['local'],'champ',champ.full_name)
            em=discord.Embed(color=champ.class_color, title='Release Date & Estimated Pull Chance', url=SPOTLIGHT_DATASET)
            em.set_author(name=champ.full_name, icon_url=champ.get_avatar())
            daily4 = 0.10
            daily3 = 0.30
            daily2 = 0.60
            p2 = 0.84
            p3 = 0.14
            p4 = 0.02
            em.add_field(name='Daily Special Drop Rates', value='2{0.star_char} {1}%\n3{0.star_char} {2}%\n4{0.star_char} {3}%\n'.format(champ, round(daily2*100,0), round(daily3*100,0), round(daily4*100),0))
            em.add_field(name='PHC Drop Rates', value='2{0.star_char} {1}%\n3{0.star_char} {2}%\n4{0.star_char} {3}%\n'.format(champ, round(p2*100,0), round(p3*100,0), round(p4*100),0))
            em.add_field(name='Release Date', value='{0.released}'.format(champ))
            if xref['basic4'] != '':
                em.add_field(name='4{0.star_char} Basic + PHC Date'.format(champ), value='{0}'.format(xref['basic4']), inline=True)
            if float(xref['chanced']) > 0:
                dchance = round(daily4*float(xref['chanced'])*100, 4)
                em.add_field(name='4{0.star_char} {0.klass} Special Odds'.format(champ), value='{0}%'.format(dchance), inline=True)
            if float(xref['chance4']) > 0:
                chance4 = round(float(xref['chance4'])*100,4)
                pchance = round(chance4*p4,4)
                em.add_field(name='PHC 4{0.star_char} Odds'.format(champ), value='{0}%'.format(pchance), inline=True)
                em.add_field(name='4{0.star_char} {1} Odds'.format(champ, xref['4b']), value='{0}%'.format(chance4),inline=True)
            if float(xref['chance5b']) >0 :
                chance5=round(float(xref['chance5b'])*100,4)
                em.add_field(name='5{0.star_char} Basic Odds'.format(champ), value='{0}%'.format(chance5),inline=True)
            if float(xref['chance5f']) >0 :
                chance5=round(float(xref['chance5f'])*100,4)
                em.add_field(name='5{0.star_char} {1} Odds'.format(champ, xref['5f']), value='{0}%'.format(chance5),inline=True)
            if float(xref['chance6b']) >0 :
                chance6=round(float(xref['chance6b'])*100,4)
                em.add_field(name='6{0.star_char} Basic Odds'.format(champ), value='{0}%'.format(chance6),inline=True)
            if float(xref['chance6f']) >0 :
                chance6=round(float(xref['chance6f'])*100,4)
                em.add_field(name='6{0.star_char} Featured Odds'.format(champ), value='{0}%'.format(chance6),inline=True)

            em.add_field(name='Shortcode', value=champ.short, inline=True)
            em.set_thumbnail(url=champ.get_featured())
            em.set_footer(text='CollectorDevTeam Dataset', icon_url=COLLECTOR_ICON)
            await self.bot.say(embed=em)


    @champ.command(pass_context=True, name='sig', aliases=['signature',])
    async def champ_sig(self, ctx, *, champ : ChampConverterSig):
        '''Champion Signature Ability'''
        appinfo = await self.bot.application_info()
        try:
            title, desc, sig_calcs = await champ.process_sig_description(
                    isbotowner=ctx.message.author == appinfo.owner)
        except KeyError:
            await champ.missing_sig_ad()
            raise
            return
        if title is None:
            return
        em = discord.Embed(color=champ.class_color, title='Signature Ability')
        em.set_author(name='{0.full_name}'.format(champ), icon_url=champ.get_avatar())
        em.add_field(name=title, value=champ.star_str)
        em.add_field(name='Signature Level {}'.format(champ.sig),
                value=desc.format(d=sig_calcs))
        em.add_field(name='Shortcode', value=champ.short)
        em.set_footer(text='MCOC Game Files', icon_url='https://imgur.com/UniRf5f.png')
        em.set_thumbnail(url=champ.get_avatar())
        await self.bot.say(embed=em)

    @champ.command(pass_context=True, name='sigplot', hidden=True)
    async def champ_sigplot(self,ctx,*, champ: ChampConverterSig):
        if champ.star <= 4 and champ.star > 1:
            x = 99
        elif champ.star > 4:
            x = 200
        elif champ.star == 1:
            await self.bot.say('1★ champs have no signature ability.')


        try:
            plt.plot([1,2,3,4], [1,4,9,16], 'ro')
            plt.axis([0, 6, 0, 20])
            plt.xlabel('Signature Ability Level')
            plt.ylabel('Signature Ability Effect')
            plt.suptitle('Sig Plot Test')
            # plt.show()
            plt.draw()
            plt.savefig('data/mcoc/sigtemp.png', format='png', dpi=150)
            await self.bot.upload('data/mcoc/sigtemp.png')
        except:
            print('champ_sigplot nothing happened')


    @champ.command(name='stats', aliases=('stat',))
    async def champ_stats(self, *, champs : ChampConverterMult):
        '''Champion(s) Base Stats'''
        for champ in champs:
            data = champ.get_spotlight(default='x')
            embeds =[]
            em = discord.Embed(color=champ.class_color, title='Champion Stats',url=SPOTLIGHT_SURVEY)
            em.set_author(name=champ.verbose_str, icon_url=champ.get_avatar())
            em.set_footer(text='CollectorDevTeam Dataset', icon_url=COLLECTOR_ICON)
            titles = ('Health', 'Attack', 'Crit Rate', 'Crit Dmg', 'Armor Penetration', 'Block Penetration', 'Crit Resistance', 'Armor', 'Block Prof')
            keys = ('health', 'attack', 'critical', 'critdamage', 'armor_pen', 'block_pen', 'crit_resist', 'armor', 'blockprof')
            xref = get_csv_row(data_files['crossreference']['local'],'champ',champ.full_name)
            # if champ.debug:
            #     em.add_field(name='Attrs', value='\n'.join(titles))
            #     em.add_field(name='Values', value='\n'.join([data[k] for k in keys]), inline=True)
            #     em.add_field(name='Added to PHC', value=xref['4basic'])
            # else:
            stats = [[titles[i], data[keys[i]]] for i in range(len(titles))]
            em.add_field(name='Base Stats', value=tabulate(stats, width=18, rotate=False, header_sep=False), inline=False)
            em.add_field(name='Shortcode',value=champ.short)
            # em.set_thumbnail(url=champ.get_featured())
            embeds.append(em)

            em2 = discord.Embed(color=champ.class_color, title='Champion Stats',url=SPOTLIGHT_SURVEY)
            em2.set_author(name=champ.verbose_str, icon_url=champ.get_avatar())
            em2.set_footer(text='CollectorDevTeam Dataset', icon_url=COLLECTOR_ICON)
            # em2.set_thumbnail(url=champ.get_featured())
            flats = []
            flats.append(data[keys[0]])
            flats.append(data[keys[1]])
            flats.append('% {}'.format(from_flat(int(data[keys[2]].replace(',','')), int(champ.chlgr_rating))))
            critdmg=round(0.5+5*from_flat(int(data[keys[3]].replace(',','')), int(champ.chlgr_rating)),2)
            flats.append('% {}'.format(critdmg))
            for k in range(4,len(keys)):
                flats.append('% {}'.format(from_flat(int(data[keys[k]].replace(',','')), int(champ.chlgr_rating))))
            pcts = [[titles[i], flats[i]] for i in range(len(titles))]
            em2.add_field(name='Base Stats %', value=tabulate(pcts, width=19, rotate=False, header_sep=False), inline=False)
            em2.add_field(name='Shortcode', value=champ.short)
            embeds.append(em2)

            try:
                menu = PagesMenu(self.bot, timeout=120, delete_onX=True, add_pageof=True)
                await menu.menu_start(embeds)                # for page in pages:
            except:
                print('PagesMenu failure')
                await self.bot.say(embed=em)

    @champ.command(pass_context=True, name='update', aliases=('add', 'dupe'), hidden=True)
    async def champ_update(self, ctx, *, args):
        '''Not a real command'''
        msg = '`{0}champ update` does not exist.\n' \
            + '`{0}roster update` is probably what you meant to do'
        prefixes = tuple(self.bot.settings.get_prefixes(ctx.message.server))
        await self.bot.say(msg.format(prefixes[0]))

    def set_collectordev_footer(self, pack):
        try:
            for embed in pack:
                embed.set_footer(text='CollectorDevTeam', icon_url=COLLECTOR_ICON)
        except TypeError:
            pack.set_footer(text='CollectorDevTeam', icon_url=COLLECTOR_ICON)

    @champ.command(name='synergies', aliases=['syn',])
    async def champ_synergies(self, *, champs: ChampConverterMult):
        '''Champion(s) Synergies'''
        pack = await self.get_synergies(champs)
        self.set_collectordev_footer(pack)
        menu = PagesMenu(self.bot, timeout=120)
        await menu.menu_start(pack)
        #await self.bot.say(embed=em)

    async def get_synergies(self, champs, embed=None):
        '''If Debug is sent, data will refresh'''
        if champs[0].debug:
            await self.gsheet_handler.cache_gsheets('synergy')
        syn_data = dataIO.load_json(local_files['synergy'])
        if len(champs) > 1:
            return await self.get_multiple_synergies(champs, syn_data, embed)
        elif len(champs) == 1:
            return await self.get_single_synergies(champs[0], syn_data, embed)

    async def get_single_synergies(self, champ, syn_data, embed=None):
        if embed is None:
            embed = discord.Embed(color=champ.class_color, title='')
            embed.set_author(name=champ.star_name_str, icon_url=champ.get_avatar())
            embed.set_thumbnail(url=champ.get_featured())
            return_single = False
        else:
            return_single = True
        champ_synergies = syn_data['SynExport'][champ.full_name]
        for lookup, data in champ_synergies.items():
            if champ.star != data['stars']:
                continue
            syneffect = syn_data['SynergyEffects'][data['synergycode']]
            triggers = data['triggers']
            effect = syneffect['rank{}'.format(data['rank'])]
            try:
                txt = syneffect['text'].format(*effect)
            except:
                print(syneffect['text'], effect)
                raise
            embed.add_field(name='{}'.format(syneffect['synergyname']),
                    value='+ **{}**\n{}\n'.format(', '.join(triggers), txt),
                    inline=False)
        if return_single:
            return embed
        else:
            return [embed]

    async def get_multiple_synergies(self, champs, syn_data, embed=None):
        if embed is None:
            embed = discord.Embed(color=discord.Color.red(),
                            title='Champion Synergies')
            return_single = False
        else:
            return_single = True
        if len(champs) > 5:
            raise MODOKError('No Synergy team can be greater than 5 champs')
        effectsused = defaultdict(list)
        champ_set = {champ.full_name for champ in champs}
        activated = {}
        for champ in champs:
            champ_synergies = syn_data['SynExport'][champ.full_name]
            for lookup, data in champ_synergies.items():
                trigger_in_tag = False
                if champ.star != data['stars']:
                    continue
                for trigger in data['triggers']:
                    if lookup in activated:
                        continue
                    if trigger.startswith('#'):
                        for trig_champ in champs:
                            if champ == trig_champ:
                                continue
                            if trigger in trig_champ.all_tags:
                                trigger_in_tag = True
                                break
                    if trigger in champ_set or trigger_in_tag:
                        syneffect = syn_data['SynergyEffects'][data['synergycode']]
                        activated[lookup] = {
                                'champ': champ,
                                'trigger': next(c for c in champs if c.full_name == trigger),
                                'rank': data['rank'],
                                'emoji': syneffect['emoji'],
                                'synergyname': syneffect['synergyname']
                            }
                        if syneffect['is_unique'] == 'TRUE' and data['synergycode'] in effectsused:
                            continue
                        effect = syneffect['rank{}'.format(data['rank'])]
                        effectsused[data['synergycode']].append(effect)

        desc= []
        try:
            embed.description = ''.join(c.collectoremoji for c in champs)
        except:
            print('Collector Emoji not found')
        for k, v in effectsused.items():
            syn_effect = syn_data['SynergyEffects'][k]
            array_sum = [sum(row) for row in iter_rows(v, True)]
            txt = syn_effect['text'].format(*array_sum)
            if embed is not None:
                embed.add_field(name=syn_effect['synergyname'],
                        value=txt, inline=False)
            else:
                desc.append('{}\n{}\n'.format(syn_effect['synergyname'], txt))
        arrows = '\u2192 \u21d2 \u21a6 <:collectarrow:422077803937267713>'.split()
        sum_txt = '{0[champ].terse_star_str}{0[champ].collectoremoji} ' \
                + '{1} ' \
                + '{0[trigger].terse_star_str}{0[trigger].collectoremoji} ' \
                + '\u2503 Level {0[rank]}'
                #+ '\u2503 {0[synergyname]} Level {0[rank]}'
                #+ '<:collectarrow:422077803937267713> \u21e8 \u2192 \U0001f86a \U0001f87a' \
                #+ 'LVL{0[rank]} {0[emoji]}'
        sum_field = defaultdict(list)
        for v in activated.values():
            arrow = arrows[min(v['champ'].debug, len(arrows)-1)]
            sum_field[v['synergyname']].append(sum_txt.format(v, arrow))
        if return_single:
            return embed
        else:
            pages = [embed]
            embed = discord.Embed(color=discord.Color.red(),
                    title='Champion Synergies',
                    description='**Synergy Breakdown**')
            for syn, lines in sum_field.items():
                embed.add_field(name=syn, value='\n'.join(lines), inline=False)
            #embed.add_field(name='Synergy Breakdown', value='\n'.join(sum_field))
            pages.append(embed)
            return pages

    async def gs_to_json(self, head_url=None, body_url=None, foldername=None, filename=None, groupby_value=None):
        if head_url is not None:
            async with aiohttp.get(head_url) as response:
                try:
                    header_json = await response.json()
                except:
                    print('No header data found.')
                    return
            header_values = header_json['values']

        async with aiohttp.get(body_url) as response:
            try:
                body_json = await response.json()
            except:
                print('No data found.')
                return
        body_values = body_json['values']

        output_dict = {}
        if head_url is not None:
            if groupby_value is None:
                groupby_value = 0
            grouped_by = header_values[0][groupby_value]
            for row in body_values:
                dict_zip = dict(zip(header_values[0],row))
                groupby = row[groupby_value]
                output_dict.update({groupby:dict_zip})
        else:
            output_dict =body_values

        if foldername is not None and filename is not None:
            if not os.path.exists(self.shell_json.format(foldername, filename)):
                if not os.path.exists(self.data_dir.format(foldername)):
                    os.makedirs(self.data_dir.format(foldername))
                dataIO.save_json(self.shell_json.format(foldername, filename), output_dict)
            dataIO.save_json(self.shell_json.format(foldername,filename),output_dict)

            # # Uncomment to debug
            # if champ.debug:
            #     await self.bot.upload(self.shell_json.format(foldername,filename))


        return output_dict

    @commands.command(hidden=True)
    async def dump_sigs(self):
        #await self.update_local()
        sdata = dataIO.load_json(local_files['signature'])
        dump = {}
        for c, champ_class in enumerate(self.champions.values()):
            #if c < 75 or c > 90:
                #continue
            champ = champ_class()
            item = {'name': champ.full_name, 'sig_data': []}
            for i in range(1, 100):
                champ.update_attrs({'sig': i})
                try:
                    title, desc, sig_calcs = await champ.process_sig_description(sdata, quiet=True)
                except (KeyError, IndexError):
                    print("Skipping ", champ.full_name)
                    break
                if sig_calcs is None:
                    break
                if i == 1:
                    item['title'] = title
                    item['description'] = desc
                    item['star_rank'] = champ.star_str
                item['sig_data'].append(sig_calcs)
            if not item['sig_data']:
                continue
            dump[champ.mattkraftid] = item
            print(champ.full_name)
        with open("sig_data_4star.json", encoding='utf-8', mode="w") as fp:
            json.dump(dump, fp, indent='\t', sort_keys=True)
        await self.bot.say('Hopefully dumped')

    @commands.command(hidden=True)
    async def json_sig(self, *, champ : ChampConverterSig):
        if champ.star != 4 or champ.rank != 5:
            await self.bot.say('This function only checks 4* rank5 champs')
            return
        jfile = dataIO.load_json("sig_data_4star.json")
        title, desc, sig_calcs = await champ.process_sig_description(quiet=True)
        jsig = jfile[champ.mattkraftid]
        em = discord.Embed(title='Check for {}'.format(champ.full_name))
        em.add_field(name=jsig['title'],
                value=jsig['description'].format(d=jsig['sig_data'][champ.sig-1]))
        await self.bot.say(embed=em)
        assert title == jsig['title']
        assert desc == jsig['description']
        assert sig_calcs == jsig['sig_data'][champ.sig-1]

    @commands.command(hidden=True)
    async def gs_sig(self):
        await self.update_local()
        gkey = '1kNvLfeWSCim8liXn6t0ksMAy5ArZL5Pzx4hhmLqjukg'
        gc = pygsheets.authorize(service_file=gapi_service_creds, no_cache=True)
        gsdata = GSExport(gc, gkey)
        struct = await gsdata.retrieve_data()
        sigs = load_kabam_json(kabam_bcg_stat_en)
        for key in struct.keys():
            champ_class = self.champions.get(key.lower(), None)
            if champ_class is None:
                continue
            struct[key]['kabam_text'] = champ_class.get_kabam_sig_text(
                    champ_class, sigs=sigs,
                    champ_exceptions=struct['kabam_key_override'])
        with open("data/mcoc/gs_json_test.json", encoding='utf-8', mode='w') as fp:
            json.dump(struct, fp, indent='  ', sort_keys=True)
        await self.bot.upload("data/mcoc/gs_json_test.json")

    @champ.command(name='use', aliases=('howto','htf',))
    async def champ_use(self, *, champs :ChampConverterMult):
        '''How to Fight With videos by MCOC Community'''
        for champ in champs:
            xref = get_csv_row(data_files['crossreference']['local'],'champ',champ.full_name)
            em = discord.Embed(color=champ.class_color, title='How-To-Use: '+champ.full_name, url='https://goo.gl/forms/VXSQ1z40H4Knia0t2')
            await self.bot.say(embed=em)
            if xref['infovideo'] != '':
                await self.bot.say(xref['infovideo'])
            else:
                await self.bot.say('I got nothing. Send the CollectorDevTeam a good video.\nClick the blue text for a survey link.')


    @champ.command(name='info', aliases=('infopage',))
    async def champ_info(self, *, champ : ChampConverterDebug):
        '''Champion Spotlight link'''
        xref = get_csv_row(data_files['crossreference']['local'],'champ',champ.full_name)
        em = discord.Embed(color=champ.class_color, title='Champ Info',url=SPOTLIGHT_SURVEY)
        em.set_author(name='{0.full_name}'.format(champ), icon_url=champ.get_avatar())
        if champ.infopage == 'none':
            em.add_field(name='Kabam Spotlight', value='No URL found')
        else:
            em.add_field(name='Kabam Spotlight', value=champ.infopage)
        if xref['writeup_url'] !='':
            em.add_field(name=xref['writeup'], value=xref['writeup_url'])
        # if xref['royal_writeup'] != '':
        #     em.add_field(name='Royal Writeup', value=xref['royal_writeup'])
        em.add_field(name='Shortcode', value=champ.short)
        em.set_footer(text='MCOC Website', icon_url='https://imgur.com/UniRf5f.png')
        em.set_thumbnail(url=champ.get_avatar())
        await self.bot.say(embed=em)

    @champ.command(name='abilities')
    async def champ_abilities(self, *, champ : ChampConverterDebug):
        '''Champion Abilities'''
        xref=get_csv_row(data_files['crossreference']['local'],'champ',champ.full_name)
        abilities=xref['abilities'].split(', ')
        extended_abilities=xref['extended_abilities']
        counters=xref['counters'].split(', ')
        hashtags=xref['hashtags'].split(' #')
        embeds = []
        if os.path.exists(ability_desc.format(champ.mattkraftid)):
            ability_file = open(ability_desc.format(champ.mattkraftid),"r", encoding='utf-8')
            pages = chat.pagify(text=ability_file.read(), delims=["\n\n"], escape=False, page_length=1500)
            for page in pages:
                # print(page)
                em = discord.Embed(color=champ.class_color, title='Abilities', descritpion='')
                em.add_field(name='Ability Keywords', value=champ.abilities)
                em.set_author(name='Champion #{0.champNumber} : {0.full_name}'.format(champ), icon_url=champ.get_avatar())
                if len(extended_abilities) > 1:
                    em.add_field(name='Extended Keywords', value=extended_abilities, inline=False)
                if len(counters) > 1:
                    em.add_field(name='Counters (#!)', value=', '.join(c.title() for c in counters), inline=False)
                em.add_field(name='Hashtags (#)', value=champ.hashtags, inline=False)
                em.set_thumbnail(url=champ.get_avatar())
                em.set_footer(text='MCOC Game Files', icon_url='https://imgur.com/UniRf5f.png')
                em.description = page
                embeds.append(em)
        appinfo = await self.bot.application_info()
        sigtitle, sigdesc, sig_calcs = await champ.process_sig_description(isbotowner=appinfo.owner)
        if sigtitle is not None:
            em = discord.Embed(color=champ.class_color, title='Signature Ability s{0.sig}: {1}'.format(champ, sigtitle), descritpion='')
            em.description='```'+sigdesc.format(d=sig_calcs)+'```'
            em.add_field(name='Ability Keywords', value=champ.abilities)
            em.set_author(name='#{0.champNumber}: {0.full_name}'.format(champ), icon_url=champ.get_avatar())
            if len(extended_abilities) > 1:
                em.add_field(name='Extended Keywords', value=extended_abilities, inline=False)
            if len(counters) > 1:
                em.add_field(name='Counters (#!)', value=', '.join(c.title() for c in counters), inline=False)
            em.add_field(name='Hashtags (#)', value=champ.hashtags, inline=False)
            em.set_thumbnail(url=champ.get_avatar())
            em.set_footer(text='MCOC Game Files', icon_url='https://imgur.com/UniRf5f.png')
            embeds.append(em)
        # else:
        #     embeds.append(em)
        if len(embeds) > 0:
            menu = PagesMenu(self.bot, timeout=120, delete_onX=True, add_pageof=True)
            await menu.menu_start(embeds)
        else:
            await self.bot.say(embed=em)

    @champ.command(name='specials', aliases=['special',])
    async def champ_specials(self, champ : ChampConverter):
        '''Special Attack Descritpion'''
        try:
            specials = champ.get_special_attacks()
            em = discord.Embed(color=champ.class_color, title='Champion Special Attacks')
            em.set_author(name='{0.full_name}'.format(champ), icon_url=champ.get_avatar())
            em.add_field(name=specials[0], value=specials[3])
            em.add_field(name=specials[1], value=specials[4])
            em.add_field(name=specials[2], value=specials[5])
            em.set_thumbnail(url=champ.get_avatar())
            em.add_field(name='Shortcode', value=champ.short)
            em.set_footer(text='MCOC Game Files', icon_url='https://imgur.com/UniRf5f.png')
            await self.bot.say(embed=em)
        except:
            await self.bot.say('Special Attack not found')
    # @commands.command()
    # async def sigarray(self, champ : ChampConverter, dbg=1, *args):
    #     '''the Signature Ability of a Champion at multiple levels'''
    #     champ = self._resolve_alias(champ)
    #     title, desc = champ.get_sigarray(**self.settings)
    #     if dbg == 0:
    #         em = discord.Embed(color=champ.class_color, title=title,
    #                 description=desc)
    #     elif dbg == 1:
    #         em = discord.Embed(color=champ.class_color, title=champ.full_name)
    #         em.add_field(name='Signature Ability Array', value=desc)
    #     else:
    #         em = discord.Embed(color=champ.class_color, title=title)
    #         em.add_field(name='__SigLvl__', value='1\n20\n40')
    #         em.add_field(name='__X__', value='1.0\n1.9\n2.1', inline=True)
    #
    #     em.set_thumbnail(url=champ.get_avatar())
    #     await self.bot.say(embed=em)

    @champ.command(name='prestige')
    async def champ_prestige(self, *, champs : ChampConverterMult):
        '''Champion(s) Prestige'''
        pch = [c for c in champs if c.has_prestige]
        numerator = 0
        spch = sorted(pch, key=attrgetter('prestige'), reverse=True)
        denom = min(len(spch), 5)
        numerator = sum(spch[i].prestige for i in range(denom))
        em = discord.Embed(color=discord.Color.magenta(),
                title='Prestige: {}'.format(numerator/denom),
                url=PRESTIGE_SURVEY,
                description='\n'.join(c.verbose_prestige_str for c in spch)
            )
        em.set_footer(icon_url=GSHEET_ICON,text='mutamatt Prestige for Collector')
        await self.bot.say(embed=em)

    @champ.command(name='aliases', aliases=('alias',))
    async def champ_aliases(self, *args):
        '''Champion Aliases'''
        em = discord.Embed(color=discord.Color.teal(), title='Champion Aliases')
        champs_matched = set()
        for arg in args:
            arg = arg.lower()
            if (arg.startswith("'") and arg.endswith("'")) or \
                    (arg.startswith('"') and arg.endswith('"')):
                champs = await self.search_champions(arg[1:-1])
            elif '*' in arg:
                champs = await self.search_champions('.*'.join(re.split(r'\\?\*', arg)))
            else:
                champs = await self.search_champions('.*{}.*'.format(arg))
            for champ in champs:
                if champ.mattkraftid not in champs_matched:
                    em.add_field(name=champ.full_name, value=champ.get_aliases())
                    champs_matched.add(champ.mattkraftid)
        await self.bot.say(embed=em)

    @commands.group(hidden=True, pass_context=True, name='datamine',aliases=('dm','datasearch'))
    async def ksearch(self, ctx):
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @ksearch.command(hidden=True, pass_context=True, name='masteries')
    async def ksearch_masteries(self, ctx, term: str = None):
        '''Search for keys or terms within masteries'''
        data =  load_kabam_json(kabam_masteries)
        await self._ksearch_paginate(data, term, None)           # for page in pages:

    @ksearch.command(hidden=True, pass_context=True, name='special_attacks', aliases=['specials'],)
    async def ksearch_special_attacks(self, ctx, term: str = None):
        '''Search for keys or terms within special_attacks'''
        data =  load_kabam_json(kabam_special_attacks)
        await self._ksearch_paginate(data, term, None)           # for page in pages:

    @ksearch.command(hidden=True, pass_context=True, name='bcg_stat_en',aliases=['bcg_stat',])
    async def ksearch_bcg_stat_en(self, ctx, term: str = None):
        '''Search for keys or terms within bcg_stat_en'''
        data =  load_kabam_json(kabam_bcg_stat_en)
        await self._ksearch_paginate(data, term, None)           # for page in pages:
    #
    @ksearch.command(hidden=True, pass_context=True, name='bcg_en', aliases=['bcg',])
    async def ksearch_bcg_en(self, ctx, term: str = None):
        '''Search for keys or terms within bcg_en'''
        data =  load_kabam_json(kabam_bcg_en)
        await self._ksearch_paginate(data, term, None)           # for page in pages:

    async def _ksearch_paginate(self, data, term, v=None):
        keylist = data.keys()
        if term is None:
            print(keylist)
            pages = chat.pagify('\n'.join(k for k in keylist))
            page_list = []
            for page in pages:
                page_list.append(page)
            menu = PagesMenu(self.bot, timeout=120, delete_onX=True, add_pageof=True)
            await menu.menu_start(page_list)                # for page in pages:
        else:
            if term in keylist:
                await self.bot.say(self._bcg_recompile(data[term]))
            else:
                ksearchlist = []
                for k in keylist:
                    if term in data[k]:
                        ksearchlist.append('\n{}\n{}\n'.format(k, self._bcg_recompile(data[k])))
                pages = chat.pagify('\n'.join(s for s in ksearchlist))
                page_list = []
                for page in pages:
                    page_list.append(chat.box(page))
                menu = PagesMenu(self.bot, timeout=120, delete_onX=True, add_pageof=True)
                await menu.menu_start(page_list)


    def _bcg_recompile(self, str_data):
        hex_re = re.compile(r'\[[0-9a-f]{6,8}\](.+?)\[-\]', re.I)
        return hex_re.sub(r'\1', str_data)


    @commands.command(hidden=True)
    async def tst(self, key):
        files = {'bio': (kabam_bio, 'ID_CHARACTER_BIOS_', 'mcocjson'),
                 'sig': (kabam_bcg_stat_en, 'ID_UI_STAT_', 'mcocsig')}
        ignore_champs = ('DRONE', 'SYMBIOD')
        if key not in files:
            await self.bot.say('Accepted Key values:\n\t' + '\n\t'.join(files.keys()))
            return
        data = load_kabam_json(files[key][0])
        no_mcocjson = []
        no_kabam_key = []
        data_keys = {k for k in data.keys() if k.startswith(files[key][1])}
        ignore_keys = set()
        for champ in ignore_champs:
            ignore_keys.update({k for k in data_keys if k.find(champ) != -1})
        data_keys -= ignore_keys
        print(ignore_keys)
        for champ in self.champs:
            if not getattr(champ, files[key][2], None):
                no_mcocjson.append(champ.full_name)
                continue
            kabam_key = files[key][1] + getattr(champ, files[key][2])
            champ_keys = {k for k in data.keys() if k.startswith(kabam_key)}
            if not champ_keys:
                no_kabam_key.append(champ.full_name)
            else:
                data_keys -= champ_keys
        if no_mcocjson:
            await self.bot.say('Could not find mcocjson alias for champs:\n\t' + ', '.join(no_mcocjson))
        if no_kabam_key:
            await self.bot.say('Could not find Kabam key for champs:\n\t' + ', '.join(no_kabam_key))
        if data_keys:
            #print(data_keys, len(data_keys))
            if len(data_keys) > 20:
                dump = {k for k in data_keys if k.endswith('TITLE')}
            else:
                dump = data_keys
            await self.bot.say('Residual keys:\n\t' + '\n\t'.join(dump))
        await self.bot.say('Done')

    @commands.has_any_role('DataDonors','CollectorDevTeam','CollectorSupportTeam','CollectorPartners')
    @commands.group(pass_context=True, aliases=['donate',], hidden=True)
    async def submit(self, ctx):
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @submit.command(pass_context=True, name='stats')
    async def submit_stats(self, ctx, champ : ChampConverter, *, stats):
        '''hp, atk, cr, cd, blockpen, critresist, armorpen, armor, bp'''
        guild = await self.check_guild(ctx)
        if not guild:
            await self.bot.say('This server is unauthorized.')
            return
        else:
            default = {
                'hp' : 0, # Health
                'atk' : 0, # Attack
                'cr' : 0, # Critical Rate
                'cd' : 0, # Critical Damage
                'blockpen' : 0, # Blcok Proficiency
                'critresist' : 0, # Critical Resistance
                'armorpen' : 0, # Armor Penetration
                'armor' : 0, # Armor
                'bp' : 0, # Block Proficiency
            }

            parse_re = re.compile(r'''(?:hp(?P<hp>/d{1,6}))
                |(?:atk(?P<atk>/d{1,4}))
                |(?:cr(?P<cr>/d{1,4}))
                |(?:cd(?P<cd>/d{1,4}))
                |(?:armorpen(?P<armopen>/d{1,4}))
                |(?:blockpen(?P<blockpen>/d{1,4}))
                |(?:critresist(?P<critresist>/d{1,4}))
                |(?:armor(?P<armor>/d{1,4}))
                |(?:bp(?P<bp>/d{1,5}))
                ''',re.X)

            dangling_arg = None
            for arg in stats.lower().split(' '):
                for m in parse_re.finditer(arg):
                    default[m.lastgroup] = int(m.group(m.lastgroup))

            message = await self.bot.say('Submission registered.\nChampion: ' + champ.verbose_str +
                    '\nHealth: {0.hp}'
                    '\nAttack: {0.atk}'
                    '\nCritical Rate: {0.cr}'
                    '\nCritical Damage: {0.cd}'
                    '\nArmor Penetration: {0.armorpen}'
                    '\nBlock Penetration: {0.blockpen}'
                    '\nCritical Resistance: {0.crit_resist}'
                    '\nArmor: {0.armor}'
                    '\nBlock Proficiency: {0.bp}'
                    '\nPress OK to confirm.'.format(default))
            await self.bot.add_reaction(message, '❌')
            await self.bot.add_reaction(message, '🆗')
            react = await self.bot.wait_for_reaction(message=message,
                    user=ctx.message.author, timeout=60, emoji=['❌', '🆗'])
            if react is not None:
                if react.reaction.emoji == '❌':
                    await self.bot.say('Submission canceled.')
                elif react.reaction.emoji == '🆗':
                    GKEY = '1VOqej9o4yLAdMoZwnWbPY-fTFynbDb_Lk8bXDNeonuE'
                    message2 = await self.bot.say('Submission in process.')
                    author = ctx.message.author
                    package = [[str(ctx.message.timestamp), author.name, champ.full_name, champ.star, champ.rank, hp, attack, cr, cd, armorpen, blockpen, critresist, armor, bp, author.id ]]
                    check = await self._process_submission(package=package, GKEY=GKEY, sheet='submit_stats')
                    if check:
                        await self.bot.edit_message(message2, 'Submission complete.')
                    else:
                        await self.bot.edit_message(message2, 'Submission failed.')
            else:
                await self.bot.say('Ambiguous response.  Submission canceled')
    # @submit.command(pass_context=True, name='stats')
    # async def submit_stats(self, ctx, args):
    #     # Need to split out hp atk cr cd armor bp
    #     hp = '' #health
    #     atk = '' #attack
    #     cr = '' #crit rate
    #     cd = '' #critical damage
    #     apen = '' #armor penetration
    #     bpen = '' #block penetration
    #     cresist = '' #critical resistance
    #     armor = '' #armor
    #     bp = '' #block proficiency
    #
    #
    #     # _bare_arg = None
    #     # parse_re = re.compile(r'''(?:s(?P<sig>[0-9]{1,3}))|(?:r(?P<rank>[1-5]))|(?:(?P<star>[1-6])\\?\*)|(?:(?P<star>[1-6])\\?\★)|(?:d(?P<debug>[0-9]{1,2}))''', re.X)
    #     parse_re = re.compile(r'''(?:hp(?P<hp>[0-9]{1,6}))
    #                             |(?:atk(?P<atk>[0-9]{1,4}))
    #                             |(?:cr(?P<cr>[0-9]{1,4}))
    #                             |(?:cd(?P<cd>[0-9]{1,4}))
    #                             |(?:armor(?P<armor>[0-9]{1,5}))
    #                             |(?:bp(?P<bp>[0-9]{1,4}))
    #                             ''',re.X)
    #
    #     await self.bot.say('hp: {}\natk: {}\ncr: {}\ncd: {}\narmor: {}\nbp:  {}'.format(hp, atk, cr, cd, armor, bp))

        # async def convert(self):
        #     bot = self.ctx.bot
        #     attrs = {}
        #     if self._bare_arg:
        #         args = self.argument.rsplit(' ', maxsplit=1)
        #         if len(args) > 1 and args[-1].isdecimal():
        #             attrs[self._bare_arg] = int(args[-1])
        #             self.argument = args[0]
        #     arg = ''.join(self.argument.lower().split(' '))
        #     for m in self.parse_re.finditer(arg):
        #         attrs[m.lastgroup] = int(m.group(m.lastgroup))
        #     token = self.parse_re.sub('', arg)
        #     if not token:
        #         err_str = "No Champion remains from arg '{}'".format(self.argument)
        #         await bot.say(err_str)
        #         raise commands.BadArgument(err_str)
        #     return (await self.get_champion(bot, token, attrs))

    @submit.command(pass_context=True, name='prestige')
    async def submit_prestige(self, ctx, champ : ChampConverter, observation : int):
        guild = await self.check_guild(ctx)
        if not guild:
            await self.bot.say('This server is unauthorized.')
            return
        else:
            message = await self.bot.say('Submission registered.\nChampion: ' +
                    '{0.verbose_str}\nPrestige: {1}\nPress OK to confirm.'.format(
                    champ, observation))
            await self.bot.add_reaction(message, '❌')
            await self.bot.add_reaction(message, '🆗')
            react = await self.bot.wait_for_reaction(message=message,
                    user=ctx.message.author, timeout=30, emoji=['❌', '🆗'])
            if react is not None:
                if react.reaction.emoji == '❌':
                    await self.bot.say('Submission canceled.')
                elif react.reaction.emoji == '🆗':
                    GKEY = '1HXMN7PseaWSvWpNJ3igUkV_VT-w4_7-tqNY7kSk0xoc'
                    message2 = await self.bot.say('Submission in process.')
                    author = ctx.message.author
                    package = [['{}'.format(champ.mattkraftid), champ.sig, observation, champ.star, champ.rank, champ.max_lvl, author.name, author.id]]
                    check = await self._process_submission(package=package, GKEY=GKEY, sheet='collector_submit')
                    if check:
                        await self.bot.edit_message(message2, 'Submission complete.')
                    else:
                        await self.bot.edit_message(message2, 'Submission failed.')
            else:
                await self.bot.say('Ambiguous response.  Submission canceled')


    @submit.command(pass_context=True, name='duel', aliases=['duels','target'])
    async def submit_duel_target(self, ctx, champ : ChampConverter, observation, pi:int = 0):
        guild = await self.check_guild(ctx)
        if not guild:
            await self.bot.say('\u26a0 This server is unauthorized.')
            return
        else:
            message = await self.bot.say('Duel Target registered.\nChampion: ' +
                    '{0.star_name_str}\nTarget: {1}\nPress OK to confirm.'.format(
                    champ, observation))
            await self.bot.add_reaction(message, '❌')
            await self.bot.add_reaction(message, '🆗')
            react = await self.bot.wait_for_reaction(message=message, user=ctx.message.author, timeout=30, emoji=['❌', '🆗'])
            if react is not None:
                if react.reaction.emoji == '❌':
                    await self.bot.say('Submission canceled.')
                elif react.reaction.emoji == '🆗':
                    # GKEY = '1VOqej9o4yLAdMoZwnWbPY-fTFynbDb_Lk8bXDNeonuE'
                    GKEY = '1FZdJPB8sayzrXkE3F2z3b1VzFsNDhh-_Ukl10OXRN6Q'
                    message2 = await self.bot.say('Submission in progress.')
                    author = ctx.message.author
                    star = '{0.star}{0.star_char}'.format(champ)
                    if pi == 0:
                        if champ.has_prestige:
                            pi=champ.prestige
                    now = str(ctx.message.timestamp)
                    package = [[now, author.name, star, champ.full_name, champ.rank, champ.max_lvl, pi, observation, author.id]]
                    print('package built')
                    check = await self._process_submission(package=package, GKEY=GKEY, sheet='collector_submit')
                    if check:
                        await self.bot.edit_message(message2, 'Submission complete.')
                        async with aiohttp.ClientSession() as s:
                            await asyncio.sleep(10)
                            await self.cache_remote_file('duelist', s, force_cache=True, verbose=True)
                            await self.bot.edit_message(message2, 'Submission complete.\nDuel Targets refreshed.')
                    else:
                        await self.bot.edit_message(message2, 'Submission failed.')
            else:
                await self.bot.say('Ambiguous response.  Submission canceled')

    @submit.command(pass_context=True, name='defkill', aliases=['defko',])
    async def submit_awkill(self, ctx, champ : ChampConverter, node:int, ko: int):
        message = await self.bot.say('Defender Kill registered.\nChampion: {0.verbose_str}\nAW Node: {1}\nKills: {2}\nPress OK to confirm.'.format(champ, node, ko))
        await self.bot.add_reaction(message, '❌')
        await self.bot.add_reaction(message, '🆗')
        react = await self.bot.wait_for_reaction(message=message, user=ctx.message.author, timeout=30, emoji=['❌', '🆗'])
        if react is not None:
            if react.reaction.emoji == '❌':
                await self.bot.say('Submission canceled.')
            elif react.reaction.emoji == '🆗':
                GKEY = '1VOqej9o4yLAdMoZwnWbPY-fTFynbDb_Lk8bXDNeonuE' #Collector Submissions
                message2 = await self.bot.say('Submission in progress.')
                author = ctx.message.author
                now = str(ctx.message.timestamp)
                package = [[now, author.name, author.id, champ.unique, node, ko]]
                print('package built')
                check = await self._process_submission(package=package, GKEY=GKEY, sheet='defender_kos')
                if check:
                    await self.bot.edit_message(message2, 'Submission complete.')
                else:
                    await self.bot.edit_message(message2, 'Submission failed.')
        else:
            GKEY = '1VOqej9o4yLAdMoZwnWbPY-fTFynbDb_Lk8bXDNeonuE' #Collector Submissions
            message2 = await self.bot.say('Ambiguous response: Submission in progress.')
            author = ctx.message.author
            now = str(ctx.message.timestamp)
            package = [[now, author.name, author.id, champ.unique, node, ko]]
            print('package built')
            check = await self._process_submission(package=package, GKEY=GKEY, sheet='defender_kos')
            if check:
                await self.bot.edit_message(message2, 'Submission complete.')
            else:
                await self.bot.edit_message(message2, 'Submission failed.')

    @submit.command(pass_context=True, name='100hits', aliases=['50hits',])
    async def submit_100hitchallenge(self, ctx, champ : ChampConverter, hits : int, wintersoldier_hp : int, author : discord.User = None):
        if author is None:
            author = ctx.message.author
        message = await self.bot.say('100 Hit Challenge registered.\nChampion: {0.verbose_str}\nHits: {1}\nWinter Soldier HP: {2}\nPress OK to confirm.'.format(champ, hits, wintersoldier_hp))
        await self.bot.add_reaction(message, '❌')
        await self.bot.add_reaction(message, '🆗')
        react = await self.bot.wait_for_reaction(message=message, user=ctx.message.author, timeout=30, emoji=['❌', '🆗'])
        GKEY = '1RoofkyYgFu6XOypoe_IPVHivvToEuLL2Vqv1KDQLGlA' #100 hit challenge
        SHEETKEY = 'collector_submit'
        pct = round(((547774-wintersoldier_hp)/547774)*100, 4)
        now = str(ctx.message.timestamp)
        package = [[author.name, champ.unique, champ.full_name, champ.star, champ.rank, wintersoldier_hp, hits, pct, now]]
        print('package built')
        if react is not None:
            if react.reaction.emoji == '❌':
                await self.bot.say('Submission canceled.')
            elif react.reaction.emoji == '🆗':
                message2 = await self.bot.say('Submission in progress.')
                check = await self._process_submission(package=package, GKEY=GKEY, sheet=SHEETKEY)
                if check:
                    await self.bot.edit_message(message2, 'Submission complete.\nWinter Soldier Damage: {}%'.format(pct))
                else:
                    await self.bot.edit_message(message2, 'Submission failed.')
        else:
            message2 = await self.bot.say('Ambiguous response: Submission in progress.')
            print('package built')
            check = await self._process_submission(package=package, GKEY=GKEY, sheet=SHEETKEY)
            if check:
                await self.bot.edit_message(message2, 'Submission complete.\nWinter Soldier Damage: {}%'.format(pct))
            else:
                await self.bot.edit_message(message2, 'Submission failed.')

    async def check_guild(self, ctx):
        authorized = ['215271081517383682','124984400747167744','378035654736609280','260436844515164160']
        serverid = ctx.message.server.id
        return serverid in authorized

    async def _process_submission(self, package, GKEY, sheet):
        try:
            gc = pygsheets.authorize(service_file=gapi_service_creds, no_cache=True)
        except FileNotFoundError:
            await self.bot.say('Cannot find credentials file.  Needs to be located:\n'
                + gapi_service_creds)
            return False
        else:
            sh = gc.open_by_key(key=GKEY, returnas='spreadsheet')
            worksheet = sh.worksheet(property='title',value=sheet)
            worksheet.append_table(start='A1',end=None, values=package, dimension='ROWS', overwrite=False)
            worksheet.sync()
            return True

    # async def _process_submit_prestige(self, ctx, champ, observation):
    #     GKEY = '1HXMN7PseaWSvWpNJ3igUkV_VT-w4_7-tqNY7kSk0xoc'
    #     author = ctx.message.author
    #     level = int(champ.rank)*10
    #     if champ.star == 5:
    #         level += 15
    #     package = [['{}'.format(champ.mattkraftid), champ.sig, observation, champ.star, champ.rank, level, author.name, author.id]]
    #     try:
    #         gc = pygsheets.authorize(service_file=gapi_service_creds, no_cache=True)
    #     except FileNotFoundError:
    #         await self.bot.say('Cannot find credentials file.  Needs to be located:\n'
    #         + gapi_service_creds)
    #         return
    #     sh = gc.open_by_key(key=GKEY,returnas='spreadsheet')
    #     worksheet = sh.worksheet(property='title',value='collector_submit')
    #     worksheet.append_table(start='A2',end=None, values=package, dimension='ROWS', overwrite=False)
    #     worksheet.sync()

    @commands.has_any_role('DataDonors','CollectorDevTeam','CollectorSupportTeam','CollectorPartners')
    @commands.group(pass_context=True, hidden=True)
    async def costs(self, ctx):
        guild = await self.check_guild(ctx)
        if not guild:
            await self.bot.say('This server is unauthorized.')
            return
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @costs.command(name='rankup', aliases=['rank',])
    async def cost_rankup(self, ctx, champs : ChampConverterMult):
        counter = 0
        for champ in champs:
            counter += 1
        print('rankup counter: '+str(counter))


def validate_attr(*expected_args):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            for attr in expected_args:
                if getattr(self, attr + '_data', None) is None:
                    raise AttributeError("{} for Champion ".format(attr.capitalize())
                        + "'{}' has not been initialized.".format(self.champ))
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


class Champion:

    base_tags = {'#cr{}'.format(i) for i in range(10, 130, 10)}
    base_tags.update({'#{}star'.format(i) for i in range(1, 6)})
    base_tags.update({'#{}*'.format(i) for i in range(1, 6)})
    base_tags.update({'#awake', }, {'#sig{}'.format(i) for i in range(1, 201)})
    dupe_levels = {2: 1, 3: 8, 4: 20, 5: 20, 6: 20}
    default_stars = {i: {'rank': i+1, 'sig': 99} for i in range(1,5)}
    default_stars[5] = {'rank': 5, 'sig': 200}
    default_stars[6] = {'rank': 1, 'sig': 200}

    sig_raw_per_str = '{:.2%}'
    sig_per_str = '{:.2f} ({:.2%})'

    def __init__(self, attrs=None):
        self.warn_bold_say = partial(warn_bold_say, self.bot)
        if attrs is None:
            attrs = {}
        self.debug = attrs.pop('debug', 0)

        self._star = attrs.pop('star', 4)
        if self._star < 1:
            logger.warn('Star {} for Champ {} is too low.  Setting to 1'.format(
                    self._star, self.full_name))
            self._star = 1
        if self._star > 6:
            logger.warn('Star {} for Champ {} is too high.  Setting to 6'.format(
                    self._star, self.full_name))
            self._star = 6
        self._default = self.default_stars[self._star].copy()

        for k,v in attrs.items():
            if k not in self._default:
                setattr(self, k, v)
        self.tags = set()
        self.update_attrs(attrs)

    def __eq__(self, other):
        return self.immutable_id == other.immutable_id \
                and self.rank == other.rank \
                and self.sig == other.sig

    def update_attrs(self, attrs):
        self.tags.difference_update(self.base_tags)
        for k in ('rank', 'sig'):
            if k in attrs:
                setattr(self, '_' + k, attrs[k])
        if self.sig < 0:
            self._sig = 0
        if self.rank < 1:
            self._rank = 1
        if self.star >= 5:
            if self.rank > 5:
                self._rank = 5
            if self.sig > 200:
                self._sig = 200
        elif self.star < 5:
            if self.rank > (self.star + 1):
                self._rank = self.star + 1
            if self.sig > 99:
                self._sig = 99
        self.tags.add('#cr{}'.format(self.chlgr_rating))
        self.tags.add('#{}star'.format(self.star))
        self.tags.add('#{}*'.format(self.star))
        if self.sig != 0:
            self.tags.add('#awake')
        self.tags.add('#sig{}'.format(self.sig))

    def update_default(self, attrs):
        self._default.update(attrs)

    def inc_dupe(self):
        self.update_attrs({'sig': self.sig + self.dupe_levels[self.star]})

    def get_avatar(self):
        image = '{}images/portraits/{}.png'.format(remote_data_basepath, self.mattkraftid)
        logger.debug(image)
        return image

    def get_featured(self):
        image = '{}images/featured/{}.png'.format(
                    remote_data_basepath, self.mattkraftid)
        logger.debug(image)
        return image

    async def get_bio(self):
        bios = load_kabam_json(kabam_bio)
        key = "ID_CHARACTER_BIOS_{}".format(self.mcocjson)
        if self.debug:
            dbg_str = "BIO:  " + key
            await self.bot.say('```{}```'.format(dbg_str))
        if key not in bios:
            raise KeyError('Cannot find Champion {} in data files'.format(self.full_name))
        return bios[key]

    @property
    def star(self):
        return self._star

    @property
    def rank(self):
        return getattr(self, '_rank', self._default['rank'])

    @property
    def sig(self):
        return getattr(self, '_sig', self._default['sig'])

    def is_defined(self, attr):
        return hasattr(self, '_' + attr)

    @property
    def immutable_id(self):
        return (type(self), self.star)

    @property
    def duel_str(self):
        return '{0.star}{0.star_char} {0.rank}/{0.max_lvl} {0.full_name}'.format(self)

    @property
    def star_str(self):
        return '{0.stars_str} {0.rank}/{0.max_lvl}'.format(self)

    @property
    def attrs_str(self):
        return '{0.star}{0.star_char} {0.rank}/{0.max_lvl} sig{0.sig}'.format(self)

    @property
    def unique(self):
        return '{0.star}-{0.mattkraftid}-{0.rank}'.format(self)

    @property
    def coded_str(self):
        return '{0.star}*{0.short}r{0.rank}s{0.sig}'.format(self)

    @property
    def verbose_str(self):
        return '{0.star}{0.star_char} {0.full_name} r{0.rank}'.format(self)
        # return '{0.stars_str} {0.full_name} r{0.rank}'.format(self)

    @property
    def star_name_str(self):
        return '{0.star}{0.star_char} {0.full_name}'.format(self)
        #return '{0.star}★ {0.full_name}'.format(self)

    @property
    def rank_sig_str(self):
        return '{0.rank}/{0.max_lvl} sig{0.sig:<2}'.format(self)

    @property
    def verbose_prestige_str(self):
        return ('{0.class_icon} {0.star}{0.star_char} {0.full_name} '
                + 'r{0.rank} s{0.sig:<2} [ {0.prestige} ]').format(self)

    @property
    def stars_str(self):
        return self.star_char * self.star

    @property
    def terse_star_str(self):
        return '{0.star}{0.star_char}'.format(self)

    @property
    def star_char(self):
        if self.sig:
            return '★'
        else:
            return '☆'

    @property
    def chlgr_rating(self):
        if self.star == 1:
            return self.rank * 10
        if self.star == 6:
            return (2 * self.star - 2 + self.rank) * 10
        else:
            return (2 * self.star - 3 + self.rank) * 10

    @property
    def max_lvl(self):
        if self.star < 5:
            return self.rank * 10
        else:
            return 15 + self.rank * 10

    @property
    def all_tags(self):
        return self.tags.union(self.class_tags)

    def to_json(self):
        translate = {'sig': 'Awakened', 'hookid': 'Id', 'max_lvl': 'Level',
                    'prestige': 'Pi', 'rank': 'Rank', 'star': 'Stars',
                    'quest_role': 'Role', 'max_prestige': 'maxpi'}
        pack = {}
        for attr, hook_key in translate.items():
            pack[hook_key] = getattr(self, attr, '')
        return pack

    def get_special_attacks(self):
        specials = load_kabam_json(kabam_special_attacks)
        prefix = 'ID_SPECIAL_ATTACK_'
        desc = 'DESCRIPTION_'
        zero = '_0'
        one = '_1'
        two = '_2'
        s0 = specials[prefix + self.mcocjson + zero]
        s1 = specials[prefix + self.mcocjson + one]
        s2 = specials[prefix + self.mcocjson + two]
        s0d = specials[prefix + desc + self.mcocjson + zero]
        s1d = specials[prefix + desc + self.mcocjson + one]
        s2d = specials[prefix + desc + self.mcocjson + two]
        specials = (s0, s1, s2, s0d, s1d, s2d)
        return specials


    @property
    @validate_attr('prestige')
    def prestige(self):
        try:
            if self.prestige_data[self.star][self.rank-1] is None:
                return 0
        except KeyError:
            return 0
        return self.prestige_data[self.star][self.rank-1][self.sig]

    @property
    def has_prestige(self):
        return hasattr(self, 'prestige_data')

    @property
    @validate_attr('prestige')
    def max_prestige(self):
        cur_rank = self.rank
        if self.star == 5:
            rank = 3 if cur_rank < 4 else 4
        else:
            rank = self.star + 1
        self.update_attrs({'rank': rank})
        maxp = self.prestige
        self.update_attrs({'rank': cur_rank})
        return maxp

    @validate_attr('prestige')
    def get_prestige_arr(self, rank, sig_arr, star=4):
        row = ['{}r{}'.format(self.short, rank)]
        for sig in sig_arr:
            try:
                row.append(self.prestige_data[star][rank-1][sig])
            except:
                logger.error(rank, sig, self.prestige_data)
                raise
        return row

    async def missing_sig_ad(self):
        em = discord.Embed(color=self.class_color,
                title='Signature Data is Missing')
        em.add_field(name=self.full_name,
                value='Contribute your data at http://discord.gg/BwhgZxk')
        await self.bot.say(embed=em)

    async def process_sig_description(self, data=None, quiet=False, isbotowner=False):
        sd = await self.retrieve_sig_data(data, isbotowner)
        ktxt = sd['kabam_text']
        if self.debug:
            dbg_str = ['Title:  ' + ktxt['title']['k']]
            dbg_str.append('Simple:  ' + ktxt['simple']['k'])
            dbg_str.append('Description Keys:  ')
            dbg_str.append('  ' + ', '.join(ktxt['desc']['k']))
            dbg_str.append('Description Text:  ')
            dbg_str.extend(['  ' + self._sig_header(d)
                            for d in ktxt['desc']['v']])
            await self.bot.say(chat.box('\n'.join(dbg_str)))

        await self._sig_error_code_handling(sd)
        if self.sig == 0:
            return self._get_sig_simple(ktxt)

        sig_calcs = {}
        try:
            stats = sd['spotlight_trunc'][self.unique]
        except (TypeError, KeyError):
            stats = {}
        self.stats_missing = False
        x_arr = self._sig_x_arr(sd)
        for effect, ckey, coeffs in zip(sd['effects'], sd['locations'], sd['sig_coeff']):
            if coeffs is None:
                await self.bot.say("**Data Processing Error**")
                if not quiet:
                    await self.missing_sig_ad()
                return self._get_sig_simple(ktxt)
            y_norm = sumproduct(x_arr, coeffs)
            sig_calcs[ckey] = self._sig_effect_decode(effect, y_norm, stats)

        if self.stats_missing:
            await self.bot.say(('Missing Attack/Health info for '
                    + '{0.full_name} {0.star_str}').format(self))

        brkt_re = re.compile(r'{([0-9])}')
        fdesc = []
        for i, txt in enumerate(ktxt['desc']['v']):
            fdesc.append(brkt_re.sub(r'{{d[{0}-\1]}}'.format(i),
                        self._sig_header(txt)))
        if self.debug:
            await self.bot.say(chat.box('\n'.join(fdesc)))
        return ktxt['title']['v'], '\n'.join(fdesc), sig_calcs

    async def retrieve_sig_data(self, data, isbotowner):
        if data is None:
            try:
                sd = dataIO.load_json(local_files['signature'])[self.full_name]
            except KeyError:
                sd = self.init_sig_struct()
            except FileNotFoundError:
                if isbotowner:
                    await self.bot.say("**DEPRECIATION WARNING**  "
                            + "Couldn't load json file.  Loading csv files.")
                sd = self.get_sig_data_from_csv()
            cfile = 'sig_coeff_4star' if self.star < 5 else 'sig_coeff_5star'
            coeff = dataIO.load_json(local_files[cfile])
            try:
                sd.update(coeff[self.full_name])
            except KeyError:
                sd.update(dict(effects=[], locations=[], sig_coeff=[]))
        else:
            sd = data[self.full_name] if self.full_name in data else data
        return sd

    async def _sig_error_code_handling(self, sd):
        if 'error_codes' not in sd or sd['error_codes']['undefined_key']:
            await self.warn_bold_say('Champion Signature data is not defined')
            self.update_attrs(dict(sig=0))
        elif sd['error_codes']['no_curve']:
            await self.warn_bold_say('{} '.format(self.star_name_str)
                    + 'does not have enough data points to create a curve')
            self.update_attrs(dict(sig=0))
        elif sd['error_codes']['low_count']:
            await self.warn_bold_say('{} '.format(self.star_name_str)
                    + 'has low data count.  Unknown estimate quality')
        elif sd['error_codes']['poor_fit']:
            await self.warn_bold_say('{} '.format(self.star_name_str)
                    + 'has poor curve fit.  Data is known to contain errors.')

    def _sig_x_arr(self, sig_dict):
        fit_type = sig_dict['fit_type'][0]
        if fit_type.startswith('lin'):
            x_var = float(self.sig)
        elif fit_type.startswith('log'):
            x_var = log(self.sig)
        else:
            raise AttributeError("Unknown fit_type '{}' for champion {}".format(
                    fit_type, self.full_name ))
        if fit_type.endswith('quad'):
            return x_var**2, x_var, 1
        elif fit_type.endswith('lin'):
            return x_var, 1
        else:
            raise AttributeError("Unknown fit_type '{}' for champion {}".format(
                    fit_type, self.full_name ))

    def _sig_effect_decode(self, effect, y_norm, stats):
        if effect == 'raw':
            if y_norm.is_integer():
                calc = '{:.0f}'.format(y_norm)
            else:
                calc = '{:.2f}'.format(y_norm)
        elif effect == 'flat':
            calc = self.sig_per_str.format(
                    to_flat(y_norm, self.chlgr_rating), y_norm/100)
        elif effect == 'attack':
            if 'attack' not in stats:
                self.stats_missing = True
                calc = self.sig_raw_per_str.format(y_norm/100)
            else:
                calc = self.sig_per_str.format(
                        stats['attack'] * y_norm / 100, y_norm/100)
        elif effect == 'health':
            if 'health' not in stats:
                self.stats_missing = True
                calc = self.sig_raw_per_str.format(y_norm/100)
            else:
                calc = self.sig_per_str.format(
                        stats['health'] * y_norm / 100, y_norm/100)
        else:
            raise AttributeError("Unknown effect '{}' for {}".format(
                    effect, self.full_name))
        return calc

    def _get_sig_simple(self, ktxt):
        return ktxt['title']['v'], ktxt['simple']['v'], None

    def get_sig_data_from_csv(self):
        struct = self.init_sig_struct()
        coeff = self.get_sig_coeff()
        ekey = self.get_effect_keys()
        spotlight = self.get_spotlight()
        if spotlight and spotlight['attack'] and spotlight['health']:
            stats = {k:int(spotlight[k].replace(',',''))
                        for k in ('attack', 'health')}
        else:
            stats = {}
        struct['spotlight_trunc'] = {self.unique: stats}
        if coeff is None or ekey is None:
            return struct
        for i in map(str, range(6)):
            if not ekey['Location_' + i]:
                break
            struct['effects'].append(ekey['Effect_' + i])
            struct['locations'].append(ekey['Location_' + i])
            try:
                struct['sig_coeff'].append((float(coeff['ability_norm' + i]),
                      float(coeff['offset' + i])))
            except:
                struct['sig_coeff'] = None
        return struct

    def init_sig_struct(self):
        return dict(effects=[], locations=[], sig_coeff=[],
                #spotlight_trunc={self.unique: stats},
                kabam_text=self.get_kabam_sig_text())

    def get_kabam_sig_text(self, sigs=None, champ_exceptions=None):
        '''required for signatures to work correctly
        preamble
        title = titlekey,
        simplekey = preample + simple
        descriptionkey = preamble + desc,
        '''

        if sigs is None:
            sigs = load_kabam_json(kabam_bcg_stat_en)
        if champ_exceptions is None:
            champ_exceptions = {
                #'CYCLOPS_90S': ['ID_UI_STAT_SIGNATURE_CYCLOPS_DESC_90S_AO'],
                'CYCLOPS_90S': ['ID_UI_STAT_SIGNATURE_CYCLOPS_DESC_90S_AO'],
                'LOKI': ['ID_UI_STAT_SIGNATURE_LOKI_LONGDESC'],
                'DEADPOOL': ['ID_UI_STAT_SIGNATURE_DEADPOOL_DESC2_AO'],
                #'ULTRON': ['ID_UI_STAT_SIGNATURE_ULTRON_DESC'],
                #'COMICULTRON': ['ID_UI_STAT_SIGNATURE_ULTRON_DESC'],
                'IRONMAN_SUPERIOR': ['ID_UI_STAT_SIGNATURE_IRONMAN_DESC_AO',
                        'ID_UI_STAT_SIGNATURE_IRONMAN_DESC_B_AO'],
                'BEAST': ['ID_UI_STAT_SIGNATURE_LONGDESC_AO',
                        'ID_UI_STAT_SIGNATURE_LONGDESC_B_AO',
                        'ID_UI_STAT_SIGNATURE_LONGDESC_C_AO',
                        'ID_UI_STAT_SIGNATURE_LONGDESC_D_AO',
                        'ID_UI_STAT_SIGNATURE_LONGDESC_E_AO'],
                'GUILLOTINE': ['ID_UI_STAT_SIGNATURE_GUILLOTINE_DESC'],
                'NEBULA': ['ID_UI_STAT_SIGNATURE_NEBULA_LONG'],
                #'RONAN': ['ID_UI_STAT_SIGNATURE_RONAN_DESC_AO'],
                'MORDO': ['ID_UI_STAT_SIG_MORDO_DESC_AO'],
                'DOC_OCK': ['ID_UI_STAT_ATTRIBUTE_DOC_OCK_SIGNATURE_DESC_A',
                            'ID_UI_STAT_ATTRIBUTE_DOC_OCK_SIGNATURE_DESC_B',
                            'ID_UI_STAT_ATTRIBUTE_DOC_OCK_SIGNATURE_DESC_D',
                            'ID_UI_STAT_ATTRIBUTE_DOC_OCK_SIGNATURE_DESC_C']
            }

        mcocsig = self.mcocsig
        preamble = None
        title = None
        simple = None
        desc = []

        if mcocsig == 'COMICULTRON':
            mcocsig = 'DRONE_TECH'
        elif mcocsig == 'CYCLOPS_90S':
            mcocsig = 'CYCLOPS'

        titles = ('ID_UI_STAT_SIGNATURE_{}_TITLE'.format(mcocsig),
            'ID_UI_STAT_ATTRIBUTE_{}_TITLE'.format(mcocsig),
            'ID_UI_STAT_{}_SIGNATURE_TITLE'.format(mcocsig),
            'ID_UI_STAT_SIG_{}_TITLE'.format(mcocsig),
            'ID_UI_STAT_ATTRIBUTE_{}_SIGNATURE_TITLE'.format(mcocsig),
            'ID_UI_STAT_ATTRIBUTE_{}_SIG_TITLE'.format(mcocsig),
            'ID_UI_STAT_SIGNATURE_FORMAT_{}_SIG_TITLE'.format(mcocsig),
            'ID_UI_STAT_SIGNATURE_{}_SIG_TITLE'.format(mcocsig),
            'ID_STAT_SIGNATURE_{}_TITLE'.format(mcocsig),
            'ID_STAT_{}_SIG_TITLE'.format(mcocsig), #added for BISHOP
            'ID_UI_STAT_FORMAT_{}_SIG_TITLE'.format(mcocsig),#added for WASP
            )

        for x in titles:
            if x in sigs:
                title = x
                print('SIG TITLE is : ' + x)

        if title is None:
            raise TitleError("'{}' title not found".format(mcocsig)) #, mcocsig)

        if self.mcocsig == 'COMICULTRON':
            mcocsig = self.mcocsig  # re-init for Ultron Classic

        preambles = ('ID_UI_STAT_SIGNATURE_{}'.format(mcocsig),
            'ID_UI_STAT_{}_SIGNATURE'.format(mcocsig),
            'ID_UI_STAT_SIG_{}'.format(mcocsig),
            'ID_UI_STAT_ATTRIBUTE_{}_SIGNATURE'.format(mcocsig),
            'ID_UI_STAT_SIGNATURE_FORMAT_{}_SIG'.format(mcocsig),
            'ID_UI_STAT_SIGNATURE_{}_SIG'.format(mcocsig),
            'ID_STAT_SIGNATURE_{}'.format(mcocsig),
            'ID_STAT_{}_SIG'.format(mcocsig),  #bishop ID_STAT_BISH_SIG_SHORT
            'ID_STAT_{}_SIG_TITLE'.format(mcocsig),
            'ID_UI_STAT_FORMAT_{}_SIG'.format(mcocsig), # added for wasp
            )

        for x in preambles:
            if x + '_SIMPLE' in sigs:
                preamble = x
                #print('SIG PREAMBLE is : ' + x)
                break
        if preamble is None and mcocsig == 'BISH':
            preamble = 'ID_STAT_BISH_SIG'
        elif preamble is None:
            raise TitleError("'{}' preamble not found".format(mcocsig))
        if preamble + '_SIMPLE_NEW2' in sigs:
            simple = preamble + '_SIMPLE_NEW2'
        if preamble + '_SIMPLE_NEW' in sigs:
            simple = preamble + '_SIMPLE_NEW'
        elif preamble + '_SIMPLE' in sigs:
            simple = preamble + '_SIMPLE'
        elif mcocsig == 'BISH':  #BISHOP
            simple = preamble + '_SHORT' #BISHOP is the only champ that swaps Short for Simple.
        else:
            raise KeyError('Signature SIMPLE cannot be found with: {}_SIMPLE'.format(preamble))


        if self.mcocsig == 'CYCLOPS_90S':
            desc.append('ID_UI_STAT_SIGNATURE_CYCLOPS_DESC_90S_AO')
        elif mcocsig in champ_exceptions:
            desc.extend(champ_exceptions[mcocsig])
        elif preamble + '_DESC_NEW' in sigs:
            desclist = ('_DESC_NEW','_DESC_NEW_B')
            if preamble + '_DESC_NEW2' in sigs:
                desclist = ('_DESC_NEW2','_DESC_NEW2_B')
            elif preamble + '_DESC_NEW_FIXED' in sigs:
                desclist = ('_DESC_NEW_FIXED','_DESC_NEW_B_FIXED')
            for k in desclist:
                if preamble + k in sigs:
                    if preamble + k + '_AO' in sigs:
                        desc.append(preamble + k + '_AO')
                    else:
                        desc.append(preamble + k)
        elif preamble + '_5STAR_DESC_MOD' in sigs:
            desc.append(preamble+'_DESC_MOD')
        else:
            for k in ('_DESC','_DESC_A','_DESC_B','_DESC_C','_DESC_D',
                      '_DESC_E','_DESC_F','_DESC_G',
                      '_LONG','_LONG_1','_LONG_2','_LONG_3','_LONG_4','_LONG_5',
                      '_LONG1','_LONG2','_LONG3','_LONG4','_LONG5',
                      '_LONG_A','_LONG_B', '_LONG_C',
                      '_0','_1',):
                if preamble + k + '_UPDATED' in sigs:
                    k = k + '_UPDATED'
                if preamble + k in sigs:
                    if preamble + k + '_ALT' in sigs:
                        desc.append(preamble + k + '_ALT')
                    elif preamble + k + '_AO' in sigs:
                        desc.append(preamble + k + '_AO')
                    else:
                        desc.append(preamble + k)
        return dict(title={'k': title, 'v': sigs[title]},
                    simple={'k': simple, 'v': sigs[simple]},
                    desc={'k': desc, 'v': [sigs[k] for k in desc]})

    def get_sig_coeff(self):
        return get_csv_row(local_files['sig_coeff'], 'CHAMP', self.full_name)

    def get_effect_keys(self):
        return get_csv_row(local_files['effect_keys'], 'CHAMP', self.full_name)

    def get_spotlight(self, default=None):
        return get_csv_row(data_files['spotlight']['local'], 'unique',
                self.unique, default=default)

    def get_aliases(self):
        return '```{}```'.format(', '.join(self.alias_set))

    @staticmethod
    def _sig_header(str_data):
        hex_re = re.compile(r'\[[0-9a-f]{6,8}\](.+?)\[-\]', re.I)
        return '• ' + hex_re.sub(r'**\1**', str_data)

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

    async def menu_start(self, pages):
        page_list = []
        if isinstance(pages, list):
            page_list = pages
        else:
            for page in pages:
                page_list.append(page)
        page_length = len(page_list)
        if page_length == 1:
            await self.bot.say(embed=page_list[0])
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
        await self.display_page(None, 0)

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

def bound_lvl(siglvl, max_lvl=99):
    if isinstance(siglvl, list):
        ret = []
        for j in siglvl:
            if j > max_lvl:
                j = max_lvl
            elif j < 0:
                j = 0
            ret.append(j)
    else:
        ret = siglvl
        if siglvl > max_lvl:
            ret = max_lvl
        elif siglvl < 0:
            ret = 0
    return ret

def tabulate(table_data, width, rotate=True, header_sep=True, align_out=True):
    rows = []
    cells_in_row = None
    for i in iter_rows(table_data, rotate):
        if cells_in_row is None:
            cells_in_row = len(i)
        elif cells_in_row != len(i):
            raise IndexError("Array is not uniform")
        if align_out:
            fstr = '{:<{width}}'
            if len(i) > 1:
                fstr += '|' + '|'.join(['{:>{width}}']*(len(i)-1))
            rows.append(fstr.format(*i, width=width))
        else:
            rows.append('|'.join(['{:^{width}}']*len(i)).format(*i, width=width))
    if header_sep:
        rows.insert(1, '|'.join(['-' * width] * cells_in_row))
    return chat.box('\n'.join(rows))

def sumproduct(arr1, arr2):
    return sum([x * y for x, y in zip(arr1, arr2)])
    # return sum([float(x) * float(y) for x, y in zip(arr1, arr2)])

def iter_rows(array, rotate):
    if not rotate:
        for i in array:
            yield i
    else:
        for j in range(len(array[0])):
            row = []
            for i in range(len(array)):
                row.append(array[i][j])
            yield row

def load_kabam_json(file, aux=None):
    raw_data = dataIO.load_json(file)
    data = ChainMap()
    aux = aux if aux is not None else []
    for dlist in aux, raw_data['strings']:
        data.maps.append({d['k']:d['v'] for d in dlist})
    return data

def _truncate_text(self, text, max_length):
    if len(text) > max_length:
        if text.strip('$').isdigit():
            text = int(text.strip('$'))
            return "${:.2E}".format(text)
        return text[:max_length-3] + "..."
    return text

def get_csv_row(filecsv, column, match_val, default=None):
    logger.debug(match_val)
    csvfile = load_csv(filecsv)
    for row in csvfile:
        if row[column] == match_val:
            if default is not None:
                for k, v in row.items():
                    if v == '':
                        row[k] = default
            return row

def get_csv_rows(filecsv, column, match_val, default=None):
    logger.debug(match_val)
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

def load_csv(filename):
    return csv.DictReader(open(filename))

def padd_it(word,max : int,opt='back'):
    loop = max-len(str(word))
    if loop > 0:
        padd = ''
        for i in loop:
            padd+=' '
        if opt =='back':
            return word+padd
        else:
            return padd+word
    else:
        logger.warn('Padding would be negative.')

async def raw_modok_says(bot, channel, word=None):
    if not word or word not in MODOKSAYS:
        word = random.choice(MODOKSAYS)
    modokimage='{}images/modok/{}.png'.format(remote_data_basepath, word)
    em = discord.Embed(color=class_color_codes['Science'],
            title='M.O.D.O.K. says', description='')
    em.set_image(url=modokimage)
    await bot.send_message(channel, embed=em)

def override_error_handler(bot):
    if not hasattr(bot, '_command_error_orig'):
        bot._command_error_orig = bot.on_command_error
    @bot.event
    async def on_command_error(error, ctx):
        if isinstance(error, MODOKError):
            bot.logger.info('<{}> {}'.format(type(error).__name__, error))
            await bot.send_message(ctx.message.channel, "\u26a0 " + str(error))
            await raw_modok_says(bot, ctx.message.channel)
        elif isinstance(error, QuietUserError):
            #await bot.send_message(ctx.message.channel, error)
            bot.logger.info('<{}> {}'.format(type(error).__name__, error))
        else:
            await bot._command_error_orig(error, ctx)

# avoiding cyclic importing
from . import hook as hook

def setup(bot):
    override_error_handler(bot)
    # if not hasattr(bot, '_command_error_orig'):
    #     bot._command_error_orig = bot.on_command_error
    # @bot.event
    # async def on_command_error(error, ctx):
    #     if isinstance(error, MODOKError):
    #         bot.logger.info('<{}> {}'.format(type(error).__name__, error))
    #         await bot.send_message(ctx.message.channel, error)
    #         await raw_modok_says(bot, ctx.message.channel)
    #     elif isinstance(error, QuietUserError):
    #         print("I'm here")
    #         bot.logger.info('<{}> {}'.format(type(error).__name__, error))
    #     else:
    #         await bot._command_error_orig(error, ctx)
    bot.add_cog(MCOC(bot))
